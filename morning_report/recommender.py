"""根據使用者的興趣收藏清單，找類似的新內容做推薦。

流程：先用 Groq 把累積的興趣清單濃縮成幾個搜尋關鍵字，再拿這些關鍵字去查多個內容來源
（Brave Search、Hacker News、Google 新聞、YouTube、Devpost、Eventbrite），彙整、去重複後
回傳原始搜尋結果——最終要怎麼寫成推薦文字，交給 content_generator.py 的主要生成流程處理，
這裡只負責「找資料」，不負責「寫文案」。

每個來源都各自處理自己缺 API key／查詢失敗的情況（直接回傳空清單），只要有任何一個來源
可用，這裡就能正常運作；全部都不可用時，get_recommendation_search_results 直接回傳空清單，
不影響晨報其他部分。
"""

from __future__ import annotations

import json

import requests

from . import config
from .sources import devpost_source, eventbrite_source, google_news_source, hn_source, youtube_source

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

MAX_RESULTS_PER_SOURCE = 3
MAX_TOTAL_RESULTS = 12

QUERY_SYSTEM_PROMPT = """根據使用者過去收藏的興趣清單，找出 1 到 3 個簡短的網路搜尋關鍵字，
用來搜尋「使用者可能也會喜歡的類似新內容」，不要只是重複他已經收藏過的原始連結或字句，
要往「同類型但他還沒看過的東西」去發想關鍵字。

只回傳一個 JSON 物件，不要有其他文字：
{"queries": ["關鍵字1", "關鍵字2"]}
"""


def _derive_search_queries(interests: list[str]) -> list[str]:
    if not interests or config.DRY_RUN:
        return []

    interests_text = "\n".join(f"- {i}" for i in interests[-20:])
    try:
        response = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
            json={
                "model": config.GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": QUERY_SYSTEM_PROMPT},
                    {"role": "user", "content": interests_text},
                ],
                "response_format": {"type": "json_object"},
            },
            timeout=30,
        )
        response.raise_for_status()
        raw_text = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(raw_text)
        return parsed.get("queries", [])[:3]
    except (requests.RequestException, KeyError, IndexError, json.JSONDecodeError) as exc:
        print(f"[recommender] 產生搜尋關鍵字失敗，跳過推薦：{exc}")
        return []


def _search_brave(query: str, count: int = MAX_RESULTS_PER_SOURCE) -> list[dict]:
    if not config.BRAVE_SEARCH_API_KEY:
        return []
    try:
        response = requests.get(
            BRAVE_SEARCH_URL,
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": config.BRAVE_SEARCH_API_KEY,
            },
            params={"q": query, "count": count},
            timeout=15,
        )
        response.raise_for_status()
        results = response.json().get("web", {}).get("results", [])
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "description": r.get("description", ""),
                "source": "Brave Search",
            }
            for r in results
        ]
    except (requests.RequestException, KeyError) as exc:
        print(f"[recommender] Brave Search 查詢失敗（{query}）：{exc}")
        return []


# 每個來源都是 (query: str, count: int) -> list[dict{title,url,description,source}]，
# 缺 API key 或查詢失敗時各自回傳空清單，之後要加新來源只需要在這裡註冊一行。
SOURCE_SEARCHERS = [
    _search_brave,
    hn_source.search,
    google_news_source.search,
    youtube_source.search,
    devpost_source.search,
    eventbrite_source.search,
]


def get_recommendation_search_results(interests: list[str]) -> list[dict]:
    """回傳多來源彙整後的原始搜尋結果（title/url/description/source），
    交給 content_generator 消化整理成推薦文字。"""
    if not interests:
        return []

    queries = _derive_search_queries(interests)
    if not queries:
        return []

    seen_urls: set[str] = set()
    all_results: list[dict] = []
    for query in queries:
        for searcher in SOURCE_SEARCHERS:
            for result in searcher(query, MAX_RESULTS_PER_SOURCE):
                url = result.get("url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append(result)

    return all_results[:MAX_TOTAL_RESULTS]
