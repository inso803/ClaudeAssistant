"""v1.0.0 晨報設定：環境變數與時區。

本機從 .env 讀取（沿用 morning_report.config 的 load_dotenv），GitHub Actions 上直接用
Secrets 注入的環境變數。
"""

from __future__ import annotations

import os
from zoneinfo import ZoneInfo

# 匯入時會順便 load_dotenv(REPO_ROOT / ".env")，並提供 Discord token / 頻道 ID
from morning_report import config as legacy_config

TZ = ZoneInfo("Asia/Taipei")

# 查詢範圍：今天 ~ 今天 + LOOKAHEAD_DAYS（含）
LOOKAHEAD_DAYS = 15

# Google 日曆：服務帳戶金鑰二選一——
#   GOOGLE_SERVICE_ACCOUNT_JSON：整份 JSON 內容（GitHub Actions 用）
#   GOOGLE_SERVICE_ACCOUNT_FILE：金鑰檔路徑（本機用，金鑰檔請放在 repo 外面）
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
GOOGLE_SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "")
GOOGLE_CALENDAR_ID = os.environ.get("GOOGLE_CALENDAR_ID", "")
# 之後要寫回日曆，所以先用完整權限；這一版只讀
GOOGLE_CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]

COOL_CALENDAR_FEED_URL = os.environ.get("COOL_CALENDAR_FEED_URL", "")

# 沿用舊版晨報的 Discord bot 與頻道（channel 預設 1547445470555807794）
DISCORD_BOT_TOKEN = legacy_config.DISCORD_BOT_TOKEN
DISCORD_CHANNEL_ID = legacy_config.DISCORD_MORNING_BRIEF_CHANNEL_ID
