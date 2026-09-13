"""Google 新聞來源（透過公開的 Google News RSS，不需要 API key）。

Google News 沒有官方對外開放的搜尋 API，但 RSS 搜尋端點是公開可用的，
用標準函式庫解析 XML 就好，不需要額外套件。
"""

from __future__ import annotations

import urllib.parse
import xml.etree.ElementTree as ET

import requests

GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"


def search(query: str, count: int = 3) -> list[dict]:
    params = {"q": query, "hl": "zh-TW", "gl": "TW", "ceid": "TW:zh-Hant"}
    try:
        response = requests.get(
            f"{GOOGLE_NEWS_RSS_URL}?{urllib.parse.urlencode(params)}",
            timeout=15,
        )
        response.raise_for_status()
        root = ET.fromstring(response.content)
    except (requests.RequestException, ET.ParseError) as exc:
        print(f"[google_news_source] 搜尋失敗（{query}）：{exc}")
        return []

    results = []
    for item in root.findall("./channel/item")[:count]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        source = (item.findtext("source") or "Google News").strip()
        if not title or not link:
            continue
        results.append(
            {
                "title": title,
                "url": link,
                "description": f"來自 {source}",
                "source": "Google News",
            }
        )
    return results
