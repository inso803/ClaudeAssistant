"""提醒規則：d = 事件日期 − 今天（只看台北時間的日期，不看時分）。

要調整天數或文字，只改 REMINDER_RULES。d=0 的事件不算提醒，放在「今天」區塊。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time

from .classify import Event

REMINDER_RULES: dict[str, dict[int, str]] = {
    "考試": {
        5: "還有 5 天，準備得怎麼樣了？",
        1: "明天考，最後確認範圍",
    },
    "專題": {
        14: "兩週後，該開始規劃了",
        7: "剩一週，主要部分應該要完成",
        1: "明天就要交／展示",
    },
    "作業": {
        2: "後天截止",
    },
    "其他": {
        1: "明天",
    },
}

WEEK_DAYS = 7  # 「本週」= 今天 ~ +6 天


@dataclass(frozen=True)
class Reminder:
    event: Event
    days_left: int
    message: str


def days_until(event: Event, today: date) -> int:
    return (event.date - today).days


def _sort_key(e: Event) -> tuple:
    # 同一天內：全天事件在前，接著依時間
    return (e.date, e.time is not None, e.time or time.min)


def sort_events(events: list[Event]) -> list[Event]:
    return sorted(events, key=_sort_key)


def todays_events(events: list[Event], today: date) -> list[Event]:
    return sort_events([e for e in events if e.date == today])


def reminders(events: list[Event], today: date) -> list[Reminder]:
    out = []
    for e in sort_events(events):
        d = days_until(e, today)
        msg = REMINDER_RULES.get(e.type, {}).get(d)
        if d > 0 and msg:
            out.append(Reminder(e, d, msg))
    return out


def week_events(events: list[Event], today: date) -> dict[date, list[Event]]:
    grouped: dict[date, list[Event]] = {}
    for e in sort_events(events):
        if 0 <= days_until(e, today) < WEEK_DAYS:
            grouped.setdefault(e.date, []).append(e)
    return grouped
