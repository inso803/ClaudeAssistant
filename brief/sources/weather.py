"""天氣：Open-Meteo（免金鑰）今天逐小時氣溫與降雨機率。

座標沿用舊版 morning_report/sources/weather_source.py（台大總校區，位於大安區；
v0.5.0 修正過的座標），舊程式本身沒有改動。
"""

from __future__ import annotations

from datetime import date

import requests

from morning_report.sources.weather_source import OPEN_METEO_URL, TAIPEI_LAT, TAIPEI_LON

from ..weather import HourlyWeather


def fetch_hourly(today: date) -> HourlyWeather:
    resp = requests.get(
        OPEN_METEO_URL,
        params={
            "latitude": TAIPEI_LAT,
            "longitude": TAIPEI_LON,
            "hourly": "temperature_2m,precipitation_probability",
            "timezone": "Asia/Taipei",
            "start_date": today.isoformat(),
            "end_date": today.isoformat(),
        },
        timeout=10,
    )
    resp.raise_for_status()
    hourly = resp.json()["hourly"]
    temps: dict[int, float] = {}
    rain: dict[int, int] = {}
    for stamp, t, p in zip(hourly["time"], hourly["temperature_2m"], hourly["precipitation_probability"]):
        hour = int(stamp[11:13])  # "2026-11-09T19:00"
        if t is not None:
            temps[hour] = t
        if p is not None:
            rain[hour] = p
    return HourlyWeather(temperature=temps, rain_prob=rain)
