"""組訊息、拆成多則（Discord 單則上限 2000 字）。"""

from __future__ import annotations

from datetime import date

from .classify import Event
from .rules import reminders, todays_events, week_events
from .weather import RAIN_PROB_THRESHOLD, WeatherSummary

DISCORD_LIMIT = 2000
WEEKDAYS = "一二三四五六日"
MALFORMED_FLAG = " ⚠️格式不符"


def fmt_day(d: date) -> str:
    return f"{d.month}/{d.day}（{WEEKDAYS[d.weekday()]}）"


def _flag(e: Event) -> str:
    return MALFORMED_FLAG if e.malformed else ""


def _label(e: Event) -> str:
    return f"{e.type}｜{e.name}{_flag(e)}"


def _today_line(e: Event) -> str:
    when = ""
    if e.time is not None:
        hhmm = e.time.strftime("%H:%M")
        when = f"（{hhmm} 截止）" if e.type == "作業" else f"（{hhmm}）"
    return f"・{_label(e)}{when}"


def _weather_block(w: WeatherSummary | None) -> list[str]:
    if w is None:
        return ["🌦 天氣資料取得失敗，出門前自己看一下天氣"]
    icon = "🌦" if w.rain_max >= RAIN_PROB_THRESHOLD else "🌤"
    return [
        f"{icon} 台北 {w.low}～{w.high}°C，降雨機率最高 {w.rain_max}%",
        "→ " + ("；".join(w.advice) if w.advice else "天氣穩定，不用特別準備"),
    ]


def compose(
    today: date,
    events: list[Event],
    weather: WeatherSummary | None,
    warnings: list[str] | None = None,
) -> str:
    blocks: list[list[str]] = [[f"☀️ {fmt_day(today)}早安"]]

    if warnings:
        blocks.append([f"⚠️ {w}" for w in warnings])

    blocks.append(_weather_block(weather))

    today_lines = [_today_line(e) for e in todays_events(events, today)]
    blocks.append(["📅 今天"] + (today_lines or ["・今天沒有排程"]))

    rem_lines = [
        f"・{_label(r.event)} — {r.message}（{r.event.date.month}/{r.event.date.day}）"
        for r in reminders(events, today)
    ]
    blocks.append(["⏰ 提醒"] + (rem_lines or ["・沒有需要提醒的事"]))

    if today.weekday() == 0:  # 只有週一
        week_lines = [
            fmt_day(d) + "、".join(f"{e.type} {e.name}{_flag(e)}" for e in evs)
            for d, evs in week_events(events, today).items()
        ]
        blocks.append(["📆 本週"] + (week_lines or ["這週沒有排程"]))

    return "\n\n".join("\n".join(b) for b in blocks)


def split_message(text: str, limit: int = DISCORD_LIMIT) -> list[str]:
    """切成每則 ≤ limit 字：優先在區塊（空行）之間切，其次在行之間，單行太長才硬切。"""
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""

    def flush() -> None:
        nonlocal current
        if current.strip():
            chunks.append(current.strip("\n"))
        current = ""

    for block in text.split("\n\n"):
        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) <= limit:
            current = candidate
            continue
        flush()
        if len(block) <= limit:
            current = block
            continue
        for line in block.split("\n"):
            candidate = f"{current}\n{line}" if current else line
            if len(candidate) <= limit:
                current = candidate
                continue
            flush()
            while len(line) > limit:
                chunks.append(line[:limit])
                line = line[limit:]
            current = line
    flush()
    return chunks
