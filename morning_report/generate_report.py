"""晨報系統主入口：組內容 -> 寫看板資料 -> 推 LINE -> 更新記憶。

用法：
    python -m morning_report.generate_report

本機測試（不呼叫 Groq API、不推播 LINE，只驗證資料流程）：
    直接執行即可 —— 沒有設定 GROQ_API_KEY 時會自動進入 DRY_RUN。
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone, timedelta

from . import config
from .content_generator import generate_report_content
from .habit_tracker import persist
from .line_sender import send_line_message
from .memory_reader import load_memory_context
from .sources import collect_interesting_links, collect_schedule

TAIPEI_TZ = timezone(timedelta(hours=8))


def write_board_data(report_dict: dict) -> None:
    config.REPORT_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    config.REPORT_DATA_PATH.write_text(
        json.dumps(report_dict, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> None:
    today = datetime.now(TAIPEI_TZ).date()

    memory = load_memory_context()
    schedule_events = collect_schedule(today)
    interesting_links = collect_interesting_links()

    report = generate_report_content(today, memory, schedule_events, interesting_links)
    print(f"[generate_report] 產生內容完成：{report.line_message[:50]}...")

    write_board_data(report.to_dict())
    print(f"[generate_report] 看板資料已寫入 {config.REPORT_DATA_PATH}")

    send_line_message(report.line_message)

    persist(today, memory.active_habits, report)
    print("[generate_report] 記憶已更新（habit_state.json / habits.md）。")


if __name__ == "__main__":
    main()
