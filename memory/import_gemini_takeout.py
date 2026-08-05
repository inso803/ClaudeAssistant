"""
把 memory/raw/ 底下的 Gemini 對話匯出檔解析成純文字，輸出到 memory/raw/extracted/
供後續人工／Claude 歸納進 profile.md。

支援兩種格式（實際遇過的匯出都長這樣，之後如果格式又不同，需要人工檢查調整）：
1. Google Takeout 的 zip，裡面是 HTML 檔（例如 gemini_gems_data.html）
2. "Gemini in Workspace" 匯出的 Conversation History 資料夾，每篇對話是一個
   conversation_<id>.txt，內容其實是 JSON（含 conversation_turns 陣列）

不會自動寫入 profile.md —— 刻意保留由人（或 Claude）閱讀萃取結果後手動歸納這一步，
避免原始對話片段直接被複製進長期保存的摘要檔案。

用法：
    python memory/import_gemini_takeout.py
"""

from __future__ import annotations

import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path

RAW_DIR = Path(__file__).parent / "raw"
EXTRACTED_DIR = RAW_DIR / "extracted"


class _TextExtractor(HTMLParser):
    """把 HTML 內容轉成保留基本段落結構的純文字。"""

    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self._chunks.append(text)

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in ("br", "p", "div", "li"):
            self._chunks.append("\n")

    def text(self) -> str:
        joined = "".join(
            chunk if chunk == "\n" else chunk + " " for chunk in self._chunks
        )
        return re.sub(r"\n{2,}", "\n\n", joined).strip()


def html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return parser.text()


def extract_zips() -> list[Path]:
    zips = sorted(RAW_DIR.glob("*.zip"))
    extracted_roots = []
    for zip_path in zips:
        target = RAW_DIR / f"_unzipped_{zip_path.stem}"
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(target)
        extracted_roots.append(target)
        print(f"解壓完成: {zip_path.name} -> {target.relative_to(RAW_DIR.parent)}")
    return extracted_roots


def find_html_files(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        files.extend(root.rglob("*.html"))
    # 也支援使用者直接把解壓好的資料夾放進 raw/ 的情況
    for existing in RAW_DIR.iterdir():
        if existing.is_dir() and not existing.name.startswith("_unzipped_") and existing.name != "extracted":
            files.extend(existing.rglob("*.html"))
    return files


def find_conversation_json_files() -> list[Path]:
    """找 'Gemini in Workspace' 格式的 conversation_*.txt（內容其實是 JSON）。"""
    return [p for p in RAW_DIR.rglob("*.txt") if p.parent != EXTRACTED_DIR]


def conversation_json_to_text(raw: str) -> str | None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    turns = data.get("conversation_turns")
    if turns is None:
        return None

    lines = [f"標題：{data.get('title', '')}"]
    for turn in turns:
        if "user_turn" in turn:
            lines.append(f"\n[使用者]\n{turn['user_turn'].get('prompt', '')}")
        elif "system_turn" in turn:
            texts = [t.get("data", "") for t in turn["system_turn"].get("text", [])]
            if texts:
                lines.append(f"\n[Gemini]\n{chr(10).join(texts)}")
    return "\n".join(lines).strip()


def main() -> None:
    RAW_DIR.mkdir(exist_ok=True)
    EXTRACTED_DIR.mkdir(exist_ok=True)

    if not any(RAW_DIR.iterdir()):
        print(f"'{RAW_DIR}' 是空的。請先把 Gemini 對話匯出檔（Takeout zip 或 "
              f"Conversation History 資料夾）放進這個資料夾。")
        return

    roots = extract_zips()
    html_files = find_html_files(roots)
    json_txt_files = find_conversation_json_files()

    empty_count = 0
    written_count = 0

    for html_file in html_files:
        raw = html_file.read_text(encoding="utf-8", errors="ignore")
        text = html_to_text(raw)
        if not text:
            empty_count += 1
            continue
        out_path = EXTRACTED_DIR / f"{html_file.stem}.txt"
        out_path.write_text(text, encoding="utf-8")
        written_count += 1

    for txt_file in json_txt_files:
        raw = txt_file.read_text(encoding="utf-8", errors="ignore")
        text = conversation_json_to_text(raw)
        if not text:
            continue
        out_path = EXTRACTED_DIR / f"{txt_file.stem}.txt"
        out_path.write_text(text, encoding="utf-8")
        written_count += 1

    if not html_files and not json_txt_files:
        print("找不到任何 .html 或 conversation_*.txt 檔案。可能是匯出檔結構不同，"
              "請人工檢查 memory/raw/ 底下的內容。")
        return

    print(f"處理完成：{written_count} 個檔案寫入純文字，{empty_count} 個 HTML 檔案內容為空。")
    if written_count:
        print(f"純文字結果在 '{EXTRACTED_DIR}'，接下來請請 Claude 讀取這些內容並歸納進 profile.md。")
    if empty_count and not written_count:
        print("所有檔案內容都是空的 —— 這代表 Takeout 匯出的分類可能沒有包含實際對話內容，"
              "請重新確認 Takeout 匯出設定（詳見 memory/README.md）。")


if __name__ == "__main__":
    main()
