# 個人 AI 助手

邱彥碩的個人 AI 助手專案：長期記憶系統 + 晨報自動化系統。詳細專案背景與執行原則見
[CLAUDE.md](CLAUDE.md)。

## 專案結構

```
memory/                     長期記憶（見 memory/README.md）
  profile.md                 使用者核心背景摘要
  habits.md                  自我提升進度追蹤（人類可讀版）
  interests.md                興趣收藏清單（人類可讀版，從 Discord 累積）
  feedback.md                使用者對晨報的回饋紀錄
  import_gemini_takeout.py   把 Google Takeout 匯出檔解析成純文字
  raw/                        原始匯出檔（.gitignore 排除）

morning_report/              晨報系統（兩段接力，見下方「目前狀態」）
  collect_report_request.py   第一段（GitHub Actions）：抓 Discord 待辦/收藏連結、多來源搜尋，
                                 不呼叫任何 LLM，寫成 morning_report/state/pending_request.json
  apply_content.py             第二段機械部分（Claude Code routine 執行）：把 routine 寫的
                                 draft_content.json 跟 pending_request.json 合併、寫看板資料、
                                 更新習慣追蹤、commit + push 回 main
  send_today_link.py           第三段（GitHub Actions，docs/data/** 有變動就觸發）：推 Discord 連結
  memory_reader.py            讀取 memory/ 的內容
  interests.py                 興趣收藏清單持久化（Discord 內容累積進 memory/）
  recommender.py               根據興趣清單找相關新內容（多來源搜尋彙整，不呼叫 LLM）
  content_generator.py        `ReportContent` 資料結構；GROQ_URL 常數留給 link_processor.py 用
  habit_tracker.py            把追蹤狀態寫回 memory/
  board_writer.py              把當天內容寫進 docs/data/（含歷史紀錄、期數、自動清超過 30 天）
  discord_push.py              把「今天晨報網址」推到 Discord 頻道（取代 ver1 的 LINE 推播）
  sources/                     內容來源：
                                  discord_source.py（今日/長期待辦、收藏連結，calendar + 長期待辦
                                  頻道 + interesting-links 頻道）
                                  hn_source.py（Hacker News，Algolia API，免金鑰）
                                  google_news_source.py（Google 新聞 RSS，免金鑰）
                                  youtube_source.py（YouTube Data API v3，需要 YOUTUBE_API_KEY，
                                  含縮圖 thumbnail）
                                  devpost_source.py（Devpost 黑客松，免金鑰、非官方端點）
                                  eventbrite_source.py（Eventbrite 活動，需要 EVENTBRITE_API_TOKEN，
                                  但 Eventbrite 已停用第三方公開搜尋 API，實際多半查不到結果）
  state/                       機器可讀狀態（habit_state.json、interests_state.json、
                                 issue_counter.json、pending_request.json/draft_content.json 是
                                 兩段接力交接用的暫存檔，處理完就刪）
  link_processor.py            interesting-links 頻道的深度處理：抓連結→逐字稿/文字摘要→回覆到 Discord
                                （這幾次重建都沒有動這支，唯一還在用 Groq 的地方）

docs/                        GitHub Pages 靜態頁面（Broadsheet 報紙風，main 分支 /docs 路徑部署）
  index.html / style.css / broadsheet.css / script.js
                                看板頁面，支援 ?date=YYYY-MM-DD 往回翻歷史；broadsheet.css 是設計
                                系統 token + 共用元件，style.css 是這個頁面專屬版面
  data/latest.json            今天的內容（每次晨報產生後覆寫，網頁沒帶 ?date= 時預設讀這份）
  data/{date}.json            每一天各自一份，超過 30 天自動被清掉
  data/manifest.json          目前還保留著的日期清單（新到舊），給看板頁面畫歷史導覽用

design_handoff_morning_brief/README.md
                              Broadsheet 視覺規格的設計交接文件（保留當歷史紀錄；design/ 底下的
                              設計工具檔案沒有進版控）

.github/workflows/
  morning-report.yml          每日排程（第一段）：蒐集資料、把結果 commit 回 repo
  send-morning-link.yml       docs/data/** 有變動就觸發（第三段）：推 Discord 連結
  interesting-links.yml       每小時排程：處理 interesting-links 頻道新連結，不 commit 回 repo
```

第二段（寫內容）是一個排程的 **Claude Code routine**（不在這個 repo 裡，在
claude.ai/code/routines 上設定），用使用者的 Claude Code 用量寫作，不呼叫任何計費 API。

## 本機測試

複製 `.env.example` 為 `.env` 並填入你的金鑰。主晨報流程分兩段，本機只能測第一段：

```powershell
pip install -r requirements.txt
python -m morning_report.collect_report_request
```

