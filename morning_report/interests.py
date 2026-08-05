"""興趣收藏清單的持久化。

Discord 的 interesting-links 頻道抓到的內容不是當天用完就丟——這裡會把新內容併進長期累積的
清單（自動去重複），存進 morning_report/state/interests_state.json（機器可讀），並鏡射一份
人類可讀的摘要到 memory/interests.md。推薦引擎（recommender.py）會讀累積後的完整清單，
而不是只看今天新增的幾筆，這樣才會隨著收藏越多、推薦越準。
"""

from __future__ import annotations

import json
from datetime import date as date_cls

from . import config

MAX_ITEMS_KEPT = 100  # state json 最多保留幾筆，避免無限成長
MAX_ITEMS_SHOWN_IN_MD = 30  # 人類可讀檔案只列最近幾筆，太多反而不好讀


def _load_state() -> dict:
    if not config.INTERESTS_STATE_PATH.exists():
        return {"items": []}
    return json.loads(config.INTERESTS_STATE_PATH.read_text(encoding="utf-8"))


def _save_state(state: dict) -> None:
    config.STATE_DIR.mkdir(parents=True, exist_ok=True)
    config.INTERESTS_STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _update_interests_md(items: list[dict]) -> None:
    lines = [
        "# 興趣收藏清單",
        "",
        "> 從 Discord 的 interesting-links 頻道累積來的收藏紀錄，晨報系統會根據這份清單去搜尋",
        "> 類似的新內容做推薦（見 recommender.py）。機器可讀的完整狀態存在",
        "> `morning_report/state/interests_state.json`，這裡只顯示最近幾筆給人看。",
        "",
        "## 最近收藏",
        "",
    ]
    recent = items[-MAX_ITEMS_SHOWN_IN_MD:][::-1]
    if recent:
        lines.extend(f"- [{item['date']}] {item['content']}" for item in recent)
    else:
        lines.append("（目前還沒有收藏任何內容）")
    lines.append("")
    config.INTERESTS_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def persist_new_links(today: date_cls, new_links: list[str]) -> list[str]:
    """把這次從 Discord 抓到的連結併進累積清單，回傳目前完整的收藏內容清單
    （不只是今天新增的，供推薦引擎參考長期喜好）。"""
    state = _load_state()
    existing_contents = {item["content"] for item in state["items"]}

    for link in new_links:
        if link not in existing_contents:
            state["items"].append({"date": today.isoformat(), "content": link})
            existing_contents.add(link)

    state["items"] = state["items"][-MAX_ITEMS_KEPT:]
    _save_state(state)
    _update_interests_md(state["items"])

    return [item["content"] for item in state["items"]]
