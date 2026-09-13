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

INTERESTS_MD_PATH = MEMORY_DIR / "interests.md"

STATE_DIR = Path(__file__).resolve().parent / "state"
HABIT_STATE_PATH = STATE_DIR / "habit_state.json"
INTERESTS_STATE_PATH = STATE_DIR / "interests_state.json"

DOCS_DIR = REPO_ROOT / "docs"
DOCS_DATA_DIR = DOCS_DIR / "data"
REPORT_DATA_PATH = DOCS_DATA_DIR / "latest.json"
REPORT_MANIFEST_PATH = DOCS_DATA_DIR / "manifest.json"
REPORT_HISTORY_RETENTION_DAYS = 30

# 兩段接力流程（見 collect_report_request.py / apply_content.py）交接用的暫存檔：
# 第一段（GitHub Actions）寫 PENDING_REQUEST_PATH，第二段（Claude Code routine）讀它、
# 寫 DRAFT_CONTENT_PATH，apply_content.py 再把兩者合併成正式看板內容
PENDING_REQUEST_PATH = STATE_DIR / "pending_request.json"
DRAFT_CONTENT_PATH = STATE_DIR / "draft_content.json"

# 只有 link_processor.py（interesting-links 深度處理）還在用 Groq，主晨報流程已經改用
# Claude Code routine 寫內容，不再呼叫 Groq。llama-3.3-70b-versatile 已下架/需要 Enterprise
# 方案，2026-09 確認過的免費可用模型改成 openai/gpt-oss-120b
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

# GitHub Actions 不允許自訂變數名稱以 GITHUB_ 開頭（會被拒絕），所以這裡改叫 PAGES_BASE_URL；
# 這個網址不是敏感資訊，預設值直接寫死，可用環境變數覆蓋
PAGES_BASE_URL = os.environ.get("PAGES_BASE_URL", "https://inso803.github.io/ClaudeAssistant/")

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
DISCORD_CALENDAR_CHANNEL_ID = os.environ.get("DISCORD_CALENDAR_CHANNEL_ID", "")
DISCORD_INTERESTING_LINKS_CHANNEL_ID = os.environ.get("DISCORD_INTERESTING_LINKS_CHANNEL_ID", "")

# ver2：晨報改成推「今天的網頁連結」到這個頻道（取代原本的 LINE 推播）。
# 預設值就是使用者指定的頻道 ID，可用環境變數覆蓋。
DISCORD_MORNING_BRIEF_CHANNEL_ID = os.environ.get(
    "DISCORD_MORNING_BRIEF_CHANNEL_ID", "1547445470555807794"
)

# 沒有設定時，推薦引擎直接跳過，不影響晨報其他部分
BRAVE_SEARCH_API_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
EVENTBRITE_API_TOKEN = os.environ.get("EVENTBRITE_API_TOKEN", "")