這段是純資料蒐集（讀 Discord、多來源搜尋），沒有金鑰的來源會自動跳過，不會呼叫任何 LLM。
第二段（寫內容）是排程的 Claude Code routine，本機沒辦法跑；要測試「寫內容 + 套用 + 推播」
這段，可以手動寫一份 `morning_report/state/draft_content.json`（欄位對照
`content_generator.py` 的 `ReportContent`），再跑：

```powershell
python -m morning_report.apply_content
```

⚠️ **注意**：`apply_content.py` 最後一步會 `git commit` + `git push origin HEAD:main`
——這是設計給 routine 用的，本機測試時如果不想真的 push 到 main，記得先確認目前的 git
狀態，或只呼叫這支腳本內部的個別函式驗證邏輯，不要整支跑。

⚠️ 另外，只要 `.env` 裡的 `DISCORD_BOT_TOKEN` 是真的有效 token，`send_today_link.py` /
`apply_content.py` 觸發的推播都是真的會送到 Discord 頻道，不是模擬。

執行後可以打開 `docs/index.html`（或用任何本機伺服器，例如 `python -m http.server` 在
`docs/` 資料夾下執行，直接用 `file://` 開會因為 fetch 本機 json 而失敗）看看看板頁面。

## 目前狀態（2026-09-14，第三輪：Broadsheet 視覺改版 + 待辦清單，已 merge 進 main）

- ✅ **視覺全面改版**：套用 `design_handoff_morning_brief/README.md` 的 Broadsheet 規格
  （報紙風、Source Serif 4 + Noto Serif TC 襯線字、青/洋紅特別色）取代原本的發車看板風格。
  `docs/broadsheet.css` 是設計系統本身（直接從設計交接包複製），`docs/style.css` 重寫成這個
  頁面專屬的版面（報頭、問候語、各區塊 eyebrow、推薦卡片手風琴、頁尾導覽都照規格的色彩/
  字級/間距實作）
- ✅ **待辦清單功能，覆蓋設計稿原本的邏輯**：兩個 Discord 頻道——`calendar`（原本是行程來源，
  這輪改成「今日待辦」）、新的長期待辦頻道（環境變數 `DISCORD_LONGTERM_TODO_CHANNEL_ID`，
  頻道 ID 還沒設定，等使用者提供）。完成方式是使用者在 Discord 上把訊息刪掉，程式只抓
  「頻道裡目前還存在的訊息」，**沒有**完成狀態欄位、**沒有** localStorage、**沒有**可點擊互動
  ——比設計稿原本的手風琴式待辦簡化很多，這是使用者明確要求的
- ✅ **JSON schema 擴充**（`content_generator.py` 的 `ReportContent`）：新增 `issue_no`（期數，
  持續累加、不受 30 天歷史清除影響，見 `board_writer.next_issue_no()`）、`greeting_sub`、
  `todos`、`todos_longterm`、`stats`（追蹤中的習慣數、收藏連結數，純數字計算、不是 AI 寫的）；
  `recommendations` 從字串陣列改成物件陣列（`source`/`meta`/`title`/`lede`/`body`/`url`/
  `thumbnail`）；移除 `schedule_summary`（原本的行程概念沒有資料來源了，因為 calendar 頻道
  改feed 待辦）
- ✅ **向後相容**：`docs/script.js` 能同時處理新舊兩種格式——舊格式的 `docs/data/2026-09-*.json`
  （`recommendations` 是字串陣列、沒有 `todos`/`stats`/`issue_no` 等欄位）一樣能正常顯示，
  只是對應區塊改用簡化樣式或直接隱藏，不會壞版面
- ✅ **沒有資料來源的欄位一律不編造**：天氣（`weather`）、還沒回的訊息（`inbox`）、睡眠／
  專注時間這兩個 stats 目前 repo 裡完全沒有來源，前端程式碼都寫好了（欄位存在就會 render），
  但後端目前不會產生這些欄位，對應區塊會直接隱藏，不留假資料或佔位文字
- ✅ 本機測試過 `collect_report_request.py`（真的抓到 Discord 待辦、真的搜到 3 則相關新聞）、
  用 Artifact 預覽驗證過新版面的新舊格式渲染邏輯（人工追蹤程式碼路徑，沒有真的瀏覽器截圖
  ——這個環境沒有可用的 headless browser）
- ✅ **已 merge 回 main**，並同步更新了排程的 Claude Code routine（`trig_01CXDoT2FHTgZyqLu9H8RJQ2`）
  的 prompt，改成寫新版 schema（物件陣列的 `recommendations`、`greeting_sub`，不再碰
  `todos`/`stats`/`issue_no`，那些由 `apply_content.py` 自己算/帶入）
