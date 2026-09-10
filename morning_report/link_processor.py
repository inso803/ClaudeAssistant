"""interesting-links 頻道的深度處理：抓連結 -> 嘗試逐字稿 -> 摘要 -> 回覆到 Discord。

跟 sources/discord_source.py 的差異：discord_source.py 只是把頻道內容原樣轉述給晨報用，
一天只讀一次；這裡是額外疊加的、每小時跑一次的獨立流程，會實際打開連結——用 yt-dlp 抓
影片音軌、能轉逐字稿就轉（呼叫 Groq 的 Whisper API），抓不到就退回貼文本身的文字描述，
最後叫 Groq 做摘要、萃取書名／工具／Claude skill 等重點，回覆在 Discord 原訊息底下。

處理過的訊息會被加上 ✅ reaction，避免下次重複處理——這是唯一的狀態記錄方式，不用額外的
資料庫。如果某則連結處理失敗或效果不好，想要重跑，直接到 Discord 上手動把 ✅ 拿掉即可，
下次排程就會重新處理一次。

不影響 discord_source.py／晨報主流程：兩邊各自獨立讀取同一個頻道，這裡不寫入 memory/ 或
morning_report/state/ 底下的任何檔案。

用法：
    python -m morning_report.link_processor
"""

from __future__ import annotations

import json
import re
import tempfile
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

import requests
import yt_dlp

from . import config
from .content_generator import GROQ_URL
from .sources.discord_source import DISCORD_API_BASE

GROQ_TRANSCRIPTION_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_WHISPER_MODEL = "whisper-large-v3-turbo"

MAX_MESSAGES_PER_RUN = 8  # 每次排程最多處理幾則，避免單次 job 跑太久／API 用量暴增
MAX_AUDIO_DURATION_SECONDS = 1200  # 超過 20 分鐘的影片不下載轉逐字稿，直接退回文字描述
MAX_AUDIO_BYTES = 25 * 1024 * 1024  # Groq 轉錄 API 的檔案大小上限

URL_PATTERN = re.compile(r"https?://\S+")

QUALITY_BADGE = {
    "transcript": "🎧 已取得完整逐字稿",
    "caption": "📝 僅取得貼文文字描述（無法完整擷取影片內容）",
    "none": "⚠️ 無法擷取內容，請自行查看原始連結",
}

SUMMARY_SYSTEM_PROMPT = """你是使用者的個人助理，負責幫他快速消化在 Discord interesting-links 頻道裡
收藏、但還沒時間看的社群媒體貼文／影片（可能是自我提升技巧、推薦書單、工具或 Claude skill 分享等內容）。

你收到的是這則貼文的逐字稿或文字描述（依「內容品質」欄位判斷是哪一種），請幫忙產生摘要，
方便使用者滑一眼就知道值不值得回頭花時間仔細看。

規則：
- 只根據提供的文字內容整理，不要編造內容裡沒提到的細節
- 特別留意書名、工具名稱、Claude skill 名稱、其他值得記下來的具體名稱，整理進 highlights
- 如果內容品質是「僅貼文文字描述」，摘要要基於這段有限的文字，不要假裝看過完整影片
- 用簡潔口語化的繁體中文

只回傳一個 JSON 物件，不要有其他文字：
{
  "summary": "2-4句摘要",
  "highlights": ["提到的書名/工具/skill等具體重點，沒有就回傳空陣列"]
}
"""


@dataclass
class LinkContent:
    title: str
    quality: str  # "transcript" | "caption" | "none"
    text: str
    platform: str


def _detect_platform(url: str) -> str:
    domain = urllib.parse.urlparse(url).netloc.lower()
    if "youtube" in domain or "youtu.be" in domain:
        return "YouTube"
    if "instagram" in domain:
        return "Instagram"
    if "threads.net" in domain or "threads.com" in domain:
        return "Threads"
    if "facebook.com" in domain or "fb.watch" in domain:
        return "Facebook"
    if "tiktok.com" in domain:
        return "TikTok"
    return "其他平台"


