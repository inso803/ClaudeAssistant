# 記憶系統

長期記憶系統，供晨報系統與未來的對話讀取使用者背景。原始對話全文與其他敏感個資不會被保存或
提交進版控，只保留摘要層級的理解。

## 檔案結構

| 路徑 | 用途 | 是否進版控 |
|---|---|---|
| `profile.md` | 使用者核心背景摘要（會持續演化） | 是 |
| `habits.md` | 自我提升進度追蹤，晨報系統讀取／更新 | 是 |
| `interests.md` | 興趣收藏清單（從 Discord 累積），推薦引擎讀取／更新 | 是 |
| `raw/` | 原始匯出檔（Gemini 對話紀錄，各種格式） | **否，已加入 .gitignore** |
| `raw/extracted/` | 從原始匯出檔解析出的純文字中繼結果 | **否，已加入 .gitignore** |
| `import_gemini_takeout.py` | 把 `raw/` 裡的匯出檔解析成純文字 | 是（程式本身） |

## 目前狀態（2026-08-05）

`profile.md` 已根據使用者提供的真實 Gemini 對話紀錄（5 篇，來自「Gemini in Workspace」的
Conversation History 匯出，2026-05~07）歸納更新。原始對話存放在
`memory/raw/gemini_conversations/`（已排除版控）。樣本量還小，之後有更多對話紀錄時應該重新
執行下面的流程、擴充 `profile.md`。

第一次嘗試用 Google Takeout 匯出時（`Gemini.zip`）拿到的是空的 metadata 檔案，沒有實際對話
內容，後來改用「Gemini in Workspace」介面直接匯出的 Conversation History 資料夾才拿到真正的
對話紀錄。`import_gemini_takeout.py` 目前同時支援這兩種格式。

## 如何補上更多 Gemini 對話紀錄

1. 取得對話匯出檔，以下兩種格式都可以：
   - Google Takeout（[takeout.google.com](https://takeout.google.com/)）匯出的 zip，記得勾選
     「Gemini Apps」對話紀錄項目，不是只有「gems」「scheduled actions」等設定類資料
   - 「Gemini in Workspace」的 Conversation History 資料夾，裡面每篇對話是一個
     `conversation_<id>.txt`（內容其實是 JSON）
2. 放進 `memory/raw/`（此資料夾已被 .gitignore 排除，不會被提交）
3. 執行：

   ```powershell
   python memory/import_gemini_takeout.py
   ```

   會把內容解析成純文字，輸出到 `memory/raw/extracted/`（同樣不進版控）。
4. 回到 Claude Code，請它讀取 `memory/raw/extracted/` 的內容，歸納重點後更新 `profile.md`。
   （這一步刻意保留由 Claude 人工歸納，而不是全自動寫入，避免把原始對話片段、或對話中出現的
   第三方個資〔例如同學姓名、學號〕直接複製進長期保存的摘要檔案。）

## 設計原則

- **只保留摘要，不保留原文**：`profile.md`／`habits.md` 只放歸納後的理解，原始資料只暫留在
  被排除版控的 `raw/`，供歸納時參考，之後可自行刪除。
- **持續演化**：這兩份檔案預期會隨著使用者在 Claude 上的互動、以及晨報系統的每日回饋不斷更新，
  不是寫一次就不動的靜態文件。
