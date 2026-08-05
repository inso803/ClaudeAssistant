# 個人 AI 助手

邱彥碩的個人 AI 助手專案：長期記憶系統 + 晨報自動化系統。詳細專案背景與執行原則見
[CLAUDE.md](CLAUDE.md)。

## 專案結構

```
memory/                     長期記憶（見 memory/README.md）
  profile.md                 使用者核心背景摘要
  habits.md                  自我提升進度追蹤（人類可讀版）
  feedback.md                使用者對晨報的回饋紀錄
  import_gemini_takeout.py   把 Google Takeout 匯出檔解析成純文字
  raw/                        原始匯出檔（.gitignore 排除）

morning_report/              晨報系統
  generate_report.py          主入口：組內容 -> 寫看板資料 -> 推 LINE -> 更新記憶
  memory_reader.py            讀取 memory/ 的內容
  content_generator.py        呼叫 Groq API 產生晨報內容
  habit_tracker.py            把追蹤狀態寫回 memory/
  line_sender.py               LINE Push Message
  sources/                     行程／收藏連結來源（Discord：calendar + interesting-links 頻道）
  state/habit_state.json       自我提升追蹤的機器可讀狀態

docs/                        GitHub Pages 靜態頁面（發車看板風格）
  index.html / style.css / script.js
  data/latest.json            每次晨報產生後覆寫

.github/workflows/
  morning-report.yml          每日排程：產生內容、推播 LINE、把結果 commit 回 repo
```

## 本機測試

複製 `.env.example` 為 `.env` 並填入你的金鑰，就會用真實 API；沒有 `.env` / 沒設
`GROQ_API_KEY` 也可以測試整個資料流程（自動進入 DRY_RUN，不呼叫 Groq API、不推播 LINE）：

```powershell
pip install -r requirements.txt
python -m morning_report.generate_report
```

執行後可以打開 `docs/index.html`（或用任何本機伺服器，例如 `python -m http.server` 在
`docs/` 資料夾下執行，直接用 `file://` 開會因為 fetch 本機 json 而失敗）看看看板頁面。

## 目前狀態（2026-08-06）

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
  當天貼的訊息會當成今日行程）、`interesting-links`（收藏連結，晨報會提醒還有幾則沒看）。
  `discord_source.py` 直接打 Discord REST API 讀最近訊息，不需要常駐 Bot 程式。本機已用真實
  Bot Token 測試過連線成功（兩個頻道目前都還沒有訊息，待使用者開始貼）
- ⏳ 目前晨報內容仍偏空泛：因為沒有正在追蹤的自我提升項目、Discord 頻道也還沒有訊息，Groq 沒
  有素材可以發揮。下一步是使用者開始在 Discord 貼行程/連結，或先手動加一項自我提升追蹤

## 未來構想（先記錄，還沒要做）

2026-08-06 聊天中使用者提出的方向，先記下來，之後要做再回來討論設計：

- **自然語言記行程自動解析**：現在 `calendar` 頻道是「使用者自己打字、原封不動當成一行行程」，
  還沒有自動解析日期/時間欄位。使用者桌面上已經有一個 `smart-line-calendar` 專案
  （FastAPI + LINE Messaging API + Gemini API + SQLite）雛型，之後可能可以延伸這個做更精準的
  自然語言解析，取代現在單純轉述訊息內容的做法，但屬於獨立專案，整合方式還沒定案
- **AI 工具趨勢內容**：`interesting-links` 頻道目前只會原樣提醒使用者收藏了什麼連結，還沒有
  真的做「AI 工具最新 tips／趨勢」這種主動整理。無法直接讀取使用者的 YouTube 訂閱清單，需要
  使用者明確告知關注的方向/頻道風格，才能設計對應的內容產生邏輯

## 需要你做的事

1. **把 Discord 三個值設進 GitHub repo 的 Secrets**（Settings → Secrets and variables →
   Actions → New repository secret），不然雲端排程還是讀不到 Discord 內容：
   - `DISCORD_BOT_TOKEN`
   - `DISCORD_CALENDAR_CHANNEL_ID`
   - `DISCORD_INTERESTING_LINKS_CHANNEL_ID`

2. 開始在 Discord 的 `calendar` / `interesting-links` 頻道貼東西，晨報才有真的素材可以講。
