# -*- coding: utf-8 -*-
"""
HEIFtLife V0.12
HEIF/HEIC 轉 JPG 拖曳小工具

V0.12 優化重點
- 轉檔改成背景執行緒，拖入大圖時視窗不會卡住。
- 增加執行錯誤 log：HEIFtLife_error_log.txt。
- 打包成 exe 後，不再嘗試用 exe 自己執行 pip；缺套件會顯示重新打包提示。
- source 模式保留缺少套件自動安裝：pillow、tkinterdnd2、pi-heif / pillow-heif。
- 拖曳路徑、中文資料夾、空白路徑處理更穩。
- 保留 200x200、淡色風格、最上層、無按鈕、Drag & Drop / Done！。
- 移除視窗裡的視窗底圖，只保留拖曳框與圖片翻身圖案。
- 拖曳進入時框線變亮，多檔完成顯示 Done！ x N。
- 轉 JPG 時盡量保留 ICC 色彩 profile。
- 內建 Canvas 繪製「圖片翻身」圖案，不使用外部圖片。
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

APP_NAME = "HEIF轉換罐"
APP_FILE = "HEIFtLife"
VERSION = "V0.12"
PROMPT_TEXT = "Drag & Drop"
DONE_TEXT = "Done！"
WORKING_TEXT = "Working..."
ERROR_TEXT = "Error"

BG = "#F5F5F7"
BLUE = "#3F7BEF"
BLUE_ACTIVE = "#1F63FF"
BLUE_LIGHT = "#AFC7FF"

SUPPORTED_EXTS = {".heif", ".heic"}
INSTALL_LOG_NAME = "HEIFtLife_install_log.txt"
ERROR_LOG_NAME = "HEIFtLife_error_log.txt"

PIP_READY = False
INSTALL_LOG_PATH: Path | None = None
ERROR_LOG_PATH: Path | None = None
HEIF_BACKEND_NAME = ""


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def app_dir() -> Path:
    """取得程式所在資料夾；Nuitka / PyInstaller 打包成 exe 時也能使用。"""
    try:
        if is_frozen():
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent
    except Exception:
        return Path.cwd()


def pick_writable_path(filename: str) -> Path:
    candidates = [
        app_dir() / filename,
        Path.cwd() / filename,
        Path.home() / "Downloads" / filename,
        Path(tempfile.gettempdir()) / filename,
    ]
    for path in candidates:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8", errors="replace") as f:
                f.write("")
            return path
        except Exception:
            continue
    return Path(tempfile.gettempdir()) / filename


def pick_install_log_path() -> Path:
    global INSTALL_LOG_PATH
    if INSTALL_LOG_PATH is None:
        INSTALL_LOG_PATH = pick_writable_path(INSTALL_LOG_NAME)
    return INSTALL_LOG_PATH


def pick_error_log_path() -> Path:
    global ERROR_LOG_PATH
    if ERROR_LOG_PATH is None:
        ERROR_LOG_PATH = pick_writable_path(ERROR_LOG_NAME)
    return ERROR_LOG_PATH


def write_text_log(path: Path, title: str, text: str) -> None:
    try:
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        with path.open("a", encoding="utf-8", errors="replace") as f:
            f.write(f"\n===== {now} | {title} =====\n")
            f.write(text)
            if not text.endswith("\n"):
                f.write("\n")
    except Exception:
        pass


def write_install_log(text: str) -> None:
    try:
        path = pick_install_log_path()
        with path.open("a", encoding="utf-8", errors="replace") as f:
            f.write(text)
            if not text.endswith("\n"):
                f.write("\n")
    except Exception:
        pass


def write_error_log(title: str, text: str) -> None:
    write_text_log(pick_error_log_path(), title, text)


def notify_error(title: str, message: str) -> None:
    """在 .pyw / 無 console 模式下也能顯示錯誤訊息。"""
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showerror(title, message, parent=root)
        root.destroy()
    except Exception:
        try:
            print(f"{title}: {message}", file=sys.stderr)
        except Exception:
            pass


def module_exists(import_name: str) -> bool:
    return importlib.util.find_spec(import_name) is not None


def startup_options() -> tuple[subprocess.STARTUPINFO | None, int]:
    startupinfo = None
    creationflags = 0
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return startupinfo, creationflags


def run_hidden_command(cmd: list[str], title: str = "執行命令") -> subprocess.CompletedProcess[str]:
    """隱藏命令視窗執行外部命令，並寫入安裝 log。"""
    write_install_log("=" * 72)
    write_install_log(title)
    write_install_log("執行：" + " ".join(cmd))

    startupinfo, creationflags = startup_options()
    result = subprocess.run(
        cmd,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        startupinfo=startupinfo,
        creationflags=creationflags,
    )
    write_install_log(result.stdout or "")
    write_install_log(f"結束碼：{result.returncode}")
    return result


def pip_module_available() -> bool:
    result = run_hidden_command([sys.executable, "-c", "import pip"], "檢查 pip 是否存在")
    return result.returncode == 0


def ensure_pip_available() -> None:
    """若 Python 沒有 pip，先用 ensurepip 自動補回。"""
    if is_frozen():
        return
    if pip_module_available():
        return

    write_install_log("pip 不存在，開始嘗試使用 ensurepip 補回 pip。")
    attempts = [
        [sys.executable, "-m", "ensurepip", "--upgrade", "--default-pip"],
        [sys.executable, "-m", "ensurepip", "--upgrade"],
    ]

    last_output = ""
    for cmd in attempts:
        result = run_hidden_command(cmd, "使用 ensurepip 安裝 pip")
        last_output = result.stdout or ""
        importlib.invalidate_caches()
        if result.returncode == 0 and pip_module_available():
            write_install_log("ensurepip 已成功補回 pip。")
            return

    log_path = pick_install_log_path()
    raise RuntimeError(
        "Python 目前沒有 pip，且自動執行 ensurepip 失敗。\n\n"
        "可手動打開命令提示字元執行：\n"
        f"{sys.executable} -m ensurepip --upgrade --default-pip\n"
        f"{sys.executable} -m pip install --upgrade pip setuptools wheel\n\n"
        f"安裝紀錄：{log_path}\n\n"
        "錯誤摘要：\n"
        + last_output[-1600:]
    )


def run_pip(args: list[str]) -> subprocess.CompletedProcess[str]:
    ensure_pip_available()
    return run_hidden_command([sys.executable, "-m", "pip", *args], "執行 pip")


def prepare_pip() -> None:
    global PIP_READY
    if PIP_READY or is_frozen():
        return
    ensure_pip_available()
    run_pip(["install", "--upgrade", "pip", "setuptools", "wheel"])
    PIP_READY = True


def install_package(import_name: str, pip_name: str) -> tuple[bool, str]:
    """source 模式嘗試安裝套件；frozen 模式不安裝，避免 exe -m pip 錯誤。"""
    if module_exists(import_name):
        return True, "已安裝"

    if is_frozen():
        return False, (
            f"打包後找不到 {import_name}。\n"
            "請確認 Nuitka 轉譯語法已包含相關 --include-package / --include-module 參數。"
        )

    prepare_pip()
    attempts = [
        ["install", "--upgrade", "--prefer-binary", "--no-cache-dir", pip_name],
        ["install", "--upgrade", "--only-binary=:all:", "--no-cache-dir", pip_name],
        ["install", "--upgrade", "--no-cache-dir", pip_name],
    ]

    last_output = ""
    for args in attempts:
        result = run_pip(args)
        last_output = result.stdout or ""
        importlib.invalidate_caches()
        if result.returncode == 0 and module_exists(import_name):
            return True, "安裝成功"
    return False, last_output[-1600:]


def ensure_basic_packages() -> None:
    failures: list[str] = []
    for import_name, pip_name in [("PIL", "pillow"), ("tkinterdnd2", "tkinterdnd2")]:
        ok, detail = install_package(import_name, pip_name)
        if not ok:
            failures.append(f"{pip_name}\n{detail}")

    if failures:
        raise RuntimeError(
            "以下必要套件無法使用：\n\n"
            + "\n\n".join(failures)
            + f"\n\n安裝/錯誤紀錄：{pick_install_log_path()}"
        )


def ensure_heif_decoder() -> None:
    if module_exists("pi_heif") or module_exists("pillow_heif"):
        return

    failures: list[str] = []
    for import_name, pip_name in [("pi_heif", "pi-heif"), ("pillow_heif", "pillow-heif")]:
        ok, detail = install_package(import_name, pip_name)
        if ok:
            return
        failures.append(f"{pip_name}\n{detail}")

    manual = (
        f"{sys.executable} -m ensurepip --upgrade --default-pip\n"
        f"{sys.executable} -m pip install --upgrade pip setuptools wheel\n"
        f"{sys.executable} -m pip install --upgrade pi-heif\n"
        f"{sys.executable} -m pip install --upgrade pillow-heif"
    )
    raise RuntimeError(
        "HEIF/HEIC 解碼套件無法使用。\n\n"
        "程式已先嘗試 pi-heif，再嘗試 pillow-heif。\n\n"
        "可手動執行：\n"
        f"{manual}\n\n"
        f"安裝紀錄：{pick_install_log_path()}\n\n"
        "錯誤摘要：\n" + "\n\n".join(failures)
    )


def ensure_required_packages() -> None:
    ensure_basic_packages()
    ensure_heif_decoder()


try:
    ensure_required_packages()
except Exception as exc:
    write_error_log("啟動失敗", f"{exc}\n\n{traceback.format_exc()}")
    notify_error("缺少套件", str(exc))
    sys.exit(1)

try:
    from PIL import Image, ImageFile
    from tkinterdnd2 import DND_FILES, TkinterDnD
except Exception as exc:
    write_error_log("匯入套件失敗", f"{exc}\n\n{traceback.format_exc()}")
    notify_error("匯入套件失敗", str(exc))
    sys.exit(1)

ImageFile.LOAD_TRUNCATED_IMAGES = True


def register_heif_backend() -> str:
    """註冊 Pillow 的 HEIF 開啟器；優先 pi-heif，失敗才使用 pillow-heif。"""
    last_error = ""
    for module_name, display_name in [("pi_heif", "pi-heif"), ("pillow_heif", "pillow-heif")]:
        try:
            module = importlib.import_module(module_name)
            register = getattr(module, "register_heif_opener")
            register()
            write_error_log("HEIF 解碼器", f"使用解碼器：{display_name}")
            return display_name
        except Exception as exc:
            last_error = f"{display_name} 註冊失敗：{exc}"
            write_error_log("HEIF 解碼器註冊失敗", f"{last_error}\n\n{traceback.format_exc()}")
    raise RuntimeError(f"無法註冊 HEIF 解碼器。{last_error}")


try:
    HEIF_BACKEND_NAME = register_heif_backend()
except Exception as exc:
    notify_error("HEIF 解碼器錯誤", str(exc))
    sys.exit(1)


def rounded_rect(canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, r: int = 18, **kwargs):
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


@dataclass(slots=True)
class ConvertResult:
    converted: int
    errors: list[str]
    elapsed: float


class HEIFtLifeApp:
    def __init__(self) -> None:
        self.root = TkinterDnD.Tk()
        self.root.title(f"{APP_NAME} {VERSION}")
        self.root.geometry("200x200")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.attributes("-topmost", True)

        self.canvas = tk.Canvas(self.root, width=200, height=200, bg=BG, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        self.status_after_id: str | None = None
        self.working_after_id: str | None = None
        self.text_id: int | None = None
        self.current_status = PROMPT_TEXT
        self.is_working = False
        self.drop_highlighted = False
        self.work_started_at = 0.0
        self.result_queue: queue.Queue[ConvertResult] = queue.Queue()

        self.draw_ui()
        self.bind_drop_targets()
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def bind_drop_targets(self) -> None:
        for widget in (self.root, self.canvas):
            try:
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<DropEnter>>", self.on_drop_enter)
                widget.dnd_bind("<<DropLeave>>", self.on_drop_leave)
                widget.dnd_bind("<<Drop>>", self.on_drop)
            except Exception as exc:
                write_error_log("拖曳註冊失敗", f"{exc}\n\n{traceback.format_exc()}")

    def draw_ui(self) -> None:
        self.canvas.delete("all")
        box_color = BLUE_ACTIVE if self.drop_highlighted else BLUE

        self.draw_dashed_round_box(30, 62, 170, 170, 14, box_color)
        self.draw_flip_icon(100, 103)

        self.text_id = self.canvas.create_text(
            100, 146, text=self.current_status, fill=box_color, font=("Helvetica", 14, "bold")
        )

    def draw_dashed_round_box(self, x1: int, y1: int, x2: int, y2: int, r: int, color: str) -> None:
        kwargs = dict(fill=color, width=2, dash=(8, 5))
        self.canvas.create_line(x1 + r, y1, x2 - r, y1, **kwargs)
        self.canvas.create_line(x1 + r, y2, x2 - r, y2, **kwargs)
        self.canvas.create_line(x1, y1 + r, x1, y2 - r, **kwargs)
        self.canvas.create_line(x2, y1 + r, x2, y2 - r, **kwargs)
        self.canvas.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, outline=color, width=2, style="arc")
        self.canvas.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, outline=color, width=2, style="arc")
        self.canvas.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, outline=color, width=2, style="arc")
        self.canvas.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, outline=color, width=2, style="arc")

    def draw_photo_icon(self, points: list[float], color: str, width: int = 3) -> None:
        self.canvas.create_polygon(points, outline=color, fill="", width=width, smooth=True)
        x_values = points[::2]
        y_values = points[1::2]
        min_x, max_x = min(x_values), max(x_values)
        min_y, max_y = min(y_values), max(y_values)
        w = max_x - min_x
        h = max_y - min_y
        self.canvas.create_oval(
            min_x + w * 0.58, min_y + h * 0.18,
            min_x + w * 0.74, min_y + h * 0.34,
            outline=color, width=width,
        )
        self.canvas.create_line(
            min_x + w * 0.10, min_y + h * 0.76,
            min_x + w * 0.35, min_y + h * 0.50,
            min_x + w * 0.52, min_y + h * 0.66,
            min_x + w * 0.73, min_y + h * 0.44,
            min_x + w * 0.94, min_y + h * 0.77,
            fill=color, width=width, smooth=True, capstyle="round", joinstyle="round",
        )

    def draw_flip_icon(self, cx: int, cy: int) -> None:
        self.canvas.create_arc(cx - 38, cy - 38, cx + 38, cy + 10, start=35, extent=120, outline=BLUE, width=4, style="arc")
        self.canvas.create_polygon(cx + 28, cy - 17, cx + 39, cy - 5, cx + 24, cy - 2, fill=BLUE, outline=BLUE)
        self.draw_photo_icon([cx - 55, cy - 4, cx - 12, cy - 17, cx - 1, cy + 22, cx - 45, cy + 34], BLUE_LIGHT)
        self.draw_photo_icon([cx - 5, cy - 2, cx + 44, cy + 5, cx + 36, cy + 42, cx - 13, cy + 35], BLUE)

    def set_status(self, text: str) -> None:
        self.current_status = text
        if self.text_id is not None:
            self.canvas.itemconfigure(self.text_id, text=text)

    def reset_status_later(self) -> None:
        if self.status_after_id:
            self.root.after_cancel(self.status_after_id)
        self.status_after_id = self.root.after(30000, lambda: self.set_status(PROMPT_TEXT))

    def set_drop_highlight(self, highlighted: bool) -> None:
        if self.drop_highlighted == highlighted:
            return
        self.drop_highlighted = highlighted
        self.draw_ui()

    def on_drop_enter(self, event) -> str | None:
        self.set_drop_highlight(True)
        return getattr(event, "action", None)

    def on_drop_leave(self, event) -> str | None:
        self.set_drop_highlight(False)
        return getattr(event, "action", None)

    def start_working_animation(self) -> None:
        self.is_working = True
        self.work_started_at = time.perf_counter()
        self.tick_working_animation()

    def tick_working_animation(self) -> None:
        if not self.is_working:
            return
        elapsed = int(time.perf_counter() - self.work_started_at)
        if elapsed >= 10:
            self.set_status(f"Working... {elapsed}s")
        else:
            self.set_status(WORKING_TEXT)
        self.working_after_id = self.root.after(500, self.tick_working_animation)

    def stop_working_animation(self) -> None:
        self.is_working = False
        if self.working_after_id:
            self.root.after_cancel(self.working_after_id)
            self.working_after_id = None

    def on_drop(self, event) -> None:
        self.set_drop_highlight(False)
        if self.is_working:
            self.set_status(WORKING_TEXT)
            return

        try:
            raw_files = self.root.tk.splitlist(event.data)
        except Exception:
            raw_files = [event.data]

        files = [Path(str(item).strip().strip('"')) for item in raw_files if str(item).strip()]
        if not files:
            return

        self.start_working_animation()
        worker = threading.Thread(target=self.convert_files_worker, args=(files,), daemon=True)
        worker.start()
        self.root.after(120, self.poll_result_queue)

    def poll_result_queue(self) -> None:
        try:
            result = self.result_queue.get_nowait()
        except queue.Empty:
            if self.is_working:
                self.root.after(120, self.poll_result_queue)
            return

        self.stop_working_animation()
        if result.converted:
            done_text = f"{DONE_TEXT} x {result.converted}" if result.converted > 1 else DONE_TEXT
            self.set_status(done_text)
            self.reset_status_later()
        else:
            self.set_status(ERROR_TEXT)
            self.reset_status_later()

        if result.errors:
            message = "\n".join(result.errors[:6])
            if len(result.errors) > 6:
                message += f"\n……另有 {len(result.errors) - 6} 筆錯誤，請看 log。"
            messagebox.showerror("轉檔失敗", message, parent=self.root)

    def convert_files_worker(self, files: list[Path]) -> None:
        started = time.perf_counter()
        converted = 0
        errors: list[str] = []

        write_error_log("開始轉檔", f"檔案數：{len(files)}\n解碼器：{HEIF_BACKEND_NAME}")
        for path in files:
            try:
                if path.suffix.lower() not in SUPPORTED_EXTS:
                    raise ValueError("只支援 .heif / .heic 檔案")
                if not path.exists():
                    raise FileNotFoundError("找不到檔案")
                out_path = path.with_name(f"{path.stem}_rt.jpg")
                self.convert_one(path, out_path)
                converted += 1
                write_error_log("轉檔成功", f"來源：{path}\n輸出：{out_path}")
            except Exception as exc:
                msg = f"{path.name}: {exc}"
                errors.append(msg)
                write_error_log("轉檔失敗", f"檔案：{path}\n錯誤：{exc}\n\n{traceback.format_exc()}")

        elapsed = time.perf_counter() - started
        write_error_log("轉檔結束", f"成功：{converted}\n錯誤：{len(errors)}\n耗時：{elapsed:.2f} 秒")
        self.result_queue.put(ConvertResult(converted=converted, errors=errors, elapsed=elapsed))

    @staticmethod
    def convert_one(src: Path, dst: Path) -> None:
        with Image.open(src) as img:
            # 讀完整影像後再轉色彩，避免部分 HEIC 延遲載入時路徑被鎖住。
            img.load()
            icc_profile = img.info.get("icc_profile")
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            save_kwargs = {"quality": 100, "subsampling": 0, "optimize": False}
            if icc_profile:
                save_kwargs["icc_profile"] = icc_profile
            img.save(dst, "JPEG", **save_kwargs)

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    try:
        HEIFtLifeApp().run()
    except Exception as exc:
        write_error_log("未預期錯誤", f"{exc}\n\n{traceback.format_exc()}")
        notify_error("程式錯誤", f"{exc}\n\n錯誤紀錄：{pick_error_log_path()}")
