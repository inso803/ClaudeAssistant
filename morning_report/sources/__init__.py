"""晨報的待辦／行程／興趣連結／天氣資料來源。

使用者在自己的 Discord 伺服器手動維護幾個頻道，程式每天讀一次最新內容。
collect_today_todos() / collect_longterm_todos() / collect_yesterdays_schedule() /
collect_interesting_links() / collect_weather() 是 collect_report_request.py 統一呼叫的
入口，之後要加新來源只需要在這裡註冊。
"""

from __future__ import annotations

from datetime import date as date_cls

from .. import config
from . import discord_source, weather_source


def collect_today_todos() -> list[str]:
    return discord_source.fetch_todo_labels(config.DISCORD_CALENDAR_CHANNEL_ID)


def collect_longterm_todos() -> list[str]:
    return discord_source.fetch_todo_labels(config.DISCORD_LONGTERM_TODO_CHANNEL_ID)


def collect_yesterdays_schedule(yesterday: date_cls) -> list[str]:
    """今日行程：使用者前一天在 calendar 頻道打的項目，當成今天的行程。"""
    return discord_source.fetch_messages_posted_on(config.DISCORD_CALENDAR_CHANNEL_ID, yesterday)


def collect_interesting_links() -> list[str]:
    return discord_source.fetch_interesting_links()


def collect_weather() -> dict | None:
    return weather_source.get_weather()
