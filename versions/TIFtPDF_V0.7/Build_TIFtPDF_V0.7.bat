@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"
set "SOURCE=TIFtPDF_V0.7.pyw"
set "OUTDIR=build_TIFtPDF_V0.7"

python -m pip install --upgrade nuitka ordered-set zstandard pillow pymupdf tkinterdnd2
if errorlevel 1 goto :error

rem 第一階段：standalone，方便檢查 DLL、Tcl/Tk 與 tkinterdnd2 資料是否齊全
python -m nuitka ^
  --mode=standalone ^
  --enable-plugin=tk-inter ^
  --windows-console-mode=disable ^
  --include-package=tkinterdnd2 ^
  --include-package-data=tkinterdnd2 ^
  --include-package=PIL ^
  --include-package=fitz ^
  --output-dir="%OUTDIR%\standalone" ^
  --output-filename=TIFtPDF_V0.7.exe ^
  --assume-yes-for-downloads ^
  "%SOURCE%"
if errorlevel 1 goto :error

rem 第二階段：正式單一執行檔
python -m nuitka ^
  --mode=onefile ^
  --enable-plugin=tk-inter ^
  --windows-console-mode=disable ^
  --include-package=tkinterdnd2 ^
  --include-package-data=tkinterdnd2 ^
  --include-package=PIL ^
  --include-package=fitz ^
  --output-dir="%OUTDIR%\onefile" ^
  --output-filename=TIFtPDF_V0.7.exe ^
  --onefile-tempdir-spec="{CACHE_DIR}/{COMPANY}/{PRODUCT}/{VERSION}" ^
  --company-name=Atex ^
  --product-name=TIFtPDF ^
  --file-version=0.7.0.0 ^
  --product-version=0.7.0.0 ^
  --file-description="TIF拌成PDF" ^
  --copyright="Atex" ^
  --assume-yes-for-downloads ^
  "%SOURCE%"
if errorlevel 1 goto :error

echo.
echo 編譯完成：%OUTDIR%\onefile\TIFtPDF_V0.7.exe
pause
exit /b 0

:error
echo.
echo 編譯失敗，請查看上方 Nuitka 訊息。
pause
exit /b 1
