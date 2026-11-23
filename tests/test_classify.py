from datetime import date, time

import pytest

from brief.classify import classify, make_event


@pytest.mark.parametrize(
    "summary, expected",
    [
        ("作業 計網 HW2", ("作業", "計網", "HW2", False)),
        ("考試 ADA 段考", ("考試", "ADA", "段考", False)),
        ("考試 自動機 期中", ("考試", "自動機", "期中", False)),
        ("專題 區塊鏈 Demo", ("專題", "區塊鏈", "Demo", False)),
        ("專題 機器人 期末海報", ("專題", "機器人", "期末海報", False)),
        ("其他 看林旭慶", ("其他", "", "看林旭慶", False)),
        ("其他 一德社課", ("其他", "", "一德社課", False)),
        ("作業  計網   HW2 第二題", ("作業", "計網", "HW2 第二題", False)),
    ],
)
def test_manual_format(summary, expected):
    assert classify(summary) == expected


@pytest.mark.parametrize(
    "summary, course, title",
    [
        ("Homework 1 [機器人知覺與學習 (CSIE5117)]", "機器人知覺與學習", "Homework 1"),
        ("Homework 4 [自動機與形式語言 (CSIE3110)]", "自動機與形式語言", "Homework 4"),
        ("Quiz 2 [微積分(一) (MATH4006)]", "微積分(一)", "Quiz 2"),
        ("Lab 3 [計算機網路]", "計算機網路", "Lab 3"),
    ],
)
def test_cool_format_is_homework(summary, course, title):
    assert classify(summary) == ("作業", course, title, False)


@pytest.mark.parametrize("summary", ["跟朋友吃飯", "作業HW2", "期中考", ""])
def test_malformed_becomes_other(summary):
    kind, course, _title, malformed = classify(summary)
    assert kind == "其他"
    assert course == ""
    assert malformed is True


def test_make_event_name():
    e = make_event("作業 計網 HW2", date(2026, 11, 11), time(23, 59), "google")
    assert e.name == "計網 HW2"
    assert make_event("其他 一德社課", date(2026, 11, 9), None, "google").name == "一德社課"
