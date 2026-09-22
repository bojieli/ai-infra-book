# Traditional Chinese Edition (繁體中文版)

《深入理解 AI Infra：量化分析與系統設計》繁體中文版，與簡體中文源稿及英文版並列，不替換原始 `manuscripts/` 或 `book/`。

全書包含前言（`introduction.md`）與第 1 至第 12 章，採用符合台灣資訊工程專業用語與 `/skill:speak-human-tw` 規範進行在地化校對與去 AI 味潤飾。

## 目錄結構

| 路徑 | 內容說明 |
| :--- | :--- |
| `introduction.md`, `chapter01.md` … `chapter12.md` | 在地化校對後的繁體中文各章節 |
| `cover.tex` | 沿用系列 ElegantBook 處理器與互聯拓撲繪圖的繁體中文封面 |
| `preamble.tex` | 繁體中文排版配置（載入系列基礎樣式並相容全書 CJK 字型） |
| `build_pdf.py`, `build_pdf.sh` | Pandoc + XeLaTeX 編譯腳本，對齊 `book-en/build_pdf.py` |
| `assemble.py` | 從 `manuscripts/` 自動重建各章節 |
| `tools/` | 翻譯腳本（`translate_tw.py`）、校驗工具（`verify_tw.py`）與技術術語表（`glossary.json`） |

## 在地化原則與品質把關

繁體中文版遵循 `/skill:speak-human-tw` 規範：

1. **資訊工程專業術語在地化**：
   - 顯存 → 視訊記憶體 (VRAM)
   - 內存 → 記憶體
   - 網絡 / 帶寬 → 網路 / 頻寬
   - 算子 → 運算子
   - 服務器 / 服務端 / 客戶端 → 伺服器 / 伺服端 / 客戶端
   - 負載均衡 → 負載平衡
   - 總線 / 鏈路 → 匯流排 / 鏈路
   - 併發 / 異步 → 並行 / 非同步
   - 緩存 → 快取 (Cache)
   - 預填充 / 解碼 → 預填充 (Prefill) / 解碼 (Decode)
   - 詞元 → 詞元 (Token)
   - 參數（避免 OpenCC 誤轉為引數）
2. **符號與排版規則**：
   - 引號轉換：簡中雙引號 `“ ”` 轉為正體角引號 `「 」`，單引號轉為 `『 』`。
   - 標點符號一律全形化，破折號與刪節號正規化為 `⋯⋯`。
   - LaTeX 數學公式（`$...$`、`$$...$$`）、程式碼區塊與向量圖參照路徑 100% 嚴格保護，零遺失、零跑版。
3. **無損引用圖表**：
   - 直接解析並引用 `manuscripts/ch01/` 等目錄下的原始高解析向量 PDF 圖檔，無需在倉庫內重複儲存冗餘的圖檔資產。

## 編譯方式

本版與主版本及英文版一樣，可透過 Pandoc + XeLaTeX 進行編譯：

```bash
bash book-zh-tw/build_pdf.sh
```

在 GitHub Actions CI 中，本版已整合進 `.github/workflows/book-site.yml`，在每次 PR 與 Release 中自動編譯輸出 `AI-Infra-Book-ZH-TW.pdf`。
