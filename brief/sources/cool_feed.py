"""NTU COOL：直接讀 iCal 訂閱 feed（COOL 的訂閱日曆無法共用給服務帳戶）。"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

import requests

from .. import config
from ..classify import Event, make_event


def parse_ical(data: bytes, today: date) -> list[Event]:
    from icalendar import Calendar

    end = today + timedelta(days=config.LOOKAHEAD_DAYS)
    events: list[Event] = []
    for comp in Calendar.from_ical(data).walk("VEVENT"):
        start = comp.get("DTSTART")
        if start is None:
            continue
        value = start.dt
        at: time | None = None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=config.TZ)
            value = value.astimezone(config.TZ)
            day, at = value.date(), value.time().replace(second=0, microsecond=0)
        else:
            day = value
        if today <= day <= end:
            events.append(make_event(str(comp.get("SUMMARY", "")), day, at, "cool"))
    return events


def fetch_events(today: date) -> list[Event]:
    if not config.COOL_CALENDAR_FEED_URL:
        raise RuntimeError("未設定 COOL_CALENDAR_FEED_URL")
    resp = requests.get(config.COOL_CALENDAR_FEED_URL, timeout=20)
    resp.raise_for_status()
    return parse_ical(resp.content, today)
