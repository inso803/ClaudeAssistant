# Handoff：每日晨報看板（Morning Brief）

給 Claude Code 的實作交接包。目標 repo：`inso803/ClaudeAssistant`（branch `main`），要改的是 `docs/` 這個 GitHub Pages 看板頁。

## 這個包是什麼

`design/` 裡的檔案是 **設計稿**，用 HTML 畫出來的視覺／互動參考，**不是可以直接上線的程式碼**。
任務是：把這份設計在 `docs/`（原生 HTML + CSS + JS，無框架、無 build step）裡重做一次，
沿用該 repo 既有的架構（`index.html` / `style.css` / `script.js` 讀 `data/*.json`）。
不要把 `.dc.html` 直接丟進 repo——它依賴設計工具的 runtime（`support.js`）。

**保真度：高保真（hi-fi）。** 顏色、字級、間距、互動都已經是最終值，請照著做。

## 設計來源

視覺系統是 **Broadsheet**：報紙風、紙白底 #f3f2f2、近黑 #201e1d、Source Serif 4 襯線字，
青 #0088b0 與洋紅 #d6006c 當印刷特別色小面積使用，另有印刷黃 #edbb00 只用於印刷裝飾。
原則：**不用框線和卡片切版，靠留白和字級做層級**。`design/broadsheet.css` 就是這套系統的
token + component 樣式表，可以整份放進 `docs/`（例如 `docs/broadsheet.css`），
用它的 CSS 變數而不是自己寫 hex。

字型（Google Fonts，中文要另外補中文襯線）：

```html
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&family=Noto+Serif+TC:wght@400;600;700&display=swap" rel="stylesheet">
```
字堆疊一律：`"Source Serif 4","Noto Serif TC",Georgia,serif`（**不要**引入無襯線體）。

## 版面（單欄直式捲動）

外層容器：`max-width:680px; margin:0 auto; padding:40px 24px 60px`，背景 #f3f2f2。
由上到下依序：

| # | 區塊 | 內容來源（JSON 欄位） |
| --- | --- | --- |
| 1 | 報頭 Masthead | 靜態 + `date` |
| 2 | 問候語 | `greeting` |
| 3 | 今日行程 SCHEDULE | `schedule`（新欄位，見下） |
| 4 | 今天想完成 TO DO | `todos`（新欄位） |
| 5 | 還沒回的訊息 UNANSWERED | `inbox`（新欄位） |
| 6 | 今天值得看的 READING | `recommendations`（需擴充成物件） |
| 7 | 昨天的你 YESTERDAY | `stats` + `habit_highlights` |
| 8 | 今天的一句話 | `closing_note` |
| 9 | 頁尾導覽 | `manifest.json` + `?date=` |

各區塊之間距離 `margin-top:50px`，**沒有分隔線**（唯二的線在報頭和第 8 區上緣）。

### 1. 報頭

- 最上方四色色條：四個 `34×9px` 方塊，間距 4px，依序 #0088b0 / #d6006c / #edbb00 / #201e1d
- 刊頭列：左「晨　報」`700 40px/1`、字距 `.14em`；右「MORNING BRIEF」`400 13px`、字距 `.2em`、色 #006786
- 刊頭下 `border-bottom:6px solid #201e1d`，間隔 3px 後再一條 `1px solid #201e1d`（thick-thin 對）
- 日期列（1px 線下方，padding-top 8px）三段左中右分散：日期 · 天氣（前面一個 9px 黃色圓點 #edbb00）· 期數；`400 14px/1.4`，色 #444141，期數色 #605d5d

### 2. 問候語

`400 27px/1.6`，`text-wrap:pretty`，margin-top 40px。下方補一行 **italic** `400 17px/1.7`、色 #444141 的說明句。

### 3–7 區塊標題（eyebrow）統一規格

`display:flex; align-items:center; gap:9px`，前置一個 `11×11px` 色塊，文字 `600 12px/1`、字距 `.26em`。
配色（刻意交替）：

| 區塊 | 色塊 | 文字色 |
| --- | --- | --- |
| 今日行程 SCHEDULE | #0088b0 | #006786 |
| 今天想完成 TO DO | #d6006c | #aa0b56 |
| 還沒回的訊息 UNANSWERED | #0088b0 | #006786 |
| 今天值得看的 READING | #d6006c | #aa0b56 |
| 昨天的你 YESTERDAY | #edbb00 | #006786 |
| 今天的一句話 | #d6006c | #aa0b56 |

