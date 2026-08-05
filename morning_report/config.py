"""晨報系統共用設定：路徑與環境變數。"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

MEMORY_DIR = REPO_ROOT / "memory"
PROFILE_PATH = MEMORY_DIR / "profile.md"
HABITS_PATH = MEMORY_DIR / "habits.md"
FEEDBACK_PATH = MEMORY_DIR / "feedback.md"

STATE_DIR = Path(__file__).resolve().parent / "state"
HABIT_STATE_PATH = STATE_DIR / "habit_state.json"

DOCS_DIR = REPO_ROOT / "docs"
REPORT_DATA_PATH = DOCS_DIR / "data" / "latest.json"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.environ.get("LINE_USER_ID", "")

GITHUB_PAGES_URL = os.environ.get("GITHUB_PAGES_URL", "")

# 沒有 ANTHROPIC_API_KEY 時（例如本機測試）改用固定內容，不呼叫外部 API
DRY_RUN = not ANTHROPIC_API_KEY
