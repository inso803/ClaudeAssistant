"""組 prompt、呼叫 Groq API，把記憶與今日事件轉成結構化的晨報內容。

改用 Groq 而不是 Gemini：Gemini API 那把 key 的免費額度一直回傳 limit: 0（疑似跟
2026-08-01 開始的 GCP 帳單系統故障有關），Groq 是另一個有真正可用免費額度的供應商，
跟 Google 的系統無關，晨報這種每天一次的小請求剛好用得上，不需要額外付費。

沒有設定 GROQ_API_KEY 時（DRY_RUN）會回傳固定的假資料，方便本機測試其他環節
（看板頁面、LINE 推送格式）而不需要真的呼叫 API。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date as date_cls

import requests

from . import config
from .memory_reader import MemoryContext

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """你是使用者的個人晨報助理。使用者是台大資工二年級學生，常往返台北大安區與台中。
請根據提供的背景資料、今天的行程、正在追蹤的自我提升項目、使用者長期收藏的興趣連結、
根據這些興趣搜尋到的相關新內容、以及使用者最近的回饋，產生今天的晨報內容。

風格要求：
- 簡潔、口語化的繁體中文，像朋友提醒而不是制式報告
- 自我提升項目要延續脈絡（提到目前進度／連續天數），不要每天都當作全新的事重講一次
- 如果使用者最近有回饋（例如「太長了」「不要講教訓的語氣」），要據此調整這次的風格
- 「收藏的連結」只是單純轉述、頂多加一句簡短提醒，不要幫使用者做內容分析或下結論，
  因為你沒有真的讀過連結內容
- 「相關新內容」的推薦一定要根據提供的搜尋結果來寫，每一則附上真實的網址；
  如果沒有提供搜尋結果，recommendations 就回傳空陣列，絕對不要自己編造網址或內容

請只回傳一個 JSON 物件，不要有任何其他文字，格式如下：
{
  "greeting": "一句今日開場問候",
  "schedule_summary": "今日行程摘要，如果沒有行程就說明今天很空",
  "habit_highlights": ["自我提升項目1的今日提醒", "項目2的今日提醒", ...],
  "links_highlight": "提醒使用者長期收藏了哪些連結還沒看的一句話，如果沒有收藏連結就回傳空字串",
  "recommendations": ["根據搜尋結果推薦的一則新內容，包含標題、一句話理由、真實網址", ...],
  "closing_note": "一句簡短收尾語",
  "line_message": "整合以上內容、適合直接推播到手機的完整訊息，控制在 200 字以內"
}
"""


@dataclass
class ReportContent:
    date: str
    greeting: str
    schedule_summary: str
    habit_highlights: list[str] = field(default_factory=list)
    links_highlight: str = ""
    recommendations: list[str] = field(default_factory=list)
    closing_note: str = ""
    line_message: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _build_user_prompt(
    today: date_cls,
    memory: MemoryContext,
    schedule_events: list[dict],
    interesting_links: list[str],
    search_results: list[dict],
) -> str:
    habits_text = "\n".join(
        f"- {h.title}：第 {h.streak_days} 天，上次提到日期 {h.last_mentioned}，備註：{h.note}"
        for h in memory.active_habits
    ) or "（目前沒有正在追蹤的項目）"

    schedule_text = "\n".join(
        f"- {e.get('time', '')} {e.get('title', '')}" for e in schedule_events
    ) or "（今天沒有登記任何行程）"

    feedback_text = "\n".join(f"- {f}" for f in memory.recent_feedback) or "（目前沒有回饋紀錄）"

    links_text = "\n".join(f"- {link}" for link in interesting_links) or "（目前沒有收藏任何連結）"

    search_text = "\n".join(
        f"- 標題：{r['title']}／網址：{r['url']}／描述：{r['description']}" for r in search_results
    ) or "（這次沒有搜尋到相關新內容，recommendations 請回傳空陣列）"

    return f"""今天日期：{today.isoformat()}

使用者背景摘要：
{memory.profile_text}

正在追蹤的自我提升項目：
{habits_text}

今日行程：
{schedule_text}

使用者長期收藏的興趣連結：
{links_text}

根據興趣搜尋到的相關新內容：
{search_text}

使用者最近的回饋：
{feedback_text}
"""


def _fallback_content(
    today: date_cls,
    memory: MemoryContext,
    schedule_events: list[dict],
    interesting_links: list[str],
    reason: str,
) -> ReportContent:
    """DRY_RUN、或 Groq API 呼叫失敗時都會用到的保底內容 —— 不是 AI 生成的，
    只是把記憶裡現有的資料直接拼起來，確保當天至少有東西可以看、可以推播，
    而不是整個晨報無聲失敗。保底內容不做搜尋／推薦，那部分本來就依賴 Groq。"""
    habit_lines = [
        f"{h.title} 第 {h.streak_days} 天，持續加油" for h in memory.active_habits
    ] or ["目前還沒有在追蹤的自我提升項目"]
    schedule_summary = (
        "、".join(e.get("title", "") for e in schedule_events) if schedule_events else "今天沒有登記行程，樂得輕鬆"
    )
    links_highlight = f"目前收藏了 {len(interesting_links)} 則連結" if interesting_links else ""
    return ReportContent(
        date=today.isoformat(),
        greeting=f"早安，今天是 {today.isoformat()}（{reason}）",
        schedule_summary=schedule_summary,
        habit_highlights=habit_lines,
        links_highlight=links_highlight,
        closing_note=f"這是保底內容，未經 AI 生成：{reason}",
        line_message=f"[備用內容] {today.isoformat()} 晨報：{schedule_summary}",
    )


def _call_groq(
    today: date_cls,
    memory: MemoryContext,
    schedule_events: list[dict],
    interesting_links: list[str],
    search_results: list[dict],
) -> ReportContent:
    response = requests.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
        json={
            "model": config.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": _build_user_prompt(
                        today, memory, schedule_events, interesting_links, search_results
                    ),
                },
            ],
            "response_format": {"type": "json_object"},
        },
        timeout=30,
    )
    response.raise_for_status()
    raw_text = response.json()["choices"][0]["message"]["content"]

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        # 模型偶爾會在 JSON 前後夾雜文字，嘗試抓出第一個 { 到最後一個 } 之間的內容再解析一次
        start, end = raw_text.find("{"), raw_text.rfind("}")
        parsed = json.loads(raw_text[start : end + 1])

    return ReportContent(
        date=today.isoformat(),
        greeting=parsed.get("greeting", ""),
        schedule_summary=parsed.get("schedule_summary", ""),
        habit_highlights=parsed.get("habit_highlights", []),
        links_highlight=parsed.get("links_highlight", ""),
        recommendations=parsed.get("recommendations", []),
        closing_note=parsed.get("closing_note", ""),
        line_message=parsed.get("line_message", ""),
    )


def generate_report_content(
    today: date_cls,
    memory: MemoryContext,
    schedule_events: list[dict],
    interesting_links: list[str] | None = None,
    search_results: list[dict] | None = None,
) -> ReportContent:
    interesting_links = interesting_links or []
    search_results = search_results or []

    if config.DRY_RUN:
        return _fallback_content(
            today, memory, schedule_events, interesting_links, "DRY RUN 測試內容，未設定 GROQ_API_KEY"
        )

    try:
        return _call_groq(today, memory, schedule_events, interesting_links, search_results)
    except (requests.RequestException, KeyError, IndexError, json.JSONDecodeError) as exc:
        print(f"[content_generator] Groq API 呼叫失敗，改用保底內容：{exc}")
        return _fallback_content(today, memory, schedule_events, interesting_links, "Groq API 暫時無法使用")
