from datetime import date, time, timedelta

from brief.classify import make_event
from brief.compose import compose, split_message
from brief.weather import HourlyWeather, WeatherSummary, summarize

MONDAY = date(2026, 11, 9)
TUESDAY = date(2026, 11, 10)
WEATHER = WeatherSummary(low=18, high=24, rain_max=60, advice=["晚上 19～22 點可能下雨，記得帶傘"])


def ev(summary, day, at=None, source="google"):
    return make_event(summary, day, at, source)


def sample_events():
    return [
        ev("其他 一德社課", MONDAY),
        ev("Homework 1 [機器人知覺與學習 (CSIE5117)]", MONDAY, time(13, 20), "cool"),
        ev("作業 計網 HW2", date(2026, 11, 11)),
        ev("其他 宿營慶功", date(2026, 11, 12)),
        ev("其他 看林旭慶", date(2026, 11, 14)),
        ev("Homework 4 [自動機與形式語言 (CSIE3110)]", date(2026, 11, 15), time(23, 59), "cool"),
    ]


def test_monday_matches_reference_layout():
    text = compose(MONDAY, sample_events(), WEATHER)
    assert text.startswith("☀️ 11/9（一）早安")
    assert "🌦 台北 18～24°C，降雨機率最高 60%\n→ 晚上 19～22 點可能下雨，記得帶傘" in text
    assert "📅 今天\n・其他｜一德社課\n・作業｜機器人知覺與學習 Homework 1（13:20 截止）" in text
    assert "⏰ 提醒\n・作業｜計網 HW2 — 後天截止（11/11）" in text
    assert "📆 本週" in text
    assert "11/9（一）其他 一德社課、作業 機器人知覺與學習 Homework 1" in text
    assert "11/15（日）作業 自動機與形式語言 Homework 4" in text


def test_non_monday_has_no_week_section():
    text = compose(TUESDAY, sample_events(), WEATHER)
    assert text.startswith("☀️ 11/10（二）早安")
    assert "📆 本週" not in text


def test_empty_day_still_has_all_sections():
    text = compose(TUESDAY, [], WEATHER)
    assert "🌦 台北" in text
    assert "📅 今天\n・今天沒有排程" in text
    assert "⏰ 提醒\n・沒有需要提醒的事" in text


def test_empty_monday_week_section():
    assert "📆 本週\n這週沒有排程" in compose(MONDAY, [], WEATHER)


def test_weather_failure_and_source_warning():
    text = compose(TUESDAY, [], None, ["Google 日曆 讀取失敗"])
    assert "⚠️ Google 日曆 讀取失敗" in text
    assert "天氣資料取得失敗" in text


def test_malformed_flag_shown():
    text = compose(TUESDAY, [ev("吃火鍋", TUESDAY)], WEATHER)
    assert "・其他｜吃火鍋 ⚠️格式不符" in text


def test_non_homework_time_has_no_deadline_word():
    text = compose(TUESDAY, [ev("考試 ADA 段考", TUESDAY, time(9, 10))], WEATHER)
    assert "・考試｜ADA 段考（09:10）" in text


def test_short_message_not_split():
    assert split_message("hello") == ["hello"]


def test_long_message_split_under_limit():
    many = [ev(f"作業 課{i} 很長的作業名稱第{i}份", MONDAY + timedelta(days=i % 7)) for i in range(200)]
    text = compose(MONDAY, many, WEATHER)
    assert len(text) > 2000
    chunks = split_message(text)
    assert len(chunks) > 1
    assert all(len(c) <= 2000 for c in chunks)
    # 依行切，不遺失內容
    assert "\n".join(chunks).replace("\n", "") == text.replace("\n", "")


def test_single_huge_line_hard_split():
    chunks = split_message("x" * 4500)
    assert [len(c) for c in chunks] == [2000, 2000, 500]


# ---- 天氣建議 ----


def hourly(temp, rain):
    return HourlyWeather(temperature={h: temp(h) for h in range(24)}, rain_prob={h: rain(h) for h in range(24)})


def test_weather_evening_rain_and_cooling():
    w = summarize(hourly(lambda h: 24 if h < 18 else 18, lambda h: 60 if 19 <= h <= 22 else 10))
    assert (w.low, w.high, w.rain_max) == (18, 24, 60)
    assert w.advice == ["晚上 19～22 點可能下雨，記得帶傘", "晚上會轉涼（降到 18°C），帶件薄外套"]


def test_weather_daytime_rain():
    w = summarize(hourly(lambda h: 25, lambda h: 50 if 9 <= h <= 15 else 0))
    assert w.advice == ["9～15 點可能下雨，記得帶傘"]


def test_weather_rain_threshold_boundary():
    assert summarize(hourly(lambda h: 25, lambda h: 39)).advice == []
    assert summarize(hourly(lambda h: 25, lambda h: 40)).advice == ["6～23 點可能下雨，記得帶傘"]


def test_weather_rain_outside_active_hours_ignored():
    assert summarize(hourly(lambda h: 25, lambda h: 90 if h < 6 else 0)).advice == []


def test_weather_cold_all_day():
    w = summarize(hourly(lambda h: 14 if h < 12 else 17, lambda h: 0))
    assert w.advice == ["整天都偏冷（最高 17°C），記得穿外套"]


def test_weather_stable():
    assert summarize(hourly(lambda h: 26, lambda h: 10)).advice == []
