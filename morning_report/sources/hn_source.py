"""Hacker News 內容來源（透過 Algolia 的 HN Search API，不需要 API key）。

給 recommender.py 用來搜尋跟使用者興趣類似的 HN 討論串，回傳格式跟其他來源一致
（title/url/description），方便統一彙整、去重複。
"""

from __future__ import annotations

import requests

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"


def search(query: str, count: int = 3) -> list[dict]:
    try:
        response = requests.get(
            HN_SEARCH_URL,
            params={"query": query, "tags": "story", "hitsPerPage": count},
            timeout=15,
        )
        response.raise_for_status()
        hits = response.json().get("hits", [])
    except (requests.RequestException, ValueError) as exc:
        print(f"[hn_source] 搜尋失敗（{query}）：{exc}")
        return []

    results = []
    for hit in hits:
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
        title = hit.get("title") or hit.get("story_title") or ""
        if not title:
            continue
        results.append(
            {
                "title": title,
                "url": url,
                "description": f"HN {hit.get('points', 0)} 分・{hit.get('num_comments', 0)} 則留言",
                "source": "Hacker News",
            }
        )
    return results
