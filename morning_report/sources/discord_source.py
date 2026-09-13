"""Discord 待辦／興趣連結來源。

使用者在自己的私人 Discord 伺服器裡手動維護幾個頻道：calendar（今日待辦）、一個長期待辦頻道、
interesting-links（貼感興趣的連結）。這裡直接打 Discord 的 REST API 抓最近的訊息，不需要跑一個
常駐的 Bot 程式（晨報一天只需要讀一次）。

待辦清單的完成方式很單純：使用者在 Discord 上把訊息刪掉就代表完成，這裡永遠只抓「頻道裡目前
還存在的訊息」當成待辦中的項目，不需要額外的完成狀態欄位。

「今日待辦」（calendar 頻道）另外疊加一個時間窗：只算「上次晨報跑完到這次之間」貼的訊息
（用最近 24 小時當近似值），太舊、忘記刪的訊息不會一直卡在今日待辦裡；「長期待辦」頻道則
不套這個時間窗，維持「現在還存在＝待辦中」，這樣才符合「長期」的用途。

沒有設定 DISCORD_BOT_TOKEN／頻道 ID 時，函式都直接回傳空清單，讓晨報系統其餘部分照常運作。
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


def fetch_todo_labels(channel_id: str, limit: int = 30) -> list[str]:
    """頻道裡目前還存在的訊息，一則當一項待辦，回傳時間由舊到新排列。用在長期待辦——
    不套時間窗，訊息存在多久都算待辦中，只有刪掉才算完成。"""
    try:
        messages = _fetch_recent_messages(channel_id, limit=limit)
    except requests.RequestException as exc:
        print(f"[discord_source] 讀取待辦頻道失敗（{channel_id}），這份清單視為空：{exc}")
        return []

    labels = [msg.get("content", "").strip() for msg in messages if msg.get("content", "").strip()]
    labels.reverse()  # Discord 回傳新到舊，反轉成舊到新
    return labels


def fetch_todo_labels_since(channel_id: str, since: datetime, limit: int = 50) -> list[str]:
    """頻道裡目前還存在、而且發文時間在 since 之後的訊息，一則當一項待辦。用在今日待辦——
    加了時間窗，太久以前貼的（忘記刪掉的舊訊息）不會一直出現在「今日」待辦裡。"""
    try:
        messages = _fetch_recent_messages(channel_id, limit=limit)
    except requests.RequestException as exc:
        print(f"[discord_source] 讀取待辦頻道失敗（{channel_id}），這份清單視為空：{exc}")
        return []

    matched = []
    for msg in messages:
        content = msg.get("content", "").strip()
        if not content:
            continue
        sent_at = datetime.fromisoformat(msg["timestamp"]).astimezone(TAIPEI_TZ)
        if sent_at >= since:
            matched.append(content)

    matched.reverse()  # Discord 回傳新到舊，反轉成舊到新
    return matched


def fetch_messages_posted_on(channel_id: str, target_date: date_cls, limit: int = 50) -> list[str]:
    """頻道裡「發文日期＝target_date」（台北時區）的訊息，一則當今日行程一項。
    用來把「前一天在 calendar 頻道打的待辦」當成今天的行程——跟 fetch_todo_labels 抓同一個
    頻道，但這裡是照發文日期篩選，不是看訊息現在還在不在，兩者用途不同、可能有重疊。"""
    try:
        messages = _fetch_recent_messages(channel_id, limit=limit)
    except requests.RequestException as exc:
        print(f"[discord_source] 讀取行程來源頻道失敗（{channel_id}），行程視為空：{exc}")
        return []

    matched = []
    for msg in messages:
        content = msg.get("content", "").strip()
        if not content:
            continue
        sent_at = datetime.fromisoformat(msg["timestamp"]).astimezone(TAIPEI_TZ)
        if sent_at.date() == target_date:
            matched.append(content)

    matched.reverse()  # Discord 回傳新到舊，反轉成舊到新
    return matched


def fetch_interesting_links(limit: int = 5) -> list[str]:
    """interesting-links 頻道最近幾則訊息，原樣回傳給內容產生時參考，
    不做額外的趨勢分析／篩選——那是之後才要做的事，這裡先單純轉述使用者自己存的東西。"""
    try:
        messages = _fetch_recent_messages(config.DISCORD_INTERESTING_LINKS_CHANNEL_ID, limit=limit)
    except requests.RequestException as exc:
        print(f"[discord_source] 讀取 interesting-links 頻道失敗，連結清單視為空：{exc}")
        return []

    return [msg["content"].strip() for msg in messages if msg.get("content", "").strip()]
