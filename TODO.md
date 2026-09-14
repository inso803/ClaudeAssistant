# TODO

還沒做的事。之後建議整批搬進 GitHub Issues（一個項目一個 Issue），這份檔案先當作過渡期的暫存清單。
完成的項目請直接刪除這一行，不用留 ✅ 記錄——「做完了什麼」屬於 [CHANGELOG.md](CHANGELOG.md) 的事。

## 功能相關

- [ ] 提供長期待辦 Discord 頻道的 ID，設進 repo Secrets：`DISCORD_LONGTERM_TODO_CHANNEL_ID`
      （開發者模式下對頻道按右鍵「複製頻道 ID」）。沒設定的話這個功能會自動跳過，不影響其他部分。
- [ ]（可選）申請 Brave Search API key：到 brave.com/search/api 註冊、選 Free tier
      （每月 2000 次查詢免費），設進 repo Secrets：`BRAVE_SEARCH_API_KEY`
- [ ]（可選）申請 YouTube Data API key：Google Cloud Console 建專案 → 啟用
      「YouTube Data API v3」→ 建立 API 金鑰，設進 repo Secrets：`YOUTUBE_API_KEY`
- [ ]（可選，效果可能有限）申請 Eventbrite Personal OAuth Token：Eventbrite 已停用第三方公開
      活動搜尋，申請了也可能一直查不到結果，優先度最低。設進 repo Secrets：`EVENTBRITE_API_TOKEN`
- [ ] 繼續在 Discord 的 `calendar`（今日待辦）／長期待辦／`interesting-links` 頻道貼東西，
      晨報才有真的素材可以講

## 開發流程相關（2026-09-14 architecture review 產出）

- [ ] 確認 `.github/workflows/` 是否真的少了 `interesting-links.yml`，並修正 README 或補回檔案
- [ ] 決定 repo 要不要維持公開（個資：`memory/profile.md`／`habits.md`／`interests.md`／
      `feedback.md` 目前是公開的）——見兩個選項：搬去 Netlify/Vercel 之後 repo 改 private，
      或只把 `memory/` 搬到別的 private 儲存位置
- [ ] 把這份 TODO.md 遷移成 GitHub Issues + 一個簡單的 Projects 看板（Backlog/In Progress/Done）
- [ ] 幫 `board_writer.py` 寫前 2-3 個 pytest 測試（30 天自動清除邏輯、`next_issue_no()` 期數累加）
- [ ] 加一個 `.github/workflows/test.yml`，PR 時自動跑 pytest
- [ ] 加 ruff（lint）+ black（格式化）設定檔；考慮加 pre-commit hook 跑 detect-secrets/gitleaks
      （曾經不小心用真的 bot token 推送過測試訊息，見 CHANGELOG v0.2.0）
- [ ] main 分支加保護規則，改成 feature branch + PR 流程（即使一人開發，自己 review 一次 diff 再合併）
- [ ] 把 Claude Code routine（`trig_01CXDoT2FHTgZyqLu9H8RJQ2`）的 prompt 存一份到
      `docs/routine-prompt.md`，之後改動這個 prompt 就跟改 code 一樣走 commit
- [ ] 新增 `docs/decisions/`（ADR），把幾次重大轉向的「為什麼」記下來：
      LINE → Discord、Groq → Claude Code routine、發車看板 → Broadsheet 視覺改版
- [ ] 重大階段完成時打 git tag（例如 `v0.5.0`），讓 GitHub Releases 自動形成版本歷史
