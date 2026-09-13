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
    date: str
    greeting: str
    schedule_summary: str
    habit_highlights: list[str] = field(default_factory=list)
    links_highlight: str = ""
    recommendations: list[str] = field(default_factory=list)
    closing_note: str = ""
    ticker_message: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
