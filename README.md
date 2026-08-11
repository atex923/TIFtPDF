# TIFtPDF

TIFtPDF（TIF拌成PDF）是一個給 Windows 使用的拖曳式轉檔小工具，用來快速處理掃描 TIFF、一般圖片與 PDF 之間的常見轉換。

## 主要功能

- **TIF / TIFF 轉 PDF**：支援單頁與多頁 TIFF，多頁檔會依原始頁序合併成同一份 PDF。
- **PNG / JPG / JPEG 轉 PDF**：圖片直接輸出成 PDF，PNG 透明背景會轉為白底，照片會套用 EXIF 方向校正。
- **PDF 轉 JPG**：PDF 每一頁輸出成一張 JPG，解析度 300 DPI、品質 100。
- **原地輸出**：轉好的檔案會放在來源檔案所在資料夾。
- **批次拖曳**：可一次拖入多個檔案，轉檔在背景執行緒處理，避免視窗卡住。
- **錯誤記錄**：失敗原因會寫入 `TIFtPDF_error.log`，方便追查。
- **Windows 打包友善**：提供 Nuitka 批次檔，可建立無 Console 的單一 EXE。

## 輸出命名

| 來源格式 | 輸出格式 | 命名規則 |
| --- | --- | --- |
| TIF / TIFF | PDF | `原檔名_rt.pdf` |
| PNG / JPG / JPEG | PDF | `原檔名_rt.pdf` |
| PDF | JPG | `原檔名P1.jpg`、`原檔名P2.jpg`、`原檔名P3.jpg`... |

## 安裝與執行

需要 Python 3.10 以上。

```bash
python -m pip install -r requirements.txt
python TIFtPDF_V0.8.pyw
```

## Windows 打包

在 Windows 環境執行：

```bat
Build_TIFtPDF_V0.8.bat
```

批次檔會先建立 standalone 版本方便檢查 DLL、Tcl/Tk 與 `tkinterdnd2` 資料，再建立 onefile 單一執行檔。

## 目前版本

`V0.8`

主目錄保留最新版主程式與打包檔：

```text
TIFtPDF_V0.8.pyw
Build_TIFtPDF_V0.8.bat
```

## 歷史版本

舊版已移到 repo 內的 `versions/` 歷史區，每個版號使用獨立資料夾保存：

```text
versions/TIFtPDF_V0.6/
versions/TIFtPDF_V0.7/
```

Google Drive 也同步保存相同的分版號資料夾：

```text
12.Codex/TIFtPDF_versions/
```
