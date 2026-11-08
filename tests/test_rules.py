from datetime import date, time, timedelta

import pytest

from brief.classify import make_event
from brief.rules import REMINDER_RULES, reminders, todays_events, week_events

TODAY = date(2026, 11, 9)  # 週一

SAMPLES = {
    "考試": "考試 ADA 段考",
    "專題": "專題 區塊鏈 Demo",
    "作業": "作業 計網 HW2",
    "其他": "其他 宿營慶功",
}


def ev(summary, d, at=None, source="google"):
    return make_event(summary, TODAY + timedelta(days=d), at, source)


@pytest.mark.parametrize(
    "kind, trigger_days",
    [("考試", {5, 1}), ("專題", {14, 7, 1}), ("作業", {2}), ("其他", {1})],
)
def test_trigger_days_per_type(kind, trigger_days):
    assert set(REMINDER_RULES[kind]) == trigger_days
    for d in range(0, 16):
        got = reminders([ev(SAMPLES[kind], d)], TODAY)
        if d in trigger_days:
            assert len(got) == 1 and got[0].days_left == d
            assert got[0].message == REMINDER_RULES[kind][d]
        else:
            assert got == [], f"{kind} d={d} 不該觸發"


def test_reminder_texts():
    assert REMINDER_RULES["考試"][5] == "還有 5 天，準備得怎麼樣了？"
    assert REMINDER_RULES["作業"][2] == "後天截止"
    assert REMINDER_RULES["專題"][1] == "明天就要交／展示"


def test_time_of_day_does_not_affect_d():
    # 後天 00:01 跟後天 23:59 都是 d=2
    early = ev("作業 計網 HW2", 2, time(0, 1))
    late = ev("作業 計網 HW3", 2, time(23, 59))
    assert len(reminders([early, late], TODAY)) == 2


def test_cool_and_malformed_events_follow_their_type():
    cool = ev("Homework 1 [機器人知覺與學習 (CSIE5117)]", 2, time(23, 59), "cool")
    bad = ev("吃飯", 1)
    got = reminders([cool, bad], TODAY)
    assert [r.event.type for r in got] == ["其他", "作業"]  # 依日期排序


def test_today_not_in_reminders():
    e = ev("其他 一德社課", 0)
    assert reminders([e], TODAY) == []
    assert todays_events([e], TODAY) == [e]


def test_today_sorted_all_day_first():
    timed = ev("作業 計網 HW2", 0, time(13, 20))
    all_day = ev("其他 一德社課", 0)
    early = ev("考試 ADA 段考", 0, time(9, 10))
    assert todays_events([timed, early, all_day], TODAY) == [all_day, early, timed]


def test_week_groups_today_to_plus_six():
    events = [ev("其他 一德社課", 0), ev("作業 計網 HW2", 2), ev("作業 自動機 HW4", 6), ev("其他 太遠", 7)]
    week = week_events(events, TODAY)
    assert list(week) == [TODAY, TODAY + timedelta(days=2), TODAY + timedelta(days=6)]
