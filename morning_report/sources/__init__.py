"""晨報的行程／事件資料來源。

目前只有 memory/ 內的長期記憶會被讀取；Discord 串接留待使用者另外確認、申請 Bot 後再加入
（見 discord_source.py 裡的 TODO）。collect_schedule() 是之後接新來源時統一呼叫的入口，
新增來源只需要在這裡註冊，不需要改動 generate_report.py。
"""

from __future__ import annotations

from . import discord_source


def collect_schedule() -> list[dict]:
    events: list[dict] = []
    events.extend(discord_source.fetch_events())
    return events
