"""晨報進入點。

    python -m brief.main                              # 正式發送
    python -m brief.main --dry-run                    # 只印出、不發送
    python -m brief.main --date 2026-11-09 --dry-run  # 假裝今天是某一天
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime

from . import config
from .classify import Event
from .compose import compose, split_message
from .send import send_messages
from .sources import cool_feed, google_calendar
from .sources import weather as weather_source
from .weather import summarize


def build_message(today: date) -> str:
    events: list[Event] = []
    warnings: list[str] = []
    for label, fetch in (("Google 日曆", google_calendar.fetch_events), ("NTU COOL", cool_feed.fetch_events)):
        try:
            events.extend(fetch(today))
        except Exception as exc:  # 一個來源壞掉不影響其他部分，但要在訊息裡講
            print(f"[main] {label} 讀取失敗：{type(exc).__name__}: {exc}", file=sys.stderr)
            warnings.append(f"{label} 讀取失敗，以下行程可能不完整")

    try:
        weather = summarize(weather_source.fetch_hourly(today))
    except Exception as exc:
        print(f"[main] 天氣讀取失敗：{type(exc).__name__}: {exc}", file=sys.stderr)
        weather = None

    return compose(today, events, weather, warnings)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="日曆提醒晨報")
    parser.add_argument("--dry-run", action="store_true", help="只印出訊息，不發送")
    parser.add_argument("--date", type=date.fromisoformat, help="假裝今天是 YYYY-MM-DD")
    args = parser.parse_args(argv)

    for stream in (sys.stdout, sys.stderr):  # Windows 終端機印中文／emoji
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    today = args.date or datetime.now(config.TZ).date()
    chunks = split_message(build_message(today))

    if args.dry_run:
        for i, chunk in enumerate(chunks, 1):
            if len(chunks) > 1:
                print(f"----- 第 {i}/{len(chunks)} 則（{len(chunk)} 字）-----")
            print(chunk)
        return 0

    send_messages(chunks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