def _extract_metadata(url: str) -> dict | None:
    """只拿中繼資料（標題／描述／長度），不下載。IG/Threads 常會在這步就因登入牆失敗，
    失敗是預期內的情況，呼叫端要自己接住 None。"""
    ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True, "noplaylist": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception as exc:  # yt-dlp 對不同平台丟出的例外型別不固定，故意接住所有例外
        print(f"[link_processor] yt-dlp 取得中繼資料失敗（{url}）：{exc}")
        return None


def _download_audio(url: str, dest_dir: Path) -> Path | None:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": "bestaudio[filesize<?25M]/bestaudio",
        "outtmpl": str(dest_dir / "%(id)s.%(ext)s"),
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = Path(ydl.prepare_filename(info))
    except Exception as exc:
        print(f"[link_processor] yt-dlp 下載音訊失敗（{url}）：{exc}")
        return None

    if not path.exists() or path.stat().st_size > MAX_AUDIO_BYTES:
        return None
    return path


def _transcribe_with_groq(audio_path: Path) -> str | None:
    if not config.GROQ_API_KEY:
        return None
    try:
        with audio_path.open("rb") as f:
            response = requests.post(
                GROQ_TRANSCRIPTION_URL,
                headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
                files={"file": (audio_path.name, f)},
                data={"model": GROQ_WHISPER_MODEL, "response_format": "text"},
                timeout=120,
            )
        response.raise_for_status()
        return response.text.strip() or None
    except requests.RequestException as exc:
        print(f"[link_processor] Groq 逐字稿轉換失敗：{exc}")
        return None


def _scrape_og_description(url: str) -> str | None:
    """yt-dlp 整個失敗時的最後手段：直接抓網頁的 og:description meta tag。
    IG/Threads 對未登入請求常常也會擋，抓不到是預期內的情況。"""
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; MorningReportLinkBot/1.0)"},
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException:
        return None
    match = re.search(
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
        response.text,
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def _gather_content(url: str) -> LinkContent:
    platform = _detect_platform(url)
    metadata = _extract_metadata(url)
    title = (metadata or {}).get("title") or url
    description = (metadata or {}).get("description") or ""
    duration = (metadata or {}).get("duration")

    can_try_audio = metadata is not None and (duration is None or duration <= MAX_AUDIO_DURATION_SECONDS)
    if can_try_audio:
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = _download_audio(url, Path(tmp))
            if audio_path is not None:
                transcript = _transcribe_with_groq(audio_path)
                if transcript:
                    return LinkContent(title=title, quality="transcript", text=transcript, platform=platform)

    if description:
        return LinkContent(title=title, quality="caption", text=description, platform=platform)

    scraped = _scrape_og_description(url)
    if scraped:
        return LinkContent(title=title, quality="caption", text=scraped, platform=platform)

    return LinkContent(title=title, quality="none", text="", platform=platform)


def _summarize(content: LinkContent) -> dict:
    if not config.GROQ_API_KEY or not content.text:
        return {"summary": "", "highlights": []}

    quality_label = {"transcript": "完整逐字稿", "caption": "僅貼文文字描述"}.get(content.quality, "")
    user_prompt = (
        f"平台：{content.platform}\n內容品質：{quality_label}\n標題：{content.title}\n\n"
        f"內容：\n{content.text[:6000]}"
    )
    try:
        response = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
            json={
                "model": config.GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
            },
            timeout=30,
        )
        response.raise_for_status()
        raw_text = response.json()["choices"][0]["message"]["content"]
        return json.loads(raw_text)
    except (requests.RequestException, KeyError, IndexError, json.JSONDecodeError) as exc:
        print(f"[link_processor] Groq 摘要失敗：{exc}")
        return {"summary": "", "highlights": []}


def _format_reply(url: str, content: LinkContent, summary: dict) -> str:
    title_line = content.title if content.title != url else f"{content.platform}貼文"
    lines = [f"**{title_line}**", QUALITY_BADGE.get(content.quality, ""), ""]

    if summary.get("summary"):
        lines.append(summary["summary"])
    elif content.quality == "none":
        lines.append("這則內容沒能抓到文字，建議直接點連結看原始貼文。")

    highlights = summary.get("highlights") or []
    if highlights:
        lines.append("")
        lines.append("**重點：**")
        lines.extend(f"- {h}" for h in highlights)

    return "\n".join(lines)[:1900]  # Discord 訊息上限 2000 字，留一點餘裕