### 3. 今日行程

每筆：`grid-template-columns:76px 1fr; gap:20px; margin-top:20px; align-items:baseline`
- 時間 `600 17px/1.4`；一般色 #605d5d，**當天重點那筆** 用 accent #006786
- 標題 `600 19px/1.45`；備註 `400 15px/1.6` 色 #605d5d
- 區塊末尾一行 italic `400 15px/1.7` 色 #605d5d 的資料來源說明

### 4. 待辦

標題列右側顯示「N / M 完成」`400 14px` 色 #605d5d。
每筆：`display:flex; gap:14px; align-items:baseline; margin-top:16px; cursor:pointer`
- 未完成：符號 `□`（`400 17px`，色 #006786）＋文字 `400 18px/1.6` 色 #201e1d
- 已完成：符號 `✕`（色 #9b9797）＋文字 `line-through`、色 #9b9797
- 點整列切換狀態（設計稿是 local state；實作上若要持久化，建議存 `localStorage`，key 帶當天日期）

### 5. 還沒回的訊息

每筆 margin-top 18px：第一行 寄件者 `600 17px/1.5` ＋ 時間 `400 14px/1.5` 色 #605d5d（flex, gap 12px）；
第二行內容 `400 16px/1.65` 色 #444141。

### 6. 今天值得看的（含縮圖）

每筆：`display:grid; grid-template-columns:minmax(0,1fr) 156px; gap:22px; align-items:start; margin-top:30px`
- 左欄：
  - 來源標籤用 Broadsheet 的 `.tag.tag-accent`（底 #cbeeff／字 #004961，`font-size:11px`，padding `3px 10px`），字距 `.14em`，字型同樣是襯線
  - 旁邊 meta `400 14px/1` 色 #605d5d（例如「討論熱度高 · 6 分鐘」）
  - 標題 `600 22px/1.45`，margin-top 10px
  - 導言 `400 17px/1.75` 色 #444141
  - 展開後的全文段落同規格，margin-top 12px
  - 展開按鈕：文字按鈕，`400 15px/1`、色 #006786、無底無框、padding `10px 0 0`；文案「讀完整摘要 ↓」／「收起 ↑」
- 右欄縮圖：`156×117px`，`border-radius:2px`，底色 #cbeeff，套 Broadsheet 的 `.halftone`（網點濾鏡，已在 broadsheet.css 裡）。
  實作時放 `<img>`（`object-fit:cover`），沒有圖時就留 #cbeeff 底色 + 置中「縮圖」字樣。
- 互動：一次只展開一則（手風琴），預設展開第一則

### 7. 昨天的你

數字列：`display:flex; flex-wrap:wrap; gap:36px; margin-top:22px`
- 數值 `600 34px/1`，顏色分別是：睡眠 #aa0b56（異常值用洋紅）、專注 #006786、收藏 #006786、習慣 #201e1d
- 標籤 `400 14px/1.5` 色 #605d5d，margin-top 6px
下方一段 `400 17px/1.75` 色 #444141 的提醒文字（對應 `habit_highlights`）

### 8. 今天的一句話

`margin-top:56px; border-top:1px solid #201e1d; padding:24px 20px`，左右各外推 -20px 做出滿版淡底，
底色 #fff1f4（accent-2-100）。引言 **italic** `400 24px/1.6`，margin-top 16px。

### 9. 頁尾導覽

flex 兩端對齊：左邊「← 前一天 · 回到今天 · 後一天 →」三個文字按鈕（`400 15px/1`，可用時 #006786，
不可用時 #605d5d、`cursor:default`），分隔點 #bab6b6；右邊資料來源說明 `400 13px/1.5` 色 #605d5d。
行為沿用現有 `docs/script.js` 的 `setRequestedDate()` / `manifest.json` 邏輯，不要重寫。

## 互動與狀態

| 互動 | 行為 |
| --- | --- |
| 點推薦項目的「讀完整摘要 ↓」 | 展開 `body` 段落，其他已展開的收合（單開手風琴）；按鈕文案切換成「收起 ↑」 |
| 點待辦整列 | 切換完成狀態（符號、顏色、刪除線、計數同步） |
| 頁尾導覽 | `?date=YYYY-MM-DD` 換頁，沿用既有實作 |
| 焦點樣式 | 用 Broadsheet 內建 `:focus-visible`（2px #0088b0 外框），不要留瀏覽器預設藍框 |

