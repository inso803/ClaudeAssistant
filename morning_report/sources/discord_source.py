"""Discord 行程來源 —— 尚未實作。

規劃：使用者會在自己的私人 Discord 伺服器手動記錄行程／事項，之後這裡會加上一個 Discord Bot
（或直接呼叫 Discord API 讀取指定頻道訊息），把當天相關的訊息轉成事件清單。

需要使用者先申請 Discord Bot Token、設定伺服器權限才能串接，這部分留待使用者另外確認後再實作，
目前先回傳空清單，讓晨報系統的其餘部分可以先跑通。
"""

from __future__ import annotations


def fetch_events() -> list[dict]:  # noqa: D401 — 之後接上 Discord 後改成實際查詢
    return []