- ✅ **端對端在正式環境測試成功一輪**（2026-09-14）：GitHub Actions 抓到真的 Discord 待辦 →
  routine 寫出真的內容（包含 3 則有 lede/body 的推薦、`issue_no: 1`）→ push 回 main →
  自動推播 Discord 連結，全部真實跑通，看板也顯示正確
- ⏳ **還沒做**：使用者還沒提供長期待辦頻道的 ID（`DISCORD_LONGTERM_TODO_CHANNEL_ID`，設進
  GitHub repo 的 Secrets 後這個功能就會開始運作，之前不影響其他部分）

## 舊狀態記錄（2026-09-13，兩段接力 + Claude Code routine）

主晨報流程整個從「GitHub Actions 直接呼叫 Groq API」改成兩段接力：GitHub Actions 只做資料
蒐集（`collect_report_request.py`），排程的 Claude Code routine 讀 repo 裡的資料自己寫內容
（`draft_content.json`），`apply_content.py` 把兩邊合併、寫看板、commit + push 回 main，
push 上 `docs/data/**` 會觸發 `send-morning-link.yml` 推 Discord 連結。這樣主流程完全不用
Groq，用的是使用者的 Claude Code 訂閱用量，不是計費 API。過程中發現並修好兩個 bug：
`vars.GITHUB_PAGES_URL` 因為 GitHub Actions 不允許變數名稱以 `GITHUB_` 開頭而從來沒真的生效過
（改名 `PAGES_BASE_URL` 並寫死預設值）；routine 的 git checkout 是 detached HEAD，裸的
`git push` 會失敗（改用 `git push origin HEAD:main`）。已經端對端測試成功一輪。

## 更早的狀態記錄（2026-09-13，morning-brief-ver2 分支，第一輪：LINE → Discord）

晨報推播邏輯全面重建：不再把摘要文字塞進推播訊息，改成把內容 render 成看板網頁，
每天只推一個網址連結到 Discord。細節：

- ✅ **移除 LINE 推播**，改用 `discord_push.py` 把「今天的看板網址」推到指定 Discord 頻道
  （頻道 ID 寫死在 `config.py` 的預設值，可用 `DISCORD_MORNING_BRIEF_CHANNEL_ID` 環境變數覆蓋）。
  沿用跟 `discord_source.py`／`link_processor.py` 同一組 bot token，**還沒實際驗證這支 bot
  在這個頻道有沒有 Send Messages 權限**——如果推播失敗，log 會印出檢查清單（bot 是否已加入
  該頻道所在伺服器／有沒有發言權限／token 是否還有效）
- ✅ **看板頁面支援歷史紀錄**：`docs/index.html` 加了上一天／下一天／回到今天／歷史清單下拉選單，
  資料來源是 `docs/data/{date}.json` + `manifest.json`，超過 30 天的日期會在下次晨報產生時
  自動從清單移除、對應 json 也會刪掉，不用手動清
- ✅ **新增 5 個內容來源**，跟原本的 Discord 興趣清單搜尋關鍵字一起查，結果彙整進
  `recommendations`：Hacker News、Google 新聞（皆免金鑰）、YouTube（需要 `YOUTUBE_API_KEY`）、
  Devpost（免金鑰、非官方端點，行為可能隨時改變）、Eventbrite（需要 `EVENTBRITE_API_TOKEN`，
  但 Eventbrite 在 2019 年底已經停用第三方公開活動搜尋 API，這個來源目前多半只會回傳空清單，
  屬於已知限制，不是設定錯誤）
- ✅ 本機測試過完整資料流程（DRY_RUN + Discord token 暫時清空），確認 `docs/data/` 的歷史紀錄
  寫入／30 天自動清除邏輯正確
- ⚠️ 本機測試時一度不小心用真的 bot token 推送了一則測試訊息到正式頻道（`.env` 裡的
  `DISCORD_BOT_TOKEN` 比預期中是有效的），已跟使用者確認過該頻道是私人頻道、不影響任何人，
  之後測試會固定先清空這個變數
- ⏳ **還沒做**：把這個分支合併回 `main`（等使用者確認）；`YOUTUBE_API_KEY` /
  `EVENTBRITE_API_TOKEN` 目前都還沒設定，這兩個來源在雲端排程上會自動跳過，不影響其他功能

## 舊狀態記錄（2026-08-06，ver1）

- ✅ 記憶系統基礎：`memory/profile.md` 已根據使用者提供的真實 Gemini 對話紀錄（5 篇，
  2026-05~07）歸納更新，`memory/habits.md` 已建立，但還沒有任何正在追蹤的自我提升項目
