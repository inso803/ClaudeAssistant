"""傳到 Discord：沿用舊版晨報的 bot（DISCORD_BOT_TOKEN）、頻道與 API base。"""

from __future__ import annotations

import requests

from morning_report.sources.discord_source import DISCORD_API_BASE

from . import config


def send_messages(chunks: list[str]) -> None:
    if not config.DISCORD_BOT_TOKEN or not config.DISCORD_CHANNEL_ID:
        raise RuntimeError("未設定 DISCORD_BOT_TOKEN 或 DISCORD_MORNING_BRIEF_CHANNEL_ID")
    for chunk in chunks:
        resp = requests.post(
            f"{DISCORD_API_BASE}/channels/{config.DISCORD_CHANNEL_ID}/messages",
            headers={"Authorization": f"Bot {config.DISCORD_BOT_TOKEN}"},
            json={"content": chunk, "allowed_mentions": {"parse": []}},
            timeout=15,
        )
        resp.raise_for_status()
    print(f"[send] 已傳送 {len(chunks)} 則訊息到 Discord。")