def _post_reply(channel_id: str, message_id: str, text: str) -> None:
    response = requests.post(
        f"{DISCORD_API_BASE}/channels/{channel_id}/messages",
        headers={"Authorization": f"Bot {config.DISCORD_BOT_TOKEN}"},
        json={"content": text, "message_reference": {"message_id": message_id}},
        timeout=15,
    )
    response.raise_for_status()


def _mark_processed(channel_id: str, message_id: str) -> None:
    emoji = urllib.parse.quote("✅")
    response = requests.put(
        f"{DISCORD_API_BASE}/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me",
        headers={"Authorization": f"Bot {config.DISCORD_BOT_TOKEN}"},
        timeout=15,
    )
    response.raise_for_status()


def _fetch_unprocessed_messages(limit: int = 50) -> list[dict]:
    response = requests.get(
        f"{DISCORD_API_BASE}/channels/{config.DISCORD_INTERESTING_LINKS_CHANNEL_ID}/messages",
        headers={"Authorization": f"Bot {config.DISCORD_BOT_TOKEN}"},
        params={"limit": limit},
        timeout=15,
    )
    response.raise_for_status()
    messages = response.json()

    unprocessed = []
    for msg in messages:
        if msg.get("author", {}).get("bot"):
            continue
        already_done = any(
            r.get("emoji", {}).get("name") == "✅" and r.get("me")
            for r in msg.get("reactions", [])
        )
        if not already_done:
            unprocessed.append(msg)

    unprocessed.reverse()  # Discord 回傳新到舊，反轉成舊到新，照時間順序處理
    return unprocessed


def _process_message(msg: dict) -> None:
    channel_id = config.DISCORD_INTERESTING_LINKS_CHANNEL_ID
    message_id = msg["id"]
    content = msg.get("content", "").strip()

    match = URL_PATTERN.search(content)
    if not match:
        # 沒有連結的訊息（純聊天之類），標記過就跳過，不回覆也不會下次又重複判斷一次
        try:
            _mark_processed(channel_id, message_id)
        except requests.RequestException as exc:
            print(f"[link_processor] 標記 ✅ 失敗：{exc}")
        return

    url = match.group(0)
    print(f"[link_processor] 處理連結：{url}")

    try:
        link_content = _gather_content(url)
        summary = _summarize(link_content)
        reply = _format_reply(url, link_content, summary)
    except Exception as exc:  # 任何未預期錯誤都不該讓整個排程中斷，改用保底訊息回覆
        print(f"[link_processor] 處理 {url} 時發生未預期錯誤：{exc}")
        reply = f"這則連結處理時發生錯誤，建議直接看原始貼文：{url}"

    try:
        _post_reply(channel_id, message_id, reply)
    except requests.RequestException as exc:
        print(f"[link_processor] 回覆訊息失敗（可能是 bot 缺少 Send Messages 權限）：{exc}")

    try:
        _mark_processed(channel_id, message_id)
    except requests.RequestException as exc:
        print(f"[link_processor] 標記 ✅ 失敗（可能是 bot 缺少 Add Reactions 權限）：{exc}")

    time.sleep(1)  # 避免短時間內連續打 Discord API 觸發 rate limit


def main() -> None:
    if not config.DISCORD_BOT_TOKEN or not config.DISCORD_INTERESTING_LINKS_CHANNEL_ID:
        print("[link_processor] 未設定 DISCORD_BOT_TOKEN 或 DISCORD_INTERESTING_LINKS_CHANNEL_ID，略過。")
        return

    try:
        messages = _fetch_unprocessed_messages()
    except requests.RequestException as exc:
        print(f"[link_processor] 讀取頻道訊息失敗：{exc}")
        return

    if not messages:
        print("[link_processor] 沒有新連結需要處理。")
        return

    for msg in messages[:MAX_MESSAGES_PER_RUN]:
        _process_message(msg)

    remaining = len(messages) - MAX_MESSAGES_PER_RUN
    if remaining > 0:
        print(f"[link_processor] 這次處理上限 {MAX_MESSAGES_PER_RUN} 則，還有 {remaining} 則留到下次排程處理。")


if __name__ == "__main__":
    main()
