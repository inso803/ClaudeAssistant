"""YouTube 影片來源（透過 YouTube Data API v3 的 search.list）。

需要在 Google Cloud Console 申請一組免費的 YouTube Data API key，設進
YOUTUBE_API_KEY 環境變數。沒有設定時直接回傳空清單，不影響晨報其他部分。
"""

from __future__ import annotations

import requests

from .. import config

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def search(query: str, count: int = 3) -> list[dict]:
    if not config.YOUTUBE_API_KEY:
        return []

    try:
        response = requests.get(
            YOUTUBE_SEARCH_URL,
            params={
                "key": config.YOUTUBE_API_KEY,
                "q": query,
                "part": "snippet",
                "type": "video",
                "maxResults": count,
                "relevanceLanguage": "zh-Hant",
            },
            timeout=15,
        )
        response.raise_for_status()
        items = response.json().get("items", [])
    except (requests.RequestException, ValueError) as exc:
        print(f"[youtube_source] 搜尋失敗（{query}）：{exc}")
        return []

    results = []
    for item in items:
        video_id = item.get("id", {}).get("videoId")
        snippet = item.get("snippet", {})
        if not video_id or not snippet.get("title"):
            continue
        results.append(
            {
                "title": snippet["title"],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "description": snippet.get("channelTitle", ""),
                "source": "YouTube",
            }
        )
    return results
