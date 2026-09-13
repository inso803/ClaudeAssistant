"""晨報的待辦／興趣連結資料來源。

使用者在自己的 Discord 伺服器手動維護幾個頻道，程式每天讀一次最新內容。
collect_today_todos() / collect_longterm_todos() / collect_interesting_links() 是
collect_report_request.py 統一呼叫的入口，之後要加新來源只需要在這裡註冊。
"""

from __future__ import annotations

from .. import config
from . import discord_source


def collect_today_todos() -> list[str]:
    return discord_source.fetch_todo_labels(config.DISCORD_CALENDAR_CHANNEL_ID)


def collect_longterm_todos() -> list[str]:
    return discord_source.fetch_todo_labels(config.DISCORD_LONGTERM_TODO_CHANNEL_ID)


def collect_interesting_links() -> list[str]:
    return discord_source.fetch_interesting_links()
