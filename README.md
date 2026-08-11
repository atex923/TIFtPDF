# HEIFtLife

HEIFtLife 是一個極簡 HEIF / HEIC 轉 JPG 拖曳小工具，主打「打開、拖進去、轉好了」的輕量流程。

## 程式特色

- **拖曳轉檔**：直接把 `.heif` / `.heic` 檔案拖進 200 x 200 小視窗。
- **原地輸出**：JPG 會輸出到原圖資料夾，檔名格式為 `原檔名_rt.jpg`。
- **高品質 JPG**：使用 `quality=100`、`subsampling=0`，不縮圖、不改尺寸。
- **色彩保留**：轉檔時盡量保留原始 HEIF / HEIC 的 ICC 色彩 profile。
- **不卡視窗**：背景執行緒處理轉檔，大圖轉換時介面仍能保持回應。
- **簡潔介面**：無按鈕、永遠置頂、淡色背景、中央虛線拖曳框與 Canvas 圖示。
- **拖曳回饋**：拖曳進入時框線變亮，轉檔中顯示 `Working...`，多檔完成顯示 `Done！ x N`。
- **錯誤可追蹤**：`.pyw` / exe 無命令視窗模式下仍會寫入 `HEIFtLife_error_log.txt`。
- **打包友善**：支援 Nuitka onefile，打包後不會再嘗試用 exe 自行執行 pip。

## 執行方式

```bash
pip install -r requirements.txt
python HEIFtLife.py
```

Windows 無命令視窗：

```bat
pythonw HEIFtLife.pyw
```

## 需求套件

- `pillow`
- `tkinterdnd2`
- `pi-heif` 或 `pillow-heif`

## 目前版本

`V0.12`
