"""Discord 待辦／興趣連結來源。

使用者在自己的私人 Discord 伺服器裡手動維護幾個頻道：calendar（今日待辦）、一個長期待辦頻道、
interesting-links（貼感興趣的連結）。這裡直接打 Discord 的 REST API 抓最近的訊息，不需要跑一個
常駐的 Bot 程式（晨報一天只需要讀一次）。

待辦清單的完成方式很單純：使用者在 Discord 上把訊息刪掉就代表完成，這裡永遠只抓「頻道裡目前
還存在的訊息」當成待辦中的項目，不需要額外的完成狀態欄位。

沒有設定 DISCORD_BOT_TOKEN／頻道 ID 時，函式都直接回傳空清單，讓晨報系統其餘部分照常運作。
"""

from __future__ import annotations

import requests

from .. import config

DISCORD_API_BASE = "https://discord.com/api/v10"


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


def fetch_todo_labels(channel_id: str, limit: int = 30) -> list[str]:
    """頻道裡目前還存在的訊息，一則當一項待辦，回傳時間由舊到新排列。"""
    try:
        messages = _fetch_recent_messages(channel_id, limit=limit)
    except requests.RequestException as exc:
        print(f"[discord_source] 讀取待辦頻道失敗（{channel_id}），這份清單視為空：{exc}")
        return []

    labels = [msg.get("content", "").strip() for msg in messages if msg.get("content", "").strip()]
    labels.reverse()  # Discord 回傳新到舊，反轉成舊到新
    return labels


def fetch_interesting_links(limit: int = 5) -> list[str]:
    """interesting-links 頻道最近幾則訊息，原樣回傳給內容產生時參考，
    不做額外的趨勢分析／篩選——那是之後才要做的事，這裡先單純轉述使用者自己存的東西。"""
    try:
        messages = _fetch_recent_messages(config.DISCORD_INTERESTING_LINKS_CHANNEL_ID, limit=limit)
    except requests.RequestException as exc:
        print(f"[discord_source] 讀取 interesting-links 頻道失敗，連結清單視為空：{exc}")
        return []

    return [msg["content"].strip() for msg in messages if msg.get("content", "").strip()]
