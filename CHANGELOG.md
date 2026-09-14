# Changelog

本檔案記錄這個專案「每個階段做了什麼改動」，格式參考 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/)。
版本號是這次health check時，依照 README 裡原本的「ver1 / ver2 / 第三輪 / 第四輪」回推補上的，
之後每完成一個階段，就在最上面加一段新的（日期由新到舊排列）。

## [v0.5.0] - 2026-09-14（第四輪：天氣 + 行程來源）

### Added
- `morning_report/sources/weather_source.py`：串接 Open-Meteo 預報 API（免金鑰），固定查台北座標，
  回傳 `{city, summary, low, high, rain_pct}`；查詢失敗就回傳 `None`，看板天氣欄位直接隱藏
- 今日行程：`discord_source.fetch_messages_posted_on()` 抓 calendar 頻道「前一天」貼的訊息，
  當成今天的行程（跟「今日待辦」抓同一個頻道，但篩選邏輯不同：待辦看訊息還在不在，行程看發文日期）

### Changed
- 天氣與行程都是決定性資料（不呼叫 LLM），直接在 `apply_content.py` 合併進看板資料，
  routine 完全不用碰

### Verified
- 本機測試過：天氣 API 真的查到資料；`schedule` 欄位邏輯正確（前一天沒有新訊息時回傳空陣列）

---

## [v0.4.0] - 2026-09-14（第三輪：Broadsheet 視覺改版 + 待辦清單）

### Added
- 待辦清單功能：兩個 Discord 頻道——`calendar`（改為「今日待辦」）、新的長期待辦頻道
  （環境變數 `DISCORD_LONGTERM_TODO_CHANNEL_ID`，頻道 ID 待補）。完成方式是使用者在 Discord
  刪掉訊息，程式只抓「頻道裡目前還存在的訊息」——沒有完成狀態欄位、沒有 localStorage、沒有互動
- JSON schema 擴充（`content_generator.py` 的 `ReportContent`）：新增 `issue_no`（期數，持續累加，
  不受 30 天歷史清除影響）、`greeting_sub`、`todos`、`todos_longterm`、`stats`；`recommendations`
  從字串陣列改成物件陣列（`source`/`meta`/`title`/`lede`/`body`/`url`/`thumbnail`）；移除
  `schedule_summary`

### Changed
- 視覺全面改版：套用 `design_handoff_morning_brief/README.md` 的 Broadsheet 規格（報紙風、
  Source Serif 4 + Noto Serif TC 襯線字、青/洋紅特別色），取代原本的發車看板風格

### Fixed
- 排程的 Claude Code routine（`trig_01CXDoT2FHTgZyqLu9H8RJQ2`）prompt 同步更新為新版 schema

### Verified
- 端對端在正式環境測試成功一輪：GitHub Actions 抓到真的 Discord 待辦 → routine 寫出真的內容
  （含 3 則有 lede/body 的推薦、`issue_no: 1`）→ push 回 main → 自動推播 Discord 連結，看板顯示正確

### Known limitations
- 向後相容：`docs/script.js` 能同時處理新舊格式，舊格式資料對應區塊改用簡化樣式或隱藏
- 沒有資料來源的欄位（睡眠/專注時間 stats、inbox）一律不編造，前端寫好了但後端不產生
- 長期待辦頻道 ID 尚未提供，功能暫時跳過

---

## [v0.3.0] - 2026-09-13（兩段接力 + Claude Code routine）

### Changed
- 主流程從「GitHub Actions 直接呼叫 Groq API」改成兩段接力：GitHub Actions 只做資料蒐集
  （`collect_report_request.py`），排程的 Claude Code routine 讀 repo 資料自己寫內容
  （`draft_content.json`），`apply_content.py` 合併、寫看板、commit + push，觸發
  `send-morning-link.yml` 推 Discord 連結
- 主流程完全不用 Groq，改用使用者的 Claude Code 訂閱用量，不是計費 API

### Fixed
- `vars.GITHUB_PAGES_URL` 因 GitHub Actions 不允許變數名稱以 `GITHUB_` 開頭而從未生效
  → 改名 `PAGES_BASE_URL` 並寫死預設值
- routine 的 git checkout 是 detached HEAD，裸的 `git push` 會失敗 → 改用
  `git push origin HEAD:main`

### Verified
- 端對端測試成功一輪

---

## [v0.2.0] - 2026-09-13（morning-brief-ver2 第一輪：LINE → Discord）

### Changed
- 晨報推播邏輯全面重建：不再把摘要文字塞進推播訊息，改成 render 成看板網頁，每天只推一個
  網址到 Discord
- 移除 LINE 推播，改用 `discord_push.py` 推「今天的看板網址」到指定 Discord 頻道

### Added
- 看板頁面支援歷史紀錄：上一天/下一天/回到今天/歷史清單下拉選單，資料來源
  `docs/data/{date}.json` + `manifest.json`，超過 30 天自動清除
- 新增 5 個內容來源：Hacker News、Google 新聞（皆免金鑰）、YouTube（需要 `YOUTUBE_API_KEY`）、
  Devpost（免金鑰、非官方端點）、Eventbrite（需要 `EVENTBRITE_API_TOKEN`，但該平台已停用
  第三方公開搜尋 API，目前多半查不到結果）

### Verified
- 本機測試過完整資料流程（DRY_RUN + Discord token 暫時清空），確認歷史紀錄寫入/30天自動
  清除邏輯正確

### Known limitations
- `YOUTUBE_API_KEY` / `EVENTBRITE_API_TOKEN` 尚未設定，雲端排程上自動跳過
- 本機測試時一度不小心用真的 bot token 推送測試訊息到正式頻道（已確認該頻道為私人頻道、
  不影響任何人；之後測試固定先清空這個變數）

---

## [v0.1.0] - 2026-08-06（ver1：晨報系統框架建立）

### Added
- 記憶系統基礎：`memory/profile.md` 根據真實 Gemini 對話紀錄（5篇，2026-05~07）歸納更新，
  `memory/habits.md` 建立
- 晨報系統框架：內容產生、LINE 推送、看板頁面、每日排程全部跑通，已推上 GitHub
  （[inso803/ClaudeAssistant](https://github.com/inso803/ClaudeAssistant)），GitHub Pages
  自動部署
- 內容產生改用 Groq API（Gemini 免費額度一直回傳 0，疑似 Google 端系統故障）；呼叫失敗時
  自動退回保底內容
- LINE 推播跑通（`LINE_USER_ID`、`LINE_CHANNEL_ACCESS_TOKEN` 設為 GitHub Secrets）
- Discord 來源接上：`calendar`（記行程）、`interesting-links`（收藏連結）兩個頻道，
  `discord_source.py` 直接打 Discord REST API，不需要常駐 Bot 程式
- 興趣收藏累積進 `memory/`：`interests.py` 併入 `memory/interests.md` +
  `morning_report/state/interests_state.json`，自動去重複
- 推薦引擎（`recommender.py`）：用 Groq 把興趣清單濃縮成搜尋關鍵字，打 Brave Search API
- `link_processor.py` + `interesting-links.yml`：每小時處理 interesting-links 頻道新連結，
  抓逐字稿/摘要並回覆 Discord

### Known limitations
- `BRAVE_SEARCH_API_KEY` 尚未設定，推薦引擎部分自動跳過
- 晨報內容偏空泛（尚無正在追蹤的自我提升項目，Discord 頻道也還沒有訊息）
- `link_processor.py` 尚未實際跑過，bot 需要補上 Send Messages 與 Add Reactions 權限
