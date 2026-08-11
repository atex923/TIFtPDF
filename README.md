# TIFtPDF

TIFtPDF（TIF拌成PDF）是一個輕量 Windows 拖曳轉檔工具，專注在日常掃描檔、圖片與 PDF 之間的快速轉換。

## 程式特色

- 拖曳 TIF / TIFF 轉成 PDF，多頁 TIFF 會依原頁序合併成同一份 PDF。
- 拖曳 PNG / JPG / JPEG 轉成 PDF，並自動處理透明背景與 EXIF 方向。
- 拖曳 PDF 轉成 JPG，每頁輸出一張 300 DPI、品質 100 的圖片。
- 輸出檔直接放在來源資料夾，不需要額外設定路徑。
- 轉檔在背景執行緒處理，降低 GUI 卡住的機會。
- 視窗保持最上層，適合反覆拖曳使用。
- 錯誤會寫入 `TIFtPDF_error.log`，方便追查問題。
- 可用 Nuitka 打包成無 Console 的 Windows 單一 EXE。

## 輸出規則

- 圖片轉 PDF：`原檔名_rt.pdf`
- PDF 轉 JPG：`原檔名P1.jpg`、`原檔名P2.jpg`、`原檔名P3.jpg`...

## 執行方式

需要 Python 3.10 以上。

```bash
python -m pip install -r requirements.txt
python TIFtPDF_V0.7.pyw
```

## Windows 打包

在 Windows 環境執行：

```bat
Build_TIFtPDF_V0.7.bat
```

批次檔會先建立 standalone 版本方便檢查，再建立 onefile 單一執行檔。

## 目前版本

V0.7
