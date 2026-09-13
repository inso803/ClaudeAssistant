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

morning_report/              晨報系統
  generate_report.py          主入口：組內容 -> 寫看板資料（含歷史）-> 推 Discord 連結 -> 更新記憶
  memory_reader.py            讀取 memory/ 的內容
  interests.py                 興趣收藏清單持久化（Discord 內容累積進 memory/）
  recommender.py               根據興趣清單找相關新內容（Groq 出關鍵字 + 多來源搜尋彙整）
  content_generator.py        呼叫 Groq API 產生晨報內容
  habit_tracker.py            把追蹤狀態寫回 memory/
  board_writer.py              把當天內容寫進 docs/data/（含歷史紀錄、自動清超過 30 天的舊資料）
  discord_push.py              把「今天晨報網址」推到 Discord 頻道（取代 ver1 的 LINE 推播）
  sources/                     內容來源：
                                  discord_source.py（行程／收藏連結，calendar + interesting-links 頻道）
                                  hn_source.py（Hacker News，Algolia API，免金鑰）
                                  google_news_source.py（Google 新聞 RSS，免金鑰）
                                  youtube_source.py（YouTube Data API v3，需要 YOUTUBE_API_KEY）
                                  devpost_source.py（Devpost 黑客松，免金鑰、非官方端點）
                                  eventbrite_source.py（Eventbrite 活動，需要 EVENTBRITE_API_TOKEN，
                                  但 Eventbrite 已停用第三方公開搜尋 API，實際多半查不到結果）
  state/                       機器可讀狀態（habit_state.json、interests_state.json）
  link_processor.py            interesting-links 頻道的深度處理：抓連結→逐字稿/文字摘要→回覆到 Discord
                                （這次 ver2 重建沒有動這支）

docs/                        GitHub Pages 靜態頁面（發車看板風格，main 分支 /docs 路徑部署）
  index.html / style.css / script.js   看板頁面，支援 ?date=YYYY-MM-DD 往回翻歷史
  data/latest.json            今天的內容（每次晨報產生後覆寫，網頁沒帶 ?date= 時預設讀這份）
  data/{date}.json            每一天各自一份，超過 30 天自動被清掉
  data/manifest.json          目前還保留著的日期清單（新到舊），給看板頁面畫歷史導覽用

.github/workflows/
  morning-report.yml          每日排程：產生內容、推 Discord 連結、把結果 commit 回 repo
  interesting-links.yml       每小時排程：處理 interesting-links 頻道新連結，不 commit 回 repo
```

## 本機測試

複製 `.env.example` 為 `.env` 並填入你的金鑰，就會用真實 API；沒有 `.env` / 沒設
`GROQ_API_KEY` 也可以測試整個資料流程（自動進入 DRY_RUN，不呼叫 Groq API）。

⚠️ 注意：DRY_RUN 只跳過 Groq／推薦搜尋，**不會**跳過 Discord 推播——只要 `.env` 裡的
`DISCORD_BOT_TOKEN` 是真的有效 token，本機測試一樣會真的推訊息到 Discord 頻道。純本機測試
資料流程時，記得暫時清空或覆寫這個變數，例如：

```powershell
pip install -r requirements.txt
$env:DISCORD_BOT_TOKEN=""; python -m morning_report.generate_report
```

執行後可以打開 `docs/index.html`（或用任何本機伺服器，例如 `python -m http.server` 在
`docs/` 資料夾下執行，直接用 `file://` 開會因為 fetch 本機 json 而失敗）看看看板頁面。

## 目前狀態（2026-09-13，morning-brief-ver2 分支）

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

1. **把 Discord 三個值設進 GitHub repo 的 Secrets**（Settings → Secrets and variables →
   Actions → New repository secret），不然雲端排程還是讀不到 Discord 內容：
   - `DISCORD_BOT_TOKEN`
   - `DISCORD_CALENDAR_CHANNEL_ID`
   - `DISCORD_INTERESTING_LINKS_CHANNEL_ID`

2. **確認 bot 在新的晨報推播頻道（ID `1547445470555807794`）有沒有權限**：這支 bot 目前是
   用來讀取 calendar/interesting-links 頻道、回覆 interesting-links 頻道，沒驗證過它在這個
   新頻道有沒有 Send Messages 權限。如果之後排程跑起來 Discord 沒收到訊息，先檢查這裡。

3. **申請 Brave Search API key**（要不要做推薦功能都可以，沒設定就自動跳過）：到
   [brave.com/search/api](https://brave.com/search/api/) 註冊、選 Free tier（每月 2000 次查詢
   免費），拿到 key 後設進 repo Secrets：`BRAVE_SEARCH_API_KEY`

4. **（可選）申請 YouTube Data API key**：Google Cloud Console 建專案 → 啟用
   「YouTube Data API v3」→ 建立 API 金鑰，設進 repo Secrets：`YOUTUBE_API_KEY`

5. **（可選，效果可能有限）申請 Eventbrite Personal OAuth Token**：Eventbrite 帳號的
   API keys 頁面可以拿到，設進 repo Secrets：`EVENTBRITE_API_TOKEN`。但如前面所說，Eventbrite
   已經停用第三方公開活動搜尋，申請了也可能一直查不到結果，優先度最低。

6. 開始在 Discord 的 `calendar` / `interesting-links` 頻道貼東西，晨報才有真的素材可以講。
