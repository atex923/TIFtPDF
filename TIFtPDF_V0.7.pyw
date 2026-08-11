# -*- coding: utf-8 -*-
"""
TIFtPDF V0.7
TIF/TIFF、PNG、JPG 與 PDF 雙向轉換小工具。

Nuitka 建議：先 standalone 測試，再 onefile 正式打包。
"""
from __future__ import annotations

import logging
import queue
import sys
import threading
import traceback
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

try:
    from PIL import Image, ImageOps, ImageSequence
    import fitz
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError as exc:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "缺少必要套件",
        "請先安裝必要套件：\n\n"
        "python -m pip install -U pillow pymupdf tkinterdnd2\n\n"
        f"詳細錯誤：{exc}",
        parent=root,
    )
    root.destroy()
    raise SystemExit(1) from exc

APP_NAME = "TIF拌成PDF"
APP_FILE = "TIFtPDF"
VERSION = "V0.7"
WINDOW_SIZE = "200x200"
PROMPT_TEXT = "Drag & Drop"
DONE_TEXT = "Done！"
SUPPORTED_EXTENSIONS = {".tif", ".tiff", ".png", ".jpg", ".jpeg", ".pdf"}

PDF_IMAGE_DPI = 300
PDF_JPG_QUALITY = 100
IMAGE_PDF_RESOLUTION = 100.0

BG = "#F5F5F7"
PANEL_BG = "#FBFBFD"
BLUE = "#3F7BEF"
BLUE_LIGHT = "#AFC7FF"
BORDER = "#D7D7DC"
RED = "#E5484D"


def executable_dir() -> Path:
    """取得使用者看得到的程式所在資料夾。"""
    if getattr(sys, "frozen", False) or "__compiled__" in globals():
        return Path(sys.argv[0]).resolve().parent
    return Path(__file__).resolve().parent


LOG_PATH = executable_dir() / f"{APP_FILE}_error.log"
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.ERROR,
    encoding="utf-8",
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def log_exception(context: str) -> None:
    logging.error("%s\n%s", context, traceback.format_exc())