沒有轉場動畫需求；展開可加 150ms 的高度或透明度過場，但不是必要。

## 建議的 JSON schema 擴充

目前 `docs/data/latest.json` 只有 `greeting / schedule_summary / habit_highlights / links_highlight /
recommendations(string[]) / closing_note / ticker_message`，不足以餵這個版面。建議擴成：

```json
{
  "date": "2026-09-14",
  "weather": { "city": "台北", "summary": "陰轉晴", "low": 24, "high": 31, "rain_pct": 20 },
  "issue_no": 185,
  "greeting": "早安彥碩，今天只有一場會議，下午才會放晴。",
  "greeting_sub": "昨天睡不到七小時，所以今天的清單我只留了三件事。",
  "schedule": [
    { "time": "10:20", "title": "演算法 期中複習課", "meta": "資工系館 104 · 兩小時", "highlight": false }
  ],
  "todos": [ { "id": "d1", "label": "把 RPG 關卡劇本第二版寄給總召" } ],
  "inbox": [ { "from": "宿營總召 · Discord", "when": "昨天 22:14", "text": "關卡人力表還缺兩個人" } ],
  "recommendations": [
    { "id": "r1", "source": "HACKER NEWS", "meta": "討論熱度高 · 6 分鐘",
      "title": "...", "lede": "...", "body": "...", "url": "https://...", "thumbnail": "https://..." }
  ],
  "stats": [ { "value": "6h20m", "label": "睡眠 · 連續四天不足", "tone": "alert" } ],
  "habit_highlights": ["你還沒有在追蹤的自我提升項目。"],
  "closing_note": "...",
  "ticker_message": "..."
}
```

`tone` 建議只有 `alert`(#aa0b56) / `accent`(#006786) / `plain`(#201e1d) 三種，前端做對應。

**向後相容很重要**：`board_writer.py` 寫出的舊格式檔案（`docs/data/2026-09-*.json`）仍在，
前端要能容錯——欄位缺少時整區不 render，`recommendations` 若是 `string[]` 就退回只顯示標題、不顯示縮圖。

需要一起改的 Python 端：
- `morning_report/content_generator.py`：Groq prompt 要改成輸出上面的結構（含 `greeting_sub`、每則推薦的 `lede`/`body` 兩段）
- `morning_report/board_writer.py`：寫檔的 schema
- `morning_report/sources/*.py`：各來源補 `thumbnail`（YouTube 有 `snippet.thumbnails`；HN / Google News 沒有縮圖，可退回來源色底）
- 天氣、睡眠／專注數據目前 **repo 裡沒有任何來源**，需要新來源或先寫死／省略

## Design tokens（全部取自 broadsheet.css）

顏色：`--color-bg` #f3f2f2 · `--color-text` #201e1d · `--color-accent` #0088b0 ·
`--color-accent-2` #d6006c · `--color-process-yellow` #edbb00 ·
中性 #444141 / #605d5d / #9b9797 / #bab6b6 / #cbeeff(accent-200) / #fff1f4(accent-2-100) /
#006786(accent-700) / #aa0b56(accent-2-700) / #004961(accent-800)

內文用的青／洋紅一律取 700 階（#006786 / #aa0b56），**不要**直接用 base 色當內文色（對比不足）。

間距：5 / 10 / 15 / 20 / 30 / 40px（`--space-1..8`）；區塊間距 50px；圓角 `--radius-md` 2px。

字級：40 / 34 / 27 / 24 / 22 / 19 / 18 / 17 / 16 / 15 / 14 / 13 / 12px，行高見各區塊。

## Assets

- 推薦縮圖：設計稿裡是可拖放的佔位框（`image-slot.js`），實作時換成真實 `thumbnail` URL
- 無圖示／icon（這套系統的 chrome 就是襯線字本身；若真的需要 icon 用 Phosphor duotone）

## 檔案

- `design/每日晨報.dc.html` — 設計稿本體（在瀏覽器直接開可看，需同目錄的 `support.js`）
- `design/broadsheet.css` — 設計系統樣式表，可整份帶進 `docs/`（注意設計稿裡 `<link>` 指向 `_ds/...`，搬過去要改成相對路徑）
- `design/support.js` — 設計工具 runtime，**不要**進 repo
- `design/image-slot.js` — 拖放縮圖佔位元件，**不要**進 repo
