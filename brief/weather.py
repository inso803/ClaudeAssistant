"""天氣建議（純邏輯，不打 API）：輸入今天逐小時的氣溫與降雨機率，產生摘要與一句建議。"""

from __future__ import annotations

from dataclasses import dataclass

# ---- 可調整的門檻 ----
RAIN_PROB_THRESHOLD = 40  # 06～23 點任一小時降雨機率 ≥ 這個值 → 建議帶傘
COLD_LOW_THRESHOLD = 16  # 06～23 點最低溫 ≤ 這個值 → 建議帶外套
EVENING_COLD_THRESHOLD = 18  # 晚上 18～23 點最低溫 ≤ 這個值 → 建議帶外套
ALL_DAY_COLD_MAX = 20  # 白天最高溫 ≤ 這個值 → 算「整天都冷」，否則算「晚上變冷」

ACTIVE_HOURS = range(6, 24)  # 06:00 ~ 23:00
DAY_HOURS = range(6, 18)  # 白天 06:00 ~ 17:00
EVENING_HOURS = range(18, 24)  # 晚上 18:00 ~ 23:00


@dataclass(frozen=True)
class HourlyWeather:
    """key 是小時（0~23）。"""

    temperature: dict[int, float]
    rain_prob: dict[int, int]


@dataclass(frozen=True)
class WeatherSummary:
    low: int
    high: int
    rain_max: int
    advice: list[str]


def _pick(values: dict[int, float], hours: range) -> list[float]:
    return [values[h] for h in hours if h in values]


def _span(hours: list[int]) -> str:
    return f"{hours[0]} 點" if hours[0] == hours[-1] else f"{hours[0]}～{hours[-1]} 點"


def _rain_advice(w: HourlyWeather) -> str | None:
    rainy = [h for h in ACTIVE_HOURS if w.rain_prob.get(h, 0) >= RAIN_PROB_THRESHOLD]
    if not rainy:
        return None
    evening = [h for h in rainy if h in EVENING_HOURS]
    if len(evening) * 2 > len(rainy):  # 超過一半的雨落在晚上 → 主要集中在晚上
        return f"晚上 {_span(evening)}可能下雨，記得帶傘"
    return f"{_span(rainy)}可能下雨，記得帶傘"


def _coat_advice(w: HourlyWeather) -> str | None:
    temps = _pick(w.temperature, ACTIVE_HOURS)
    if not temps:
        return None
    day = _pick(w.temperature, DAY_HOURS) or temps
    evening = _pick(w.temperature, EVENING_HOURS)
    low, day_max = min(temps), max(day)
    evening_min = min(evening) if evening else None

    # 只看絕對溫度，不看日夜溫差
    cold = low <= COLD_LOW_THRESHOLD
    evening_cold = evening_min is not None and evening_min <= EVENING_COLD_THRESHOLD
    if not (cold or evening_cold):
        return None
    if day_max <= ALL_DAY_COLD_MAX:
        return f"整天都偏冷（最高 {round(day_max)}°C），記得穿外套"
    if evening_cold:
        return f"晚上會轉涼（降到 {round(evening_min)}°C），帶件薄外套"
    # 冷的是清晨（例如 6 點 15°C），晚上不冷
    return f"早上偏涼（最低 {round(low)}°C），帶件薄外套"


def summarize(w: HourlyWeather) -> WeatherSummary | None:
    temps = _pick(w.temperature, ACTIVE_HOURS)
    if not temps:
        return None
    rain = [w.rain_prob[h] for h in ACTIVE_HOURS if h in w.rain_prob]
    advice = [a for a in (_rain_advice(w), _coat_advice(w)) if a]
    return WeatherSummary(
        low=round(min(temps)),
        high=round(max(temps)),
        rain_max=round(max(rain)) if rain else 0,
        advice=advice,
    )
