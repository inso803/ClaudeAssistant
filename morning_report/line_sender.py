"""透過 LINE Messaging API 的 Push Message 把晨報推到使用者手機。"""

from __future__ import annotations

import requests

from . import config

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"


def send_line_message(text: str) -> None:
    if not config.LINE_CHANNEL_ACCESS_TOKEN or not config.LINE_USER_ID:
        print("[line_sender] 未設定 LINE_CHANNEL_ACCESS_TOKEN / LINE_USER_ID，略過推送（本機測試模式）。")
        return

    response = requests.post(
        LINE_PUSH_URL,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.LINE_CHANNEL_ACCESS_TOKEN}",
        },
        json={
            "to": config.LINE_USER_ID,
            "messages": [{"type": "text", "text": text}],
        },
        timeout=10,
    )
    response.raise_for_status()
    print("[line_sender] 推送成功。")
