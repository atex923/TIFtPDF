# TIFtPDF V0.7 — Codex 移轉說明

## 專案基本資訊
- 程式名稱：TIFtPDF
- 視窗中文標題：TIF拌成PDF
- 目前版號：V0.7
- 版本規則：一般改版只增加第二碼，依序 V0.7、V0.8 … V0.99。
- Windows GUI：Tkinter + tkinterdnd2
- 主程式：TIFtPDF_V0.7.pyw
- 目標：使用 Nuitka 轉譯為 Windows 單一 EXE，且不顯示 Console。

## 現有功能
1. 拖曳 TIF / TIFF：轉成 PDF。
   - 多頁 TIFF 依原頁序轉入同一份 PDF。
2. 拖曳 PNG / JPG / JPEG：轉成 PDF。
3. 拖曳 PDF：每頁各轉成一張 JPG。
   - 解析度：300 DPI。
   - JPG 品質：100。
   - 命名：原檔名P1.jpg、原檔名P2.jpg、原檔名P3.jpg……
4. 圖片轉 PDF 輸出：原檔名_rt.pdf。
5. 輸出位置：來源檔案所在資料夾。
6. 視窗最上層顯示。
7. 轉檔放在背景執行緒，避免 GUI 卡死。
8. 錯誤寫入 TIFtPDF_error.log。
9. 執行時不自動安裝 Python 套件；缺套件時顯示提示。

## 主要相依套件
- Pillow
- PyMuPDF (`fitz`)
- tkinterdnd2

## Nuitka 打包原則
先 standalone 測試，再 onefile 正式打包。

### Standalone
```bat
python -m nuitka ^
  --mode=standalone ^
  --enable-plugin=tk-inter ^
  --windows-console-mode=disable ^
  --include-package=tkinterdnd2 ^
  --include-package-data=tkinterdnd2 ^
  --include-package=PIL ^
  --include-package=fitz ^
  --output-dir=build_TIFtPDF_V0.7\standalone ^
  --output-filename=TIFtPDF_V0.7.exe ^
  --assume-yes-for-downloads ^
  TIFtPDF_V0.7.pyw
```

### Onefile
```bat
python -m nuitka ^
  --mode=onefile ^
  --enable-plugin=tk-inter ^
  --windows-console-mode=disable ^
  --include-package=tkinterdnd2 ^
  --include-package-data=tkinterdnd2 ^
  --include-package=PIL ^
  --include-package=fitz ^
  --output-dir=build_TIFtPDF_V0.7\onefile ^
  --output-filename=TIFtPDF_V0.7.exe ^
  --onefile-tempdir-spec="{CACHE_DIR}/{COMPANY}/{PRODUCT}/{VERSION}" ^
  --company-name=Atex ^
  --product-name=TIFtPDF ^
  --file-version=0.7.0.0 ^
  --product-version=0.7.0.0 ^
  --file-description="TIF拌成PDF" ^
  --copyright=Atex ^
  --assume-yes-for-downloads ^
  TIFtPDF_V0.7.pyw
```

## Codex 接手要求
- 以 `TIFtPDF_V0.7.pyw` 為唯一最新主程式基準。
- 不要改掉既有拖曳操作方式與輸出命名規則，除非收到明確新需求。
- 修改後先做 Python 語法檢查。
- 若修改影響打包，相對應同步修改 `Build_TIFtPDF_V0.7.bat`。
- 每次正式功能修改後依規則進版，並同步更新：
  - 檔名
  - `VERSION`
  - 視窗標題
  - Nuitka 輸出檔名
  - EXE file-version / product-version
  - build 資料夾名稱
- Nuitka 問題優先以 standalone 驗證，不要只測 onefile。
- 維持中文路徑與中文檔名可正常處理。

## V0.7 更新摘要
- 導入 GitHub 專案結構與 README。
- 圖片轉 PDF 時套用 EXIF 方向校正，手機照片方向更穩定。
- 混合拖曳時保留有效檔案轉換，並清楚回報略過數量。
- 同步更新 Nuitka 打包檔名、輸出資料夾與 EXE 版本資訊。

## 建議驗收項目
- 單頁 TIFF → PDF
- 多頁 TIFF → 單一 PDF，頁數與順序正確
- PNG（含透明背景）→ PDF
- JPG / JPEG → PDF
- PDF 1頁 / 多頁 → JPG，300 DPI、品質100
- PDF 輸出 JPG 命名為 P1、P2…
- 中文資料夾、中文檔名
- 一次拖曳多個不同格式檔案
- 大型 PDF 轉圖時 GUI 不凍結
- Standalone EXE 可啟動
- Onefile EXE 可啟動
- 無 Console 視窗
