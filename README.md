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
  content_generator.py        呼叫 Claude API 產生晨報內容
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

不需要任何 API key 也可以測試整個資料流程（會自動進入 DRY_RUN，不呼叫 Claude API、不推播 LINE）：

```powershell
python -m morning_report.generate_report
```

執行後可以打開 `docs/index.html`（或用任何本機伺服器，例如 `python -m http.server` 在
`docs/` 資料夾下執行，直接用 `file://` 開會因為 fetch 本機 json 而失敗）看看看板頁面。

## 目前狀態

- ✅ 記憶系統基礎：`memory/profile.md`、`memory/habits.md` 已建立，**但 profile.md 目前是用
  CLAUDE.md 既有背景描述手動建立的初始版本，還沒有匯入真實 Gemini 對話紀錄**（見下方「需要你
  做的事」）
- ✅ 晨報系統框架：內容產生、LINE 推送、看板頁面、每日排程全部跑通（本機以 DRY_RUN 驗證過）
- ⏳ Discord 串接：`morning_report/sources/discord_source.py` 目前是空的 stub，等你之後確認要
  怎麼做（自架 Bot？或是別的方式讀取 Discord 訊息？）再實作
- ⏳ 尚未推上 GitHub、尚未設定任何 secrets，所以排程還不會真的執行

## 需要你做的事

1. **重新匯出 Gemini 對話紀錄**：目前的 `Gemini.zip` 裡沒有實際對話內容（只有兩個空的
   metadata 檔案），需要你到 [Google Takeout](https://takeout.google.com/) 重新匯出，記得勾選
   包含對話內容的 Gemini Apps 項目。詳細步驟見 [memory/README.md](memory/README.md)。

2. **建立 GitHub repo 並推上去**：這台環境沒有安裝 `gh` CLI，我沒辦法幫你建立遠端 repo，需要你
   自己在 GitHub 上建一個新 repo，把這個資料夾 push 上去，再到 repo 的 Settings → Pages 選擇
   「Deploy from branch」、分支選 `main`、資料夾選 `/docs`。

3. **申請 LINE Messaging API channel**：到
   [LINE Developers Console](https://developers.line.biz/console/) 建立 Provider 與 Channel
   （Messaging API 類型），取得 `Channel Access Token`；並且要拿到你自己的 LINE User ID
   （把這個官方帳號加為好友後，可以用 LINE 的 webhook 或第三方工具取得）。

4. **申請 Anthropic API Key**：到 [console.anthropic.com](https://console.anthropic.com/) 取得
   API key，供晨報內容產生使用（沒有這把 key 時系統會用 DRY_RUN 假資料，不會出錯，但內容不是
   真的由 Claude 生成）。

5. **把上面拿到的三個值設成 GitHub repo 的 Secrets**（Settings → Secrets and variables →
   Actions）：
   - `ANTHROPIC_API_KEY`
   - `LINE_CHANNEL_ACCESS_TOKEN`
   - `LINE_USER_ID`

   設定完成後，`.github/workflows/morning-report.yml` 會在每天 22:30 UTC（台北時間 06:30）自動
   跑，你也可以到 Actions 分頁手動點 "Run workflow" 立即測試。

以上都完成後跟我說一聲，我可以幫你檢查 Actions 執行結果、調整內容風格，或是開始規劃 Discord
串接。
