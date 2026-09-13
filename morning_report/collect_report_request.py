"""晨報兩段接力流程 —— 第一段（跑在 GitHub Actions，維持現有每日排程）。

只做資料蒐集，不呼叫任何 LLM：
    抓 Discord 行程／收藏連結 -> 累積興趣清單 -> 多來源推薦搜尋 -> 寫成 pending_request.json

第二段是排程的 Claude Code routine，讀這份 pending_request.json（連同 repo 裡的
memory/、morning_report/state/interests_state.json）寫出今天的晨報內容，存成
draft_content.json，再跑 apply_content.py 把內容寫進看板、更新習慣追蹤、commit 回 repo。

用法：
    python -m morning_report.collect_report_request
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta

from . import config
from .interests import persist_new_links
from .recommender import get_recommendation_search_results
from .sources import collect_interesting_links, collect_schedule

TAIPEI_TZ = timezone(timedelta(hours=8))


def main() -> None:
    today = datetime.now(TAIPEI_TZ).date()

    schedule_events = collect_schedule(today)

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
                "schedule_events": schedule_events,
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
