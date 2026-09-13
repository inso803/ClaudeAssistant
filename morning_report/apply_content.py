"""晨報兩段接力流程 —— 第二段的機械部分（由排程的 Claude Code routine 執行）。

Routine 自己（用 Claude 寫作，不呼叫任何 API）已經把今天的文案寫進
morning_report/state/draft_content.json（greeting／greeting_sub／habit_highlights／
links_highlight／recommendations／closing_note／ticker_message），這支腳本負責：
- 待辦清單（today_todos／longterm_todos）直接從 pending_request.json 帶過來，routine 不用碰，
  也不會被它的文字潤飾影響
- 「昨天的你」數字（stats）用現有資料算，不是 AI 寫的
- 把兩邊合併、寫進看板資料（含歷史紀錄、期數），更新習慣追蹤，最後 commit + push

push 上 main 的 docs/data/** 變動會觸發 send-morning-link.yml，由它負責推 Discord 連結
（那支 workflow 才有 DISCORD_BOT_TOKEN，routine 本身不需要碰任何 secret）。

用法（routine 在寫完 draft_content.json 之後執行）：
    python -m morning_report.apply_content
"""

from __future__ import annotations

import json
import subprocess
from datetime import date as date_cls

from . import config
from .board_writer import next_issue_no, write_report
from .content_generator import ReportContent
from .habit_tracker import persist
from .memory_reader import load_memory_context


def _load_json(path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"找不到 {path}，routine 應該要先把內容寫進這個檔案")
    return json.loads(path.read_text(encoding="utf-8"))


def _saved_links_count() -> int:
    if not config.INTERESTS_STATE_PATH.exists():
        return 0
    data = json.loads(config.INTERESTS_STATE_PATH.read_text(encoding="utf-8"))
    return len(data.get("items", []))


def _build_stats(memory) -> list[dict]:
    """只放有真實資料來源的數字（追蹤中的習慣、收藏連結），沒有的（睡眠、專注時間）
    就不編——這兩個目前 repo 裡沒有任何來源。"""
    return [
        {"value": str(len(memory.active_habits)), "label": "追蹤中的習慣", "tone": "plain"},
        {"value": str(_saved_links_count()), "label": "收藏連結", "tone": "accent"},
    ]


def main() -> None:
    pending = _load_json(config.PENDING_REQUEST_PATH)
    draft = _load_json(config.DRAFT_CONTENT_PATH)

    today = date_cls.fromisoformat(pending["date"])
    memory = load_memory_context()

    report = ReportContent(
        date=today.isoformat(),
        issue_no=next_issue_no(today),
        greeting=draft.get("greeting", ""),
        greeting_sub=draft.get("greeting_sub", ""),
        todos=pending.get("today_todos", []),
        todos_longterm=pending.get("longterm_todos", []),
        habit_highlights=draft.get("habit_highlights", []),
        links_highlight=draft.get("links_highlight", ""),
        recommendations=draft.get("recommendations", []),
        stats=_build_stats(memory),
        closing_note=draft.get("closing_note", ""),
        ticker_message=draft.get("ticker_message", ""),
    )

    write_report(today, report.to_dict())
    print(f"[apply_content] 看板資料已寫入（含歷史紀錄），日期 {today.isoformat()}，第 {report.issue_no} 期")

    persist(today, memory.active_habits, report)
    print("[apply_content] 記憶已更新（habit_state.json / habits.md）。")

    # pending_request.json 是 stage 1 commit 進 repo 的，這裡刪掉後照樣 git add 讓刪除也
    # 一起 commit；draft_content.json 只是 routine 本機寫的暫存檔，從沒進過 git，單純刪掉
    # 就好，不用（也不能）git add 一個從未被追蹤過的已刪除檔案
    config.PENDING_REQUEST_PATH.unlink(missing_ok=True)
    config.DRAFT_CONTENT_PATH.unlink(missing_ok=True)

    subprocess.run(["git", "config", "user.name", "morning-report-routine"], check=True, cwd=config.REPO_ROOT)
    subprocess.run(
        ["git", "config", "user.email", "actions@users.noreply.github.com"], check=True, cwd=config.REPO_ROOT
    )
    subprocess.run(
        [
            "git",
            "add",
            "docs/data",
            "memory/habits.md",
            str(config.HABIT_STATE_PATH.relative_to(config.REPO_ROOT)),
            str(config.ISSUE_COUNTER_PATH.relative_to(config.REPO_ROOT)),
            str(config.PENDING_REQUEST_PATH.relative_to(config.REPO_ROOT)),
        ],
        check=True,
        cwd=config.REPO_ROOT,
    )
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=config.REPO_ROOT)
    if diff.returncode == 0:
        print("[apply_content] 沒有變更需要 commit。")
        return

    subprocess.run(
        ["git", "commit", "-m", f"chore: apply morning report content for {today.isoformat()}"],
        check=True,
        cwd=config.REPO_ROOT,
    )
    # 用 HEAD:main 而不是裸的 git push：Claude Code routine 的 checkout 常常是 detached HEAD
    # （不在任何分支上），這時候 `git push` 會直接失敗（"You are not currently on a branch"）。
    # HEAD:main 不管目前是否在分支上都能正確把目前這個 commit 推到遠端的 main。
    subprocess.run(["git", "push", "origin", "HEAD:main"], check=True, cwd=config.REPO_ROOT)
    print("[apply_content] 已 commit + push 回 main。")


if __name__ == "__main__":
    main()
