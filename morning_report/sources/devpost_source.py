"""Devpost 黑客松來源（透過 Devpost 網站前端在用的公開 JSON 端點，不需要 API key）。

這個端點沒有正式文件，是 devpost.com/hackathons 搜尋頁本身在用的，行為可能隨時改變；
失敗時直接回傳空清單，不影響晨報其他部分。只列「open」（還可以報名）的黑客松。
"""

from __future__ import annotations

import requests

DEVPOST_SEARCH_URL = "https://devpost.com/api/hackathons"


def search(query: str, count: int = 3) -> list[dict]:
    try:
        response = requests.get(
            DEVPOST_SEARCH_URL,
            params={"search": query, "status[]": "open"},
            headers={"Accept": "application/json"},
            timeout=15,
        )
        response.raise_for_status()
        hackathons = response.json().get("hackathons", [])
    except (requests.RequestException, ValueError) as exc:
        print(f"[devpost_source] 搜尋失敗（{query}）：{exc}")
        return []

    results = []
    for h in hackathons[:count]:
        title = h.get("title", "")
        url = h.get("url", "")
        if not title or not url:
            continue
        deadline = h.get("submission_period_dates", "")
        results.append(
            {
                "title": title,
                "url": url,
                "description": f"報名/繳交期限：{deadline}" if deadline else "Devpost 黑客松",
                "source": "Devpost",
            }
        )
    return results
