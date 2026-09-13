"""根據使用者的興趣收藏清單，找類似的新內容做推薦。

流程：直接拿使用者最近收藏的幾筆內容當搜尋關鍵字（不再用 LLM 生關鍵字——這段是兩段接力流程
第一段的一部分，跑在 GitHub Actions 裡，不應該依賴任何 LLM），查詢多個內容來源
（Brave Search、Hacker News、Google 新聞、YouTube、Devpost、Eventbrite），彙整、去重複後
回傳原始搜尋結果，交給 Claude Code routine（見 collect_report_request.py 的說明）寫成推薦文字。

每個來源都各自處理自己缺 API key／查詢失敗的情況（直接回傳空清單），只要有任何一個來源
可用，這裡就能正常運作；全部都不可用時，get_recommendation_search_results 直接回傳空清單，
不影響晨報其他部分。
"""

from __future__ import annotations

import re
import urllib.parse

import requests

from . import config
from .sources import devpost_source, eventbrite_source, google_news_source, hn_source, youtube_source

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
YOUTUBE_OEMBED_URL = "https://www.youtube.com/oembed"

MAX_RESULTS_PER_SOURCE = 3
MAX_TOTAL_RESULTS = 12
MAX_QUERIES = 3

_OG_TITLE_RE = re.compile(
    r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', re.IGNORECASE
)


def _extract_keyword(url: str) -> str | None:
    """興趣清單裡存的多半是原始網址（YouTube 影片、Threads 貼文…），直接拿網址當搜尋關鍵字
    查不到東西，這裡不呼叫任何 LLM，改用免金鑰的方式抓出網址背後真正的標題來當關鍵字：
    YouTube 用官方 oEmbed 端點，其他網站嘗試抓 og:title。抓不到就回傳 None，呼叫端會跳過。"""
    domain = urllib.parse.urlparse(url).netloc.lower()
    try:
        if "youtube.com" in domain or "youtu.be" in domain:
            response = requests.get(YOUTUBE_OEMBED_URL, params={"url": url, "format": "json"}, timeout=10)
            response.raise_for_status()
            return response.json().get("title") or None

        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; MorningReportBot/1.0)"},
            timeout=10,
        )
        response.raise_for_status()
        match = _OG_TITLE_RE.search(response.text)
        return match.group(1).strip() if match else None
    except (requests.RequestException, ValueError) as exc:
        print(f"[recommender] 無法從 {url} 抓到標題，略過這筆：{exc}")
        return None


def _pick_search_queries(interests: list[str]) -> list[str]:
    """從最近收藏的幾筆內容抓出真正的標題當搜尋關鍵字（見 _extract_keyword）。"""
    queries = []
    for item in reversed(interests):
        keyword = _extract_keyword(item.strip())
        if keyword and keyword not in queries:
            queries.append(keyword)
        if len(queries) >= MAX_QUERIES:
            break
    return queries


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
    交給 Claude Code routine 消化整理成推薦文字。"""
    queries = _pick_search_queries(interests)
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
