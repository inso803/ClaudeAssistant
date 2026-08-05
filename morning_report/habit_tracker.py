"""晨報產生後，把本次追蹤的自我提升項目狀態寫回 memory/，讓隔天可以延續脈絡。

habit_state.json 是機器可讀的來源（連續天數、上次提及日期），habits.md 是給人看的鏡射＋歷程紀錄，
兩者都由這裡統一更新，不需要手動同步。
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import date as date_cls

from . import config
from .content_generator import ReportContent
from .memory_reader import HabitThread

_ACTIVE_SECTION_RE = re.compile(
    r"(## 進行中項目\n)(.*?)(\n## )", re.DOTALL
)
_HISTORY_MARKER = "## 歷史紀錄"


def load_state() -> dict:
    if not config.HABIT_STATE_PATH.exists():
        return {"active_threads": []}
    return json.loads(config.HABIT_STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    config.STATE_DIR.mkdir(parents=True, exist_ok=True)
    config.HABIT_STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def bump_streaks(today: date_cls, active_habits: list[HabitThread]) -> list[HabitThread]:
    """今天有在晨報中提到的項目，連續天數 +1、更新最後提及日期。"""
    updated = []
    for habit in active_habits:
        if habit.last_mentioned != today.isoformat():
            habit.streak_days += 1
            habit.last_mentioned = today.isoformat()
        updated.append(habit)
    return updated


def _render_active_section(active_habits: list[HabitThread]) -> str:
    if not active_habits:
        return "（目前尚無進行中項目）\n"
    blocks = []
    for h in active_habits:
        blocks.append(
            f"### {h.title}\n"
            f"- 狀態：進行中\n"
            f"- 開始追蹤：{h.started}\n"
            f"- 連續天數：{h.streak_days}\n"
            f"- 最近進度：{h.note or '（尚無紀錄）'}\n"
        )
    return "\n".join(blocks) + "\n"


def _append_history_entry(habits_md: str, report: ReportContent) -> str:
    entry = f"\n### {report.date}\n{report.closing_note or report.schedule_summary}\n"
    if _HISTORY_MARKER in habits_md:
        return habits_md.replace(_HISTORY_MARKER, f"{_HISTORY_MARKER}\n{entry}", 1)
    return habits_md + f"\n{_HISTORY_MARKER}\n{entry}"


def update_habits_md(active_habits: list[HabitThread], report: ReportContent) -> None:
    if not config.HABITS_PATH.exists():
        return
    text = config.HABITS_PATH.read_text(encoding="utf-8")

    new_section = _render_active_section(active_habits)
    if _ACTIVE_SECTION_RE.search(text):
        text = _ACTIVE_SECTION_RE.sub(lambda m: m.group(1) + new_section + m.group(3), text)

    text = _append_history_entry(text, report)
    config.HABITS_PATH.write_text(text, encoding="utf-8")


def persist(today: date_cls, active_habits: list[HabitThread], report: ReportContent) -> None:
    updated = bump_streaks(today, active_habits)
    save_state({"active_threads": [asdict(h) for h in updated]})
    update_habits_md(updated, report)
