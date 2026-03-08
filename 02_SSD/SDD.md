這是一份根據您提供的 PRD 所設計的精簡版軟體設計文件 (SDD)。本文件專為 **Python + Streamlit** 生態系優化，旨在讓開發者（或 AI 輔助工具）能快速從零開始建構出功能完備的 MVP。

---

# 軟體設計文件 (SDD)：DOCX 轉 MP3 專業轉換工具

**版本：** 1.0  
**狀態：** 實作準備  
**技術棧：** Python, Streamlit, SQLite, Edge-TTS

---

## 1. 簡介

### 1.1 專案概述
本專案旨在開發一個輕量級的 Web 工具，將 DOCX 文件的內容轉換為高品質的 MP3 語音檔。透過整合 Microsoft Edge TTS 服務，解決長文本處理潰散、網路連線限制以及中文破音字讀音錯誤等核心痛點。

### 1.2 系統目標
*   **高穩定性解析**：精確提取 DOCX 文字，不受複雜格式干擾。
*   **自定義校正**：提供視覺化替換表，修正特定詞彙的朗讀發音。
*   **智慧分拆**：自動將超過 10,000 字的長文切分為多個音檔，確保合成成功。
*   **跨區穩定**：支援手動切換不同地區的 TTS 伺服器端點。
*   **批次交付**：自動編號並打包成 ZIP 檔供使用者一鍵下載。

### 1.3 技術選型
*   **程式語言**：Python 3.9+
*   **Web UI 框架**：Streamlit (提供即時互動介面與狀態管理)
*   **TTS 引擎**：`edge-tts` (非官方但穩定的 Microsoft Edge 接口)
*   **文件處理**：`python-docx`
*   **資料庫**：SQLite (儲存替換規則與使用者偏好)
*   **資料庫 ORM**：SQLAlchemy

---

## 2. 系統架構與運作流程

### 2.1 整體架構
```
[使用者瀏覽器] 
      ↑↓ (HTTP/Websocket)
[Streamlit 應用程式 (app.py)]
      ↑↓
[業務邏輯層 (Logic)] ←→ [Edge TTS API (外部服務)]
      ↑↓
[資料持久層 (SQLAlchemy + SQLite)]
```

### 2.2 運作流程詳解
1.  **設定階段**：使用者於側邊欄選擇服務區域 (Region)、語音 (Voice) 與調整速度。
2.  **上傳與解析**：使用者上傳 `.docx`，系統調用 `parser.py` 提取純文字。
3.  **預處理**：系統根據資料庫中的「替換表」，執行全域文字替換（如：般若 → 波惹）。
4.  **智慧切分**：若字數超過 10,000 字，`splitter.py` 尋找標點符號進行斷點切分。
5.  **非同步合成**：系統將文本段落發送至 `edge-tts`，產生多個 MP3 二進位流。
6.  **打包下載**：使用 `zipfile` 模組將所有 MP3 包裝，顯示下載按鈕。

---

## 3. 核心模組設計

### 3.1 介面主控模組 (`app.py`)
*   **職責**：定義 UI 佈局、接收用戶輸入、管理應用程式狀態。
*   **核心功能**：
    *   `render_sidebar()`：渲染區域、語音、語速等控制項。
    *   `render_replacement_table()`：顯示與編輯詞彙替換表。
    *   `handle_conversion()`：觸發轉換流程的邏輯封裝。

### 3.2 文件解析模組 (`docx_handler.py`)
*   **職責**：處理 DOCX 檔案讀取。
*   **核心功能**：
    *   `extract_text(file_buffer)`：從上傳的檔案流中提取段落文字，合併為字串。

### 3.3 語音合成引擎 (`tts_engine.py`)
*   **職責**：與 Edge TTS 通訊，處理分段與區域切換。
*   **核心功能**：
    *   `get_voices(region)`：根據區域獲取支援的語音清單。
    *   `split_text(text, limit=10000)`：執行智慧切分演算法。
    *   `generate_audio(text, voice, rate, pitch)`：呼叫 `edge-tts` 產生音訊。

### 3.4 資料管理模組 (`database.py`)
*   **職責**：管理 SQLite 資料庫的連線與 CRUD 操作。
*   **核心功能**：
    *   `get_all_rules()`：獲取所有替換規則。
    *   `add_rule(original, target)`：新增替換規則。
    *   `delete_rule(rule_id)`：刪除特定規則。

---

## 4. 資料庫設計

### 4.1 資料庫選型
選用 **SQLite**。原因：無需額外架設伺服器、單一檔案易於備份、讀寫效能足以應付個人級替換表需求。

### 4.2 資料表設計

