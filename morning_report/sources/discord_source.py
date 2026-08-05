"""Discord 行程／興趣連結來源。

使用者在自己的私人 Discord 伺服器裡手動維護兩個頻道：一個記錄行程（calendar），一個貼感興趣的
連結（interesting-links）。這裡直接打 Discord 的 REST API 抓最近的訊息，不需要跑一個常駐的
Bot 程式（晨報一天只需要讀一次）。

沒有設定 DISCORD_BOT_TOKEN／頻道 ID 時，兩個函式都直接回傳空清單，讓晨報系統其餘部分照常運作。
"""

from __future__ import annotations

from datetime import date as date_cls
from datetime import datetime, timedelta, timezone

import requests

from .. import config

DISCORD_API_BASE = "https://discord.com/api/v10"
TAIPEI_TZ = timezone(timedelta(hours=8))


def _fetch_recent_messages(channel_id: str, limit: int = 50) -> list[dict]:
    if not config.DISCORD_BOT_TOKEN or not channel_id:
        return []
    response = requests.get(
        f"{DISCORD_API_BASE}/channels/{channel_id}/messages",
        headers={"Authorization": f"Bot {config.DISCORD_BOT_TOKEN}"},
        params={"limit": limit},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def fetch_events(today: date_cls) -> list[dict]:
    """calendar 頻道裡「今天」貼的訊息，當成今日行程。每則訊息當一筆事件，
    time 留空，因為使用者通常會把時間寫在訊息內容裡（例如「14:00-15:00 開會」），
    直接把整句放進 title 交給後續生成內容的模型判讀就好。"""
    try:
        messages = _fetch_recent_messages(config.DISCORD_CALENDAR_CHANNEL_ID)
    except requests.RequestException as exc:
        print(f"[discord_source] 讀取 calendar 頻道失敗，行程來源視為空：{exc}")
        return []

    events = []
    for msg in messages:
        content = msg.get("content", "").strip()
        if not content:
            continue
        sent_at = datetime.fromisoformat(msg["timestamp"]).astimezone(TAIPEI_TZ)
        if sent_at.date() != today:
            continue
        events.append({"time": "", "title": content})
    return events


def fetch_interesting_links(limit: int = 5) -> list[str]:
    """interesting-links 頻道最近幾則訊息，原樣回傳給內容產生時參考，
    不做額外的趨勢分析／篩選——那是之後才要做的事，這裡先單純轉述使用者自己存的東西。"""
    try:
        messages = _fetch_recent_messages(config.DISCORD_INTERESTING_LINKS_CHANNEL_ID, limit=limit)
    except requests.RequestException as exc:
        print(f"[discord_source] 讀取 interesting-links 頻道失敗，連結清單視為空：{exc}")
        return []

    return [msg["content"].strip() for msg in messages if msg.get("content", "").strip()]
