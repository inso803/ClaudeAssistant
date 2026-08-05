"""晨報系統共用設定：路徑與環境變數。"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# 本機測試時從 .env 讀取設定；GitHub Actions 上直接用 repo secrets 注入的環境變數，
# 找不到 .env 也不會報錯
try:
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

MEMORY_DIR = REPO_ROOT / "memory"
PROFILE_PATH = MEMORY_DIR / "profile.md"
HABITS_PATH = MEMORY_DIR / "habits.md"
FEEDBACK_PATH = MEMORY_DIR / "feedback.md"

STATE_DIR = Path(__file__).resolve().parent / "state"
HABIT_STATE_PATH = STATE_DIR / "habit_state.json"

DOCS_DIR = REPO_ROOT / "docs"
REPORT_DATA_PATH = DOCS_DIR / "data" / "latest.json"

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.environ.get("LINE_USER_ID", "")

GITHUB_PAGES_URL = os.environ.get("GITHUB_PAGES_URL", "")

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
DISCORD_CALENDAR_CHANNEL_ID = os.environ.get("DISCORD_CALENDAR_CHANNEL_ID", "")
DISCORD_INTERESTING_LINKS_CHANNEL_ID = os.environ.get("DISCORD_INTERESTING_LINKS_CHANNEL_ID", "")

# 沒有 GROQ_API_KEY 時（例如本機測試）改用固定內容，不呼叫外部 API
DRY_RUN = not GROQ_API_KEY
