"""Google 日曆（服務帳戶）：讀今天 ~ +15 天的事件。"""

from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta

from .. import config
from ..classify import Event, make_event


def _credentials():
    from google.oauth2 import service_account

    scopes = config.GOOGLE_CALENDAR_SCOPES
    if config.GOOGLE_SERVICE_ACCOUNT_JSON:
        info = json.loads(config.GOOGLE_SERVICE_ACCOUNT_JSON)
        return service_account.Credentials.from_service_account_info(info, scopes=scopes)
    if config.GOOGLE_SERVICE_ACCOUNT_FILE:
        return service_account.Credentials.from_service_account_file(config.GOOGLE_SERVICE_ACCOUNT_FILE, scopes=scopes)
    raise RuntimeError("未設定 GOOGLE_SERVICE_ACCOUNT_JSON 或 GOOGLE_SERVICE_ACCOUNT_FILE")


def parse_start(start: dict) -> tuple[date, time | None]:
    """全天事件用 start.date，有時間的用 start.dateTime，一律轉成台北時間。"""
    if "dateTime" in start:
        dt = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00")).astimezone(config.TZ)
        return dt.date(), dt.time().replace(second=0, microsecond=0)
    return date.fromisoformat(start["date"]), None


def fetch_events(today: date) -> list[Event]:
    if not config.GOOGLE_CALENDAR_ID:
        raise RuntimeError("未設定 GOOGLE_CALENDAR_ID")
    from googleapiclient.discovery import build

    service = build("calendar", "v3", credentials=_credentials(), cache_discovery=False)
    end = today + timedelta(days=config.LOOKAHEAD_DAYS)
    time_min = datetime.combine(today, time.min, tzinfo=config.TZ).isoformat()
    time_max = datetime.combine(end + timedelta(days=1), time.min, tzinfo=config.TZ).isoformat()

    events: list[Event] = []
    page_token = None
    while True:
        resp = (
            service.events()
            .list(
                calendarId=config.GOOGLE_CALENDAR_ID,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
                pageToken=page_token,
            )
            .execute()
        )
        for item in resp.get("items", []):
            if item.get("status") == "cancelled":
                continue
            day, at = parse_start(item.get("start", {}))
            if today <= day <= end:  # 前一天開始、跨到今天的事件不算
                events.append(make_event(item.get("summary", ""), day, at, "google"))
        page_token = resp.get("nextPageToken")
        if not page_token:
            return events
