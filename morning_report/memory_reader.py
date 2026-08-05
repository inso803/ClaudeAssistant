"""讀取 memory/ 底下的長期記憶，組成產生晨報內容所需的上下文。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from . import config


@dataclass
class HabitThread:
    id: str
    title: str
    started: str
    last_mentioned: str
    streak_days: int
    note: str


@dataclass
class MemoryContext:
    profile_text: str
    active_habits: list[HabitThread]
    recent_feedback: list[str]


def read_profile() -> str:
    if not config.PROFILE_PATH.exists():
        return ""
    return config.PROFILE_PATH.read_text(encoding="utf-8")


def read_habit_state() -> list[HabitThread]:
    if not config.HABIT_STATE_PATH.exists():
        return []
    data = json.loads(config.HABIT_STATE_PATH.read_text(encoding="utf-8"))
    return [HabitThread(**item) for item in data.get("active_threads", [])]


def read_recent_feedback(limit: int = 5) -> list[str]:
    """讀取 memory/feedback.md 最近的幾則回饋（每則以 '- ' 開頭的一行）。"""
    if not config.FEEDBACK_PATH.exists():
        return []
    lines = [
        line.strip().lstrip("- ").strip()
        for line in config.FEEDBACK_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("- ")
    ]
    return lines[-limit:]


def load_memory_context() -> MemoryContext:
    return MemoryContext(
        profile_text=read_profile(),
        active_habits=read_habit_state(),
        recent_feedback=read_recent_feedback(),
    )
