"""晨報兩段接力流程 —— 第一段（跑在 GitHub Actions，維持現有每日排程）。

只做資料蒐集，不呼叫任何 LLM：
    抓 Discord 今日/長期待辦、前一天的行程、天氣、累積興趣清單 -> 多來源推薦搜尋
    -> 寫成 pending_request.json

第二段是排程的 Claude Code routine，讀這份 pending_request.json（連同 repo 裡的
memory/、morning_report/state/interests_state.json）寫出今天的晨報文案，存成
draft_content.json，再跑 apply_content.py 把內容寫進看板、更新習慣追蹤、commit 回 repo。

待辦清單（today_todos / longterm_todos）、行程（schedule）、天氣（weather）都不需要 routine
改寫，apply_content.py 會直接從這裡原封不動帶進最終的看板資料：
- 待辦完成方式是使用者在 Discord 上把訊息刪掉；今日待辦另外套一個 24 小時時間窗（見
  sources/__init__.py 的 collect_today_todos），太舊忘記刪的訊息不會一直卡在今日待辦裡，
  長期待辦則不套這個窗
- 行程是「前一天在 calendar 頻道打的項目」，當成今天的行程（使用者習慣前一晚先打好隔天的事）
- 天氣來自 Open-Meteo，不需要 API key

用法：
    python -m morning_report.collect_report_request
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta

from . import config
from .interests import persist_new_links
from .recommender import get_recommendation_search_results
from .sources import (
    collect_interesting_links,
    collect_longterm_todos,
    collect_today_todos,
    collect_weather,
    collect_yesterdays_schedule,
)

TAIPEI_TZ = timezone(timedelta(hours=8))


def main() -> None:
    now = datetime.now(TAIPEI_TZ)
    today = now.date()
    yesterday = today - timedelta(days=1)

    today_todos = collect_today_todos(now)
    longterm_todos = collect_longterm_todos()
    print(f"[collect_report_request] 今日待辦 {len(today_todos)} 則，長期待辦 {len(longterm_todos)} 則。")

    schedule_items = collect_yesterdays_schedule(yesterday)
    schedule = [{"time": "", "title": item, "meta": "", "highlight": False} for item in schedule_items]
    print(f"[collect_report_request] 今日行程（來自前一天貼的訊息）{len(schedule)} 則。")

    weather = collect_weather()
    print(f"[collect_report_request] 天氣資料{'取得成功' if weather else '取得失敗，看板將隱藏此欄位'}。")

    todays_links = collect_interesting_links()
    interesting_links = persist_new_links(today, todays_links)
    print(f"[collect_report_request] 興趣收藏清單累積至 {len(interesting_links)} 則。")

    search_results = get_recommendation_search_results(interesting_links)
    print(f"[collect_report_request] 推薦搜尋找到 {len(search_results)} 則相關內容。")

    config.STATE_DIR.mkdir(parents=True, exist_ok=True)
    config.PENDING_REQUEST_PATH.write_text(
        json.dumps(
            {
                "date": today.isoformat(),
                "weather": weather,
                "schedule": schedule,
                "today_todos": today_todos,
                "longterm_todos": longterm_todos,
                "search_results": search_results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[collect_report_request] 已寫入 {config.PENDING_REQUEST_PATH}，等待 routine 寫內容。")


if __name__ == "__main__":
    main()
