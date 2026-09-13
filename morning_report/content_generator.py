"""晨報內容的資料結構。

主晨報流程已經改用兩段接力（見 collect_report_request.py / apply_content.py 的說明）：
內容不再由這裡呼叫 Groq 生成，而是由排程的 Claude Code routine 直接寫成
draft_content.json，apply_content.py 讀進來組成 ReportContent。

GROQ_URL 這個常數還留著，是因為 link_processor.py（interesting-links 頻道的深度處理，
跟主晨報流程無關）還在用 Groq 做逐字稿摘要，直接 import 這裡的常數共用。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


@dataclass
class ReportContent:
    """對應 docs/ 看板頁面(Broadsheet 版型)吃的 JSON schema。

    `schedule` / `todos` / `todos_longterm` / `weather` 都是 apply_content.py 直接從
    pending_request.json 帶過來的決定性資料，routine 不需要碰、也不會被它的文字潤飾影響：
    `schedule` 是前一天在 calendar 頻道打的項目（當成今天的行程），每則是
    {time, title, meta, highlight}，這裡 time/meta 目前固定是空字串、highlight 固定 false
    （沒有語意分析，純轉述）；`weather` 是 {city, summary, low, high, rain_pct} 或 None。
    `recommendations` 每一則是 {source, meta, title, lede, body, url, thumbnail} 物件
    （routine 寫的）；`stats` 每一則是 {value, label, tone}，tone 只有 alert/accent/plain
    三種（apply_content.py 算的，不是 AI 寫的）。沒有資料來源的欄位（inbox）乾脆不放進這個
    dataclass，前端看到欄位不存在就整區不 render。
    """

    date: str
    issue_no: int
    greeting: str
    greeting_sub: str = ""
    weather: dict | None = None
    schedule: list[dict] = field(default_factory=list)
    todos: list[str] = field(default_factory=list)
    todos_longterm: list[str] = field(default_factory=list)
    habit_highlights: list[str] = field(default_factory=list)
    links_highlight: str = ""
    recommendations: list[dict] = field(default_factory=list)
    stats: list[dict] = field(default_factory=list)
    closing_note: str = ""
    ticker_message: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
