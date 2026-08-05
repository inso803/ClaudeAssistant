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
  sources/                     行程資料來源（目前只有 Discord 的 stub，尚未實作）
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
- ⏳ 目前晨報內容偏空泛：因為沒有正在追蹤的自我提升項目、也沒有任何行程來源，Groq 沒有素材可以
  發揮。下一步是先手動加一項自我提升追蹤，並決定行程來源怎麼接（見下方「未來構想」）
- ⏳ Discord 串接：`morning_report/sources/discord_source.py` 目前是空的 stub，尚未實作

## 未來構想（先記錄，還沒要做）

2026-08-06 聊天中使用者提出的兩個晨報內容方向，先記下來，之後要做再回來討論設計：

1. **自然語言記行程**：类似 LINE Bot 那樣輸入「8/1 14:00-15:00 開會」就能自動解析存起來，
   讓晨報的「今日行程」有真的資料可以講，不用等 Discord 串接完成。使用者桌面上已經有一個
   `smart-line-calendar` 專案（FastAPI + LINE Messaging API + Gemini API + SQLite）雛型，
   可能可以延伸這個而不是重寫，但屬於獨立專案，跟本專案的整合方式還沒定案。
2. **AI 工具趨勢內容**：晨報加入類似使用者關注的 AI 工具相關 YouTube 頻道那種調性的內容——
   AI 工具的最新 tips、趨勢整理。注意：無法直接讀取使用者的 YouTube 訂閱清單，需要使用者
   明確告知關注的方向/頻道風格，才能設計對應的內容產生邏輯。

## 需要你做的事

目前沒有阻塞性的待辦——`morning_report/habits.md` 裡加一個自我提升追蹤項目、決定「未來構想」
要不要做，是唯二會讓晨報內容變豐富的路徑，兩者都可以晚點再決定。