**表名：`replacement_rules`**

| 欄位名稱 | 資料型態 | 說明 | 備註 |
|----------|----------|------|------|
| id | INTEGER | 唯一識別碼 | 主鍵，自動遞增 |
| original_text | TEXT | 原始文字（如：般若） | 不可為空 |
| replace_with | TEXT | 替換後文字（如：波惹） | 可為空 |
| created_at | DATETIME | 建立時間 | 自動生成 |

---

## 5. 使用者介面與互動規劃

### 5.1 頁面結構
*   **側邊欄 (Sidebar)**：
    *   服務區域選擇（下拉選單：TW, CN, US）。
    *   語音角色選擇（動態連動選單）。
    *   語速調節 (0.5x - 2.0x)。
    *   音高調節 (-50Hz - +50Hz)。
*   **主面板 (Main Panel)**：
    *   **分頁 1：檔案轉檔** - 拖放上傳區、字數預覽、轉換進度條、下載按鈕。
    *   **分頁 2：發音校正** - 詞彙替換管理介面（新增/刪除規則）。

### 5.2 核心互動流程
1.  用戶進入「發音校正」頁面設定常用術語。
2.  回到「檔案轉檔」頁面，上傳 `.docx`。
3.  點擊「開始轉換」，介面顯示 Progress Bar 與當前處理段落。
4.  完成後，主面板出現「下載 ZIP 包」按鈕。

---

## 6. API 設計 / 功能函數

### 智慧切分函數 `split_text_smartly`
*   **輸入**：`text` (str), `max_chars` (int)
*   **輸出**：`List[str]`
*   **邏輯**：
    1.  如果 `len(text) <= max_chars`，直接回傳。
    2.  如果超過，取 `text[0:max_chars]`。
    3.  從 `max_chars` 位置向後搜尋最近的 `。` 或 `\n`。
    4.  切割並遞迴處理剩餘文字。

### 全域替換函數 `apply_replacement_rules`
*   **輸入**：`raw_text` (str)
*   **輸出**：`cleaned_text` (str)
*   **邏輯**：從資料庫讀取所有規則，迴圈執行 `raw_text.replace(old, new)`。

---

## 7. 錯誤處理策略

| 錯誤情境 | 處理策略 | UI 呈現 |
|----------|----------|------|
| TTS 伺服器連線超時 | 自動重試 2 次，若仍失敗則跳過該段並記錄 | 顯示紅標警告「區域 [XX] 連線失敗，請嘗試切換區域」 |
| DOCX 檔案損壞 | 捕捉解析異常 | 彈出錯誤對話框「檔案格式不正確或已損毀」 |
| 字數超過瀏覽器限制 | 前端檢查字數 (限 10 萬字) | 提示「文件過大，請分拆後上傳」 |
| SQLite 寫入失敗 | 捕捉資料庫鎖定異常 | 提示「設定儲存失敗」 |

---

## 8. 實作路徑 (Implementation Roadmap)

### 8.1 環境建置與依賴安裝
```bash
mkdir docx_to_mp3_tool
cd docx_to_mp3_tool
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
```

**requirements.txt**
```text
streamlit
python-docx
edge-tts
sqlalchemy
pandas
shutil
```

安裝指令：
```bash
pip install -r requirements.txt
```

### 8.2 資料庫模組開發 (`database.py`)
*   實作 SQLAlchemy `Base` 與 `ReplacementRule` Model。
*   實作 `init_db()` 確保資料表自動建立。

### 8.3 核心業務邏輯開發
1.  **`docx_handler.py`**：實作 `python-docx` 提取文字。
2.  **`tts_logic.py`**：整合 `edge-tts` 的 `Communicate` 類別，實作 `async` 轉換函式。
3.  **`utils.py`**：實作智慧切分與 ZIP 壓縮邏輯。

### 8.4 使用者介面開發 (`app.py`)
1.  設置 Streamlit `st.set_page_config`。
2.  建立 `st.sidebar` 控制項。
3.  實作 `st.tabs(["轉檔任務", "發音字典"])`。
4.  使用 `st.dataframe` 或 `st.table` 配合按鈕展示字典管理。

### 8.5 測試與驗證
*   **單元測試**：驗證 15,000 字是否正確切分為兩段。
*   **整合測試**：上傳一個包含「般若」的檔案，確認輸出的音訊讀作「波惹」。
*   **連線測試**：分別切換 TW, CN 區域，測試語音列表加載速度。

### 8.6 部署與運行說明
在本機執行：
```bash
streamlit run app.py
```
本工具可直接部屬至 Streamlit Cloud 或任何支援 Python 的 VPS。

---
**SDD 結束**