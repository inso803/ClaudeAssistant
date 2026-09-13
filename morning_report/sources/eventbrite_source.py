"""Eventbrite 活動來源。

⚠️ Eventbrite 在 2019 年底已經停用了給第三方應用程式用的公開活動搜尋 API，
新申請的 API key 大多只能查自己帳號名下建立的活動，查不到公開活動列表。
這裡還是照標準方式實作 search，但實際多半會回傳空清單或 401——這是 Eventbrite
API 本身的限制，不是設定錯誤。之後如果 Eventbrite 開放新的搜尋方式，只要改這個檔案即可。

需要在 Eventbrite 帳號的 API keys 頁面申請 Personal OAuth Token，設進
EVENTBRITE_API_TOKEN 環境變數。沒有設定時直接回傳空清單。
"""

from __future__ import annotations

import requests

from .. import config

EVENTBRITE_SEARCH_URL = "https://www.eventbriteapi.com/v3/events/search/"


def search(query: str, count: int = 3, location: str = "Taipei, Taiwan") -> list[dict]:
    if not config.EVENTBRITE_API_TOKEN:
        return []

    try:
        response = requests.get(
            EVENTBRITE_SEARCH_URL,
            headers={"Authorization": f"Bearer {config.EVENTBRITE_API_TOKEN}"},
            params={"q": query, "location.address": location, "expand": "venue"},
            timeout=15,
        )
        response.raise_for_status()
        events = response.json().get("events", [])
    except (requests.RequestException, ValueError) as exc:
        print(f"[eventbrite_source] 搜尋失敗，這是 Eventbrite API 已知限制（{query}）：{exc}")
        return []

    results = []
    for e in events[:count]:
        name = e.get("name", {}).get("text", "")
        url = e.get("url", "")
        start = e.get("start", {}).get("local", "")
        if not name or not url:
            continue
        results.append(
            {
                "title": name,
                "url": url,
                "description": f"活動時間：{start}" if start else "Eventbrite 活動",
                "source": "Eventbrite",
            }
        )
    return results
