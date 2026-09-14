"""天氣來源：Open-Meteo 預報 API，完全免費、不需要 API key。

只抓「今天」的預報（forecast_days=1），回傳看板報頭要的四個欄位：城市、天氣描述、最低/最高溫、
降雨機率。座標固定在台灣大學總校區（使用者主要活動範圍，公館），查詢失敗就回傳 None，
看板報頭的天氣欄位會直接隱藏，不影響其他部分。
"""

from __future__ import annotations

import requests

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

TAIPEI_LAT = 25.0174
TAIPEI_LON = 121.5405
CITY_NAME = "台北"

# WMO 天氣代碼對照，只取常見的幾類，簡短描述就好
_WEATHER_CODE_LABELS: dict[int, str] = {
    0: "晴天",
    1: "晴時多雲",
    2: "多雲",
    3: "陰天",
    45: "有霧",
    48: "有霧",
    51: "毛毛雨",
    53: "毛毛雨",
    55: "毛毛雨",
    56: "凍雨",
    57: "凍雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "凍雨",
    67: "凍雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "陣雪",
    80: "短暫陣雨",
    81: "短暫陣雨",
    82: "強陣雨",
    85: "陣雪",
    86: "強陣雪",
    95: "雷雨",
    96: "雷雨挾冰雹",
    99: "雷雨挾冰雹",
}


def get_weather() -> dict | None:
    try:
        response = requests.get(
            OPEN_METEO_URL,
            params={
                "latitude": TAIPEI_LAT,
                "longitude": TAIPEI_LON,
                "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "timezone": "Asia/Taipei",
                "forecast_days": 1,
            },
            timeout=10,
        )
        response.raise_for_status()
        daily = response.json()["daily"]
        code = daily["weathercode"][0]
        return {
            "city": CITY_NAME,
            "summary": _WEATHER_CODE_LABELS.get(code, "天氣多變"),
            "low": round(daily["temperature_2m_min"][0]),
            "high": round(daily["temperature_2m_max"][0]),
            "rain_pct": round(daily["precipitation_probability_max"][0]),
        }
    except (requests.RequestException, KeyError, IndexError, ValueError) as exc:
        print(f"[weather_source] 取得天氣資料失敗，看板天氣欄位將隱藏：{exc}")
        return None
