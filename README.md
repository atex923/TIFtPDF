# TIFtPDF + HEIFtLife

這個 repo 目前收錄兩個輕量拖曳轉檔小工具：

- `TIFtPDF`：TIF / TIFF、常見圖片與 PDF 之間的日常轉換工具。
- `HEIFtLife`：HEIF / HEIC 拖曳轉 JPG 工具。

兩者都偏向「打開小視窗、拖進檔案、直接輸出」的快速工作流。

## TIFtPDF 特色

- 拖曳 TIF / TIFF 轉成 PDF，多頁 TIFF 會依原頁序合併成同一份 PDF。
- 拖曳 PNG / JPG / JPEG 轉成 PDF，並自動處理透明背景與 EXIF 方向。
- 拖曳 PDF 轉成 JPG，每頁輸出一張 300 DPI、品質 100 的圖片。
- 輸出檔直接放在來源資料夾，不需要額外設定路徑。
- 轉檔在背景執行緒處理，降低 GUI 卡住的機會。
- 視窗保持最上層，適合反覆拖曳使用。
- 錯誤會寫入 `TIFtPDF_error.log`，方便追查問題。
- 可用 Nuitka 打包成無 Console 的 Windows 單一 EXE。

## TIFtPDF 輸出規則

- 圖片轉 PDF：`原檔名_rt.pdf`
- PDF 轉 JPG：`原檔名P1.jpg`、`原檔名P2.jpg`、`原檔名P3.jpg`...

## HEIFtLife 特色

- 拖曳 `.heif` / `.heic` 轉成 JPG。
- JPG 會輸出到原圖資料夾，檔名格式為 `原檔名_rt.jpg`。
- 使用 `quality=100`、`subsampling=0`，不縮圖、不改尺寸。
- 轉檔時盡量保留原始 HEIF / HEIC 的 ICC 色彩 profile。
- 背景執行緒處理轉檔，大圖轉換時介面仍能保持回應。
- 無按鈕、永遠置頂、淡色背景、中央虛線拖曳框與 Canvas 圖示。
- 拖曳進入時框線變亮，轉檔中顯示 `Working...`，多檔完成顯示 `Done！ x N`。
- `.pyw` / exe 無命令視窗模式下仍會寫入 `HEIFtLife_error_log.txt`。

## 執行方式

需要 Python 3.10 以上。

```bash
python -m pip install -r requirements.txt
```

執行 TIFtPDF：

```bash
python TIFtPDF_V0.7.pyw
```

執行 HEIFtLife：

```bash
python HEIFtLife.py
```

Windows 無命令視窗執行 HEIFtLife：

```bat
pythonw HEIFtLife.pyw
```

## Windows 打包 TIFtPDF

在 Windows 環境執行：

```bat
Build_TIFtPDF_V0.7.bat
```

批次檔會先建立 standalone 版本方便檢查，再建立 onefile 單一執行檔。

## 目前版本

- TIFtPDF：`V0.7`
- HEIFtLife：`V0.12`
