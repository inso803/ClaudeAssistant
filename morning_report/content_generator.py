"""組 prompt、呼叫 Gemini API，把記憶與今日事件轉成結構化的晨報內容。

用 Gemini 而不是 Claude API 是因為 Gemini API 有可用的免費額度，晨報這種每天一次的小請求
剛好用得上，不需要額外付費。

沒有設定 GEMINI_API_KEY 時（DRY_RUN）會回傳固定的假資料，方便本機測試其他環節
（看板頁面、LINE 推送格式）而不需要真的呼叫 API。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date as date_cls

import requests

from . import config
from .memory_reader import MemoryContext

GEMINI_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)

SYSTEM_PROMPT = """你是使用者的個人晨報助理。使用者是台大資工二年級學生，常往返台北大安區與台中。
請根據提供的背景資料、今天的行程、正在追蹤的自我提升項目、以及使用者最近的回饋，
產生今天的晨報內容。

風格要求：
- 簡潔、口語化的繁體中文，像朋友提醒而不是制式報告
- 自我提升項目要延續脈絡（提到目前進度／連續天數），不要每天都當作全新的事重講一次
- 如果使用者最近有回饋（例如「太長了」「不要講教訓的語氣」），要據此調整這次的風格

請只回傳一個 JSON 物件，不要有任何其他文字，格式如下：
{
  "greeting": "一句今日開場問候",
  "schedule_summary": "今日行程摘要，如果沒有行程就說明今天很空",
  "habit_highlights": ["自我提升項目1的今日提醒", "項目2的今日提醒", ...],
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
    closing_note: str = ""
    line_message: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _build_user_prompt(today: date_cls, memory: MemoryContext, schedule_events: list[dict]) -> str:
    habits_text = "\n".join(
        f"- {h.title}：第 {h.streak_days} 天，上次提到日期 {h.last_mentioned}，備註：{h.note}"
        for h in memory.active_habits
    ) or "（目前沒有正在追蹤的項目）"

    schedule_text = "\n".join(
        f"- {e.get('time', '')} {e.get('title', '')}" for e in schedule_events
    ) or "（今天沒有登記任何行程）"

    feedback_text = "\n".join(f"- {f}" for f in memory.recent_feedback) or "（目前沒有回饋紀錄）"

    return f"""今天日期：{today.isoformat()}

使用者背景摘要：
{memory.profile_text}

正在追蹤的自我提升項目：
{habits_text}

今日行程：
{schedule_text}

使用者最近的回饋：
{feedback_text}
"""


def _dry_run_content(today: date_cls, memory: MemoryContext, schedule_events: list[dict]) -> ReportContent:
    habit_lines = [
        f"{h.title} 第 {h.streak_days} 天，持續加油" for h in memory.active_habits
    ] or ["目前還沒有在追蹤的自我提升項目"]
    schedule_summary = (
        "、".join(e.get("title", "") for e in schedule_events) if schedule_events else "今天沒有登記行程，樂得輕鬆"
    )
    return ReportContent(
        date=today.isoformat(),
        greeting=f"早安，今天是 {today.isoformat()}（DRY RUN 測試內容）",
        schedule_summary=schedule_summary,
        habit_highlights=habit_lines,
        closing_note="這是本機測試產生的假資料，未呼叫 Gemini API。",
        line_message=f"[測試] {today.isoformat()} 晨報：{schedule_summary}",
    )


def generate_report_content(
    today: date_cls, memory: MemoryContext, schedule_events: list[dict]
) -> ReportContent:
    if config.DRY_RUN:
        return _dry_run_content(today, memory, schedule_events)

    url = GEMINI_URL_TEMPLATE.format(model=config.GEMINI_MODEL)
    response = requests.post(
        url,
        params={"key": config.GEMINI_API_KEY},
        json={
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": _build_user_prompt(today, memory, schedule_events)}],
                }
            ],
            "generationConfig": {"responseMimeType": "application/json"},
        },
        timeout=30,
    )
    response.raise_for_status()
    raw_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]

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
        closing_note=parsed.get("closing_note", ""),
        line_message=parsed.get("line_message", ""),
    )