- ✅ 晨報系統框架：內容產生、LINE 推送、看板頁面、每日排程全部跑通
- ✅ 已推上 GitHub（[inso803/ClaudeAssistant](https://github.com/inso803/ClaudeAssistant)），
  GitHub Pages 已啟用並自動部署
- ✅ 內容產生改用 Groq API（Gemini 免費額度一直回傳 0，疑似跟 Google 端系統故障有關，改用不同
  供應商），`GROQ_API_KEY` 已設定並確認成功生成內容
- ✅ Groq API 呼叫失敗時會自動退回保底內容，不會讓整個晨報當機
- ✅ LINE 推播已跑通（`LINE_USER_ID`、`LINE_CHANNEL_ACCESS_TOKEN` 都已設定為 GitHub Secrets，
  Actions 手動觸發過一次，推播成功送達）
- ✅ Discord 來源已接上：使用者建立了自己的 Discord 伺服器，兩個頻道——`calendar`（手動記行程，
  當天貼的訊息會當成今日行程）、`interesting-links`（收藏連結）。`discord_source.py` 直接打
  Discord REST API 讀最近訊息，不需要常駐 Bot 程式。本機已用真實 Bot Token 測試過連線成功
- ✅ 興趣收藏會累積進 `memory/`：`interesting-links` 頻道的內容不再是當天用完就丟，
  `interests.py` 會併入 `memory/interests.md` + `morning_report/state/interests_state.json`
  長期保存（自動去重複），推薦引擎讀的是累積後的完整清單，不只是當天新增的
- ✅ 推薦引擎（`recommender.py`）：用 Groq 把興趣清單濃縮成搜尋關鍵字，打 Brave Search API
  查真的網路內容，結果交給 Groq 整理成 `recommendations`，看板跟 LINE 訊息都會顯示。
  還沒設定 `BRAVE_SEARCH_API_KEY`，目前這部分會自動跳過（不影響其他功能）
- ⏳ 目前晨報內容仍偏空泛：因為沒有正在追蹤的自我提升項目、Discord 頻道也還沒有訊息，Groq 沒
  有素材可以發揮。下一步是使用者開始在 Discord 貼行程/連結，或先手動加一項自我提升追蹤
- ✅ 新增 `link_processor.py` + `interesting-links.yml`：每小時讀 interesting-links 頻道新訊息，
  用 yt-dlp 嘗試抓影片音軌、呼叫 Groq 的 Whisper API 轉逐字稿（IG/Threads 常因登入牆失敗，
  這時退回抓貼文的 og:description 文字），再用 Groq 摘要並列出書名/工具/skill 等重點，
  回覆在原訊息底下並加上 ✅ reaction 標記已處理（拿掉 ✅ 就會在下次排程重新處理一次）。
  不影響 discord_source.py／晨報主流程，兩邊各自獨立讀取同一個頻道。還沒實際跑過，
  bot 目前只有讀取權限，需要確認/補上 Send Messages 與 Add Reactions 權限才能正常回覆

## 未來構想（先記錄，還沒要做）

- **自然語言記行程自動解析**：現在 `calendar` 頻道是「使用者自己打字、原封不動當成一行行程」，
  還沒有自動解析日期/時間欄位。使用者桌面上已經有一個 `smart-line-calendar` 專案
  （FastAPI + LINE Messaging API + Gemini API + SQLite）雛型，之後可能可以延伸這個做更精準的
  自然語言解析，取代現在單純轉述訊息內容的做法，但屬於獨立專案，整合方式還沒定案

## 需要你做的事

1. **提供長期待辦 Discord 頻道的 ID**，設進 repo Secrets：`DISCORD_LONGTERM_TODO_CHANNEL_ID`
   （開發者模式下對頻道按右鍵「複製頻道 ID」）。沒設定的話這個功能會自動跳過，不影響其他部分。

2. **（可選）申請 Brave Search API key**：到 [brave.com/search/api](https://brave.com/search/api/)
   註冊、選 Free tier（每月 2000 次查詢免費），設進 repo Secrets：`BRAVE_SEARCH_API_KEY`

3. **（可選）申請 YouTube Data API key**：Google Cloud Console 建專案 → 啟用
   「YouTube Data API v3」→ 建立 API 金鑰，設進 repo Secrets：`YOUTUBE_API_KEY`

4. **（可選，效果可能有限）申請 Eventbrite Personal OAuth Token**：Eventbrite 已經停用第三方
   公開活動搜尋，申請了也可能一直查不到結果，優先度最低。設進 repo Secrets：
   `EVENTBRITE_API_TOKEN`

5. 繼續在 Discord 的 `calendar`（今日待辦）／長期待辦／`interesting-links` 頻道貼東西，
   晨報才有真的素材可以講；`calendar` 頻道現在放的是待辦事項，不是行程了。
