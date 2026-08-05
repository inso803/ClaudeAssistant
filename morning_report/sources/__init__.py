"""晨報的行程／興趣連結資料來源。

使用者在自己的 Discord 伺服器手動維護兩個頻道，程式每天讀一次最新內容。
collect_schedule() / collect_interesting_links() 是 generate_report.py 統一呼叫的入口，
之後要加新來源只需要在這裡註冊。
"""

from __future__ import annotations

from datetime import date as date_cls

from . import discord_source


def collect_schedule(today: date_cls) -> list[dict]:
    events: list[dict] = []
    events.extend(discord_source.fetch_events(today))
    return events


def collect_interesting_links() -> list[str]:
    return discord_source.fetch_interesting_links()
