"""把當天的晨報內容寫進 docs/data/，讓 GitHub Pages 上的看板網頁可以讀取、往回翻歷史紀錄。

檔案配置：
- docs/data/{date}.json  ：當天的完整內容（看板網頁用 ?date=YYYY-MM-DD 讀這份）
- docs/data/latest.json  ：跟今天同一份內容的複本，網頁沒帶 ?date= 時預設讀這份
- docs/data/manifest.json：目前還保留著的日期清單（新到舊），超過保留天數的日期會被移出
  清單，對應的 {date}.json 也會一併刪除——不用手動清，每次產生晨報時自動處理。
"""

from __future__ import annotations

import json
from datetime import date as date_cls, timedelta

from . import config


def _dated_path(day_str: str):
    return config.DOCS_DATA_DIR / f"{day_str}.json"


def _load_manifest() -> list[str]:
    if not config.REPORT_MANIFEST_PATH.exists():
        return []
    return json.loads(config.REPORT_MANIFEST_PATH.read_text(encoding="utf-8")).get("dates", [])


def _prune_old_entries(dates: list[str], today: date_cls) -> list[str]:
    cutoff = today - timedelta(days=config.REPORT_HISTORY_RETENTION_DAYS)
    kept = []
    for day_str in dates:
        try:
            keep = date_cls.fromisoformat(day_str) >= cutoff
        except ValueError:
            keep = False
        if keep:
            kept.append(day_str)
        else:
            _dated_path(day_str).unlink(missing_ok=True)
    return kept


def write_report(today: date_cls, report_dict: dict) -> None:
    config.DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today_str = today.isoformat()
    payload = json.dumps(report_dict, ensure_ascii=False, indent=2)

    _dated_path(today_str).write_text(payload, encoding="utf-8")
    config.REPORT_DATA_PATH.write_text(payload, encoding="utf-8")

    dates = _load_manifest()
    if today_str not in dates:
        dates.append(today_str)
    dates.sort(reverse=True)
    dates = _prune_old_entries(dates, today)

    config.REPORT_MANIFEST_PATH.write_text(
        json.dumps({"dates": dates}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
