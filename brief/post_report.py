"""用 morning report bot 把 Claude 整理好的 Discord 回報發到 inso803 #morning-briefing。

由 .github/workflows/discord-report.yml（workflow_dispatch）呼叫：Claude 在 GitHub 網頁按
Run workflow，把回報內容貼進 message 欄位。GitHub 的輸入欄位是單行，所以換行用字面上的
「\\n」表示，這裡再換回真正的換行。

    python -m brief.post_report --message "第一行\\n第二行" [--reply-to-brief] [--dry-run]

鐵律：只能發到 inso803 的 #morning-briefing（頻道 ID 寫死在這裡，不接受外部指定）。
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

import requests

from morning_report.sources.discord_source import DISCORD_API_BASE

from . import config
from .compose import split_message

# 鐵律：唯一允許的目的地＝inso803 伺服器的 #morning-briefing
ALLOWED_CHANNEL_ID = "1547445470555807794"


def decode_message(raw: str) -> str:
    """把字面上的 \\n 換回換行，去掉頭尾空白。"""
    return raw.replace("\\n", "\n").strip()


def _headers() -> dict:
    return {"Authorization": f"Bot {config.DISCORD_BOT_TOKEN}"}


def find_todays_brief_id(messages: list[dict], bot_user_id: str, today_label: str) -> str | None:
    """在頻道最近的訊息裡找今天 bot 發的晨報（內容以「11/23（一）早安」這種開頭）。"""
    for msg in messages:  # Discord 回傳新到舊
        author = msg.get("author") or {}
        if author.get("id") == bot_user_id and (msg.get("content") or "").lstrip().find(today_label) != -1:
            return msg["id"]
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="用 bot 發 Discord 回報")
    parser.add_argument("--message", default=os.environ.get("REPORT_MESSAGE", ""))
    parser.add_argument("--reply-to-brief", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    text = decode_message(args.message)
    if not text:
        print("[post_report] 回報內容是空的，不發送", file=sys.stderr)
        return 1
    chunks = split_message(text)

    if args.dry_run:
        for chunk in chunks:
            print(chunk)
            print("-----")
        return 0

    if not config.DISCORD_BOT_TOKEN:
        print("[post_report] 未設定 DISCORD_BOT_TOKEN", file=sys.stderr)
        return 1

    reply_to = None
    if args.reply_to_brief:
        me = requests.get(f"{DISCORD_API_BASE}/users/@me", headers=_headers(), timeout=15)
        me.raise_for_status()
        recent = requests.get(
            f"{DISCORD_API_BASE}/channels/{ALLOWED_CHANNEL_ID}/messages",
            headers=_headers(),
            params={"limit": 20},
            timeout=15,
        )
        recent.raise_for_status()
        now = datetime.now(config.TZ)
        reply_to = find_todays_brief_id(recent.json(), me.json()["id"], f"{now.month}/{now.day}（")
        if reply_to is None:
            print("[post_report] 找不到今天的晨報，改成直接發一則新訊息")

    for i, chunk in enumerate(chunks):
        body = {"content": chunk, "allowed_mentions": {"parse": []}}
        if i == 0 and reply_to:
            body["message_reference"] = {"message_id": reply_to, "fail_if_not_exists": False}
        resp = requests.post(
            f"{DISCORD_API_BASE}/channels/{ALLOWED_CHANNEL_ID}/messages",
            headers=_headers(),
            json=body,
            timeout=15,
        )
        resp.raise_for_status()
    print(f"[post_report] 已傳送 {len(chunks)} 則訊息到 #morning-briefing。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
