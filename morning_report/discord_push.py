"""把「今天的晨報網址」推到 Discord 頻道，取代原本的 LINE 推播（ver2）。

推播內容只有連結，不把摘要文字塞進訊息——今天的內容都在網頁看板上，點連結進去看就好。
沿用跟 sources/discord_source.py、link_processor.py 同一支 bot／token，這支 bot 需要
已經被加進目標頻道所在的伺服器，並且有該頻道的 Send Messages 權限。
"""

from __future__ import annotations

import requests

from . import config
from .sources.discord_source import DISCORD_API_BASE


def send_morning_link(url: str) -> None:
    if not config.DISCORD_BOT_TOKEN or not config.DISCORD_MORNING_BRIEF_CHANNEL_ID:
        print("[discord_push] 未設定 DISCORD_BOT_TOKEN 或 DISCORD_MORNING_BRIEF_CHANNEL_ID，略過推送（本機測試模式）。")
        return

    try:
        response = requests.post(
            f"{DISCORD_API_BASE}/channels/{config.DISCORD_MORNING_BRIEF_CHANNEL_ID}/messages",
            headers={"Authorization": f"Bot {config.DISCORD_BOT_TOKEN}"},
            json={"content": f"📋 今日晨報：{url}"},
            timeout=15,
        )
        response.raise_for_status()
        print("[discord_push] 推送成功。")
    except requests.RequestException as exc:
        print(
            "[discord_push] 推送失敗，請檢查："
            "1) bot 是否已被加進該頻道所在的伺服器；"
            "2) bot 在該頻道是否有 Send Messages 權限；"
            "3) DISCORD_BOT_TOKEN 是否仍然有效。"
            f" 錯誤內容：{exc}"
        )
