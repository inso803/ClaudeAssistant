"""標題解析：把日曆事件標題轉成 Event(type, course, title, ...)。

兩種格式：
- 手動建立：`類型 課名 內容`，類型固定 作業／考試／專題／其他（其他沒有課名）
- NTU COOL：`作業名稱 [課名 (課號)]`，一律視為作業
兩種都對不上 → 當作「其他」，並標記 malformed（訊息裡顯示 ⚠️格式不符）。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, time

TYPES = ("作業", "考試", "專題", "其他")

MANUAL_RE = re.compile(r"^(作業|考試|專題|其他)\s+(.+)$")
# 「Homework 1 [機器人知覺與學習 (CSIE5117)]」；課號括號可有可無
COOL_RE = re.compile(r"^(.+?)\s*\[\s*([^\[\]]+?)\s*(?:\(([^()]*)\))?\s*\]\s*$")


@dataclass(frozen=True)
class Event:
    type: str  # 作業／考試／專題／其他
    course: str  # 沒有課名時是空字串
    title: str  # 內容（不含類型與課名）
    date: date  # 台北時間的日期
    time: time | None  # 全天事件為 None
    source: str  # "google" 或 "cool"
    malformed: bool = False

    @property
    def name(self) -> str:
        """課名 + 內容，例如「計網 HW2」。"""
        return " ".join(p for p in (self.course, self.title) if p)


def classify(summary: str) -> tuple[str, str, str, bool]:
    """回傳 (type, course, title, malformed)。"""
    text = " ".join((summary or "").split())  # 壓掉多餘空白

    m = MANUAL_RE.match(text)
    if m:
        kind, rest = m.group(1), m.group(2).strip()
        if kind == "其他":
            return kind, "", rest, False
        parts = rest.split(" ", 1)
        return kind, parts[0], parts[1] if len(parts) > 1 else "", False

    m = COOL_RE.match(text)
    if m:
        return "作業", m.group(2).strip(), m.group(1).strip(), False

    return "其他", "", text or "（無標題）", True


def make_event(summary: str, day: date, at: time | None, source: str) -> Event:
    kind, course, title, malformed = classify(summary)
    return Event(kind, course, title, day, at, source, malformed)
