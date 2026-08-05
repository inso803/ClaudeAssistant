# 記憶系統

長期記憶系統，供晨報系統與未來的對話讀取使用者背景。原始對話全文與其他敏感個資不會被保存或
提交進版控，只保留摘要層級的理解。

## 檔案結構

| 路徑 | 用途 | 是否進版控 |
|---|---|---|
| `profile.md` | 使用者核心背景摘要（會持續演化） | 是 |
| `habits.md` | 自我提升進度追蹤，晨報系統讀取／更新 | 是 |
| `raw/` | 原始匯出檔（例如 Google Takeout 的 Gemini 對話紀錄 zip） | **否，已加入 .gitignore** |
| `raw/extracted/` | 從原始匯出檔解析出的純文字中繼結果 | **否，已加入 .gitignore** |
| `import_gemini_takeout.py` | 把 `raw/` 裡的 Takeout 匯出檔解壓、解析成純文字 | 是（程式本身） |

## 如何補上真實的 Gemini 對話紀錄

目前 `profile.md` 是用 CLAUDE.md 裡既有的背景描述手動建立的初始版本，**還沒有真正匯入過
Gemini 對話紀錄**，因為第一次提供的 `Gemini.zip` 裡只有兩個空的 metadata 檔案
（`gemini_scheduled_actions_data.html`、`gemini_gems_data.html`），沒有實際對話內容。

要補上真實資料，請：

1. 前往 [Google Takeout](https://takeout.google.com/)
2. 取消全選，只勾選「**Gemini Apps**」（或介面上等效的 Gemini 對話紀錄項目），確認勾選的是
   包含對話內容的項目，不是只有「gems」「scheduled actions」等設定類資料
3. 匯出、下載 zip
4. 把 zip 放進 `memory/raw/`（此資料夾已被 .gitignore 排除，不會被提交）
5. 執行：

   ```powershell
   python memory/import_gemini_takeout.py
   ```

   這會把 zip 解壓、把每篇對話解析成純文字，輸出到 `memory/raw/extracted/`（同樣不進版控）。
6. 回到 Claude Code，請它讀取 `memory/raw/extracted/` 的內容，歸納重點後更新 `profile.md`。
   （這一步刻意保留由 Claude 人工歸納，而不是全自動寫入，避免把原始對話片段直接複製進
   長期保存的摘要檔案。）

## 設計原則

- **只保留摘要，不保留原文**：`profile.md`／`habits.md` 只放歸納後的理解，原始資料只暫留在
  被排除版控的 `raw/`，供歸納時參考，之後可自行刪除。
- **持續演化**：這兩份檔案預期會隨著使用者在 Claude 上的互動、以及晨報系統的每日回饋不斷更新，
  不是寫一次就不動的靜態文件。