def rounded_rect(canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, radius: int = 18, **kwargs) -> int:
    points = [
        x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def flatten_to_rgb(frame: Image.Image) -> Image.Image:
    """轉為 PDF/JPG 可安全儲存的 RGB，透明區域改成白色。"""
    frame.load()
    frame = ImageOps.exif_transpose(frame)
    if frame.mode == "RGB":
        return frame.copy()
    if frame.mode == "L":
        return frame.convert("RGB")
    if frame.mode in {"RGBA", "LA"} or "transparency" in frame.info:
        rgba = frame.convert("RGBA")
        background = Image.new("RGB", rgba.size, "white")
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return frame.convert("RGB")


def tif_to_pdf(source: Path, destination: Path) -> int:
    pages: list[Image.Image] = []
    try:
        with Image.open(source) as image:
            pages = [flatten_to_rgb(frame) for frame in ImageSequence.Iterator(image)]
        if not pages:
            raise ValueError("找不到可轉換的 TIFF 頁面")
        pages[0].save(
            destination,
            "PDF",
            save_all=True,
            append_images=pages[1:],
            resolution=IMAGE_PDF_RESOLUTION,
        )
        return len(pages)
    finally:
        for page in pages:
            page.close()


def image_to_pdf(source: Path, destination: Path) -> int:
    with Image.open(source) as image:
        page = flatten_to_rgb(image)
    try:
        page.save(destination, "PDF", resolution=IMAGE_PDF_RESOLUTION)
    finally:
        page.close()
    return 1


def is_supported_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS


def pdf_to_jpg(source: Path, dpi: int = PDF_IMAGE_DPI, quality: int = PDF_JPG_QUALITY) -> int:
    with fitz.open(source) as document:
        if document.page_count <= 0:
            raise ValueError("PDF 沒有可轉換的頁面")
        matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        for page_number, page in enumerate(document, start=1):
            destination = source.with_name(f"{source.stem}P{page_number}.jpg")
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            try:
                pixmap.save(str(destination), jpg_quality=quality)
            finally:
                pixmap = None
        return document.page_count


@dataclass(slots=True)
class ConversionResult:
    converted: int = 0
    total_pages: int = 0
    tif_count: int = 0
    image_count: int = 0
    pdf_count: int = 0
    skipped_count: int = 0
    errors: list[str] | None = None
    skipped: list[str] | None = None

    def __post_init__(self) -> None:
        if self.errors is None:
            self.errors = []
        if self.skipped is None:
            self.skipped = []

    @property
    def attempted(self) -> int:
        return self.converted + len(self.errors or [])


def summarize_result(result: ConversionResult) -> str:
    lines = [
        f"成功：{result.converted} 個檔案，共 {result.total_pages} 頁。",
        f"TIF→PDF：{result.tif_count} 個；圖片→PDF：{result.image_count} 個；PDF→JPG：{result.pdf_count} 個。",
    ]
    if result.skipped_count:
        lines.append(f"略過：{result.skipped_count} 個不支援或不存在的項目。")
    return "\n".join(lines)


def convert_files(paths: list[Path]) -> ConversionResult:
    result = ConversionResult()
    assert result.errors is not None
    assert result.skipped is not None
    for path in paths:
        if not is_supported_file(path):
            result.skipped_count += 1
            result.skipped.append(path.name or str(path))
            continue
        try:
            suffix = path.suffix.lower()
            if suffix == ".pdf":
                page_count = pdf_to_jpg(path)
                result.pdf_count += 1
            else:
                destination = path.with_name(f"{path.stem}_rt.pdf")
                if suffix in {".tif", ".tiff"}:
                    page_count = tif_to_pdf(path, destination)
                    result.tif_count += 1
                else:
                    page_count = image_to_pdf(path, destination)
                    result.image_count += 1
            result.converted += 1
            result.total_pages += page_count
        except Exception as exc:
            log_exception(f"轉檔失敗：{path}")
            result.errors.append(f"{path.name}：{exc}")
    return result


class TIFtPDFApp:
    def __init__(self) -> None:
        self.root = TkinterDnD.Tk()
        self.root.title(f"{APP_NAME} {VERSION}")
        self.root.geometry(WINDOW_SIZE)
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.attributes("-topmost", True)

        self.canvas = tk.Canvas(self.root, width=200, height=200, bg=BG, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        self.status_after_id: str | None = None
        self.text_id: int | None = None
        self.result_queue: queue.Queue[ConversionResult] = queue.Queue()
        self.is_working = False

        self.draw_ui()
        self.canvas.drop_target_register(DND_FILES)
        self.canvas.dnd_bind("<<Drop>>", self.on_drop)

    def draw_ui(self) -> None:
        self.canvas.delete("all")
        rounded_rect(self.canvas, 8, 8, 192, 192, radius=18, fill=PANEL_BG, outline=BORDER, width=1)
        self.canvas.create_oval(22, 21, 34, 33, fill="#FF5F57", outline="#E0473F")
        self.canvas.create_oval(42, 21, 54, 33, fill="#FFBD2E", outline="#E0A326")
        self.canvas.create_oval(62, 21, 74, 33, fill="#28C840", outline="#20A934")
        self.canvas.create_text(130, 27, text=APP_NAME, fill="#3A3A3C", font=("Microsoft JhengHei UI", 10, "bold"))
        self.canvas.create_line(8, 44, 192, 44, fill="#E5E5EA")
        self.draw_dashed_round_box(30, 62, 170, 170, 14)
        self.draw_convert_icon(100, 106)
        self.text_id = self.canvas.create_text(100, 148, text=PROMPT_TEXT, fill=BLUE, font=("Helvetica", 14, "bold"))

    def draw_dashed_round_box(self, x1: int, y1: int, x2: int, y2: int, radius: int) -> None:
        self.canvas.create_line(x1 + radius, y1, x2 - radius, y1, fill=BLUE, width=2, dash=(8, 5))
        self.canvas.create_line(x1 + radius, y2, x2 - radius, y2, fill=BLUE, width=2, dash=(8, 5))
        self.canvas.create_line(x1, y1 + radius, x1, y2 - radius, fill=BLUE, width=2, dash=(8, 5))
        self.canvas.create_line(x2, y1 + radius, x2, y2 - radius, fill=BLUE, width=2, dash=(8, 5))
        self.canvas.create_arc(x1, y1, x1 + 2 * radius, y1 + 2 * radius, start=90, extent=90, outline=BLUE, width=2, style="arc")
        self.canvas.create_arc(x2 - 2 * radius, y1, x2, y1 + 2 * radius, start=0, extent=90, outline=BLUE, width=2, style="arc")
        self.canvas.create_arc(x1, y2 - 2 * radius, x1 + 2 * radius, y2, start=180, extent=90, outline=BLUE, width=2, style="arc")
        self.canvas.create_arc(x2 - 2 * radius, y2 - 2 * radius, x2, y2, start=270, extent=90, outline=BLUE, width=2, style="arc")

    def draw_convert_icon(self, cx: int, cy: int) -> None:
        self.canvas.create_polygon(cx - 53, cy - 30, cx - 19, cy - 30, cx - 8, cy - 19, cx - 8, cy + 28, cx - 53, cy + 28, fill="", outline=BLUE_LIGHT, width=3, joinstyle="round")
        self.canvas.create_line(cx - 19, cy - 30, cx - 19, cy - 19, cx - 8, cy - 19, fill=BLUE_LIGHT, width=3)
        self.canvas.create_text(cx - 30, cy + 2, text="IMG", fill=BLUE_LIGHT, font=("Arial", 11, "bold"))
        self.canvas.create_line(cx - 1, cy, cx + 18, cy, fill=BLUE, width=4, arrow="last", arrowshape=(9, 11, 5))
        self.canvas.create_polygon(cx + 24, cy - 30, cx + 53, cy - 30, cx + 64, cy - 19, cx + 64, cy + 28, cx + 24, cy + 28, fill="", outline=BLUE, width=3, joinstyle="round")
        self.canvas.create_line(cx + 53, cy - 30, cx + 53, cy - 19, cx + 64, cy - 19, fill=BLUE, width=3)
        self.canvas.create_rectangle(cx + 30, cy - 2, cx + 59, cy + 16, fill=RED, outline=RED)
        self.canvas.create_text(cx + 44, cy + 7, text="PDF", fill="white", font=("Arial", 9, "bold"))

    def set_status(self, text: str) -> None:
        if self.text_id is not None:
            self.canvas.itemconfigure(self.text_id, text=text)

    def reset_status_later(self) -> None:
        if self.status_after_id:
            self.root.after_cancel(self.status_after_id)
        self.status_after_id = self.root.after(30000, lambda: self.set_status(PROMPT_TEXT))

    def on_drop(self, event) -> None:
        if self.is_working:
            messagebox.showinfo("轉檔進行中", "請等待目前的轉檔完成。", parent=self.root)
            return

        paths = [Path(value) for value in self.root.tk.splitlist(event.data)]
        if not any(is_supported_file(path) for path in paths):
            self.set_status("Image/PDF only")
            messagebox.showwarning("檔案格式不符", "請拖曳 TIF、TIFF、PNG、JPG、JPEG 或 PDF 檔案。", parent=self.root)
            self.reset_status_later()
            return

        self.is_working = True
        self.set_status("Working...")
        threading.Thread(target=self.worker, args=(paths,), daemon=True).start()
        self.root.after(100, self.poll_result)

    def worker(self, paths: list[Path]) -> None:
        self.result_queue.put(convert_files(paths))

    def poll_result(self) -> None:
        try:
            result = self.result_queue.get_nowait()
        except queue.Empty:
            self.root.after(100, self.poll_result)
            return

        self.is_working = False
        errors = result.errors or []
        if result.converted:
            self.set_status(DONE_TEXT)
            if errors or result.skipped_count:
                details = summarize_result(result)
                if errors:
                    details += "\n\n失敗：\n" + "\n".join(errors[:8]) + f"\n\n錯誤紀錄：{LOG_PATH}"
                messagebox.showwarning("部分轉檔完成", details, parent=self.root)
        else:
            self.set_status("Error")
            if errors:
                message = "\n".join(errors[:8]) + f"\n\n錯誤紀錄：{LOG_PATH}"
            else:
                message = "沒有可轉換的檔案。"
            messagebox.showerror("轉檔失敗", message, parent=self.root)
        self.reset_status_later()

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    try:
        TIFtPDFApp().run()
        return 0
    except Exception:
        log_exception("程式啟動失敗")
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("程式錯誤", f"程式無法啟動。\n\n錯誤紀錄：{LOG_PATH}", parent=root)
            root.destroy()
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
