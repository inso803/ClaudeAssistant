"""晨報兩段接力流程 —— 第三段：docs/data/** 有變動時觸發，推 Discord 連結。

這是唯一會碰 DISCORD_BOT_TOKEN 的地方（跟 discord_source.py／link_processor.py 共用同一支
bot），刻意跟寫內容的 Claude Code routine 分開，routine 完全不需要碰任何 secret。

用法：
    python -m morning_report.send_today_link
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from . import config
from .discord_push import send_morning_link

TAIPEI_TZ = timezone(timedelta(hours=8))


def main() -> None:
    today = datetime.now(TAIPEI_TZ).date()
    base = config.PAGES_BASE_URL.rstrip("/")
    send_morning_link(f"{base}/?date={today.isoformat()}")


if __name__ == "__main__":
    main()
