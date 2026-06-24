# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import io
import json
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk
from tkinter import ttk

import cv2
import requests
from PIL import Image, ImageDraw, ImageFont, ImageTk


APP_TITLE = "中医药饮片智能检测与识别系统"
DEFAULT_SERVER_URL = "http://127.0.0.1:8868"
DEFAULT_CONF = 0.25
UPLOAD_MAX_SIDE = 1600
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
IMAGE_OUTPUT_DIR = OUTPUT_DIR / "images"
RECORD_OUTPUT_DIR = OUTPUT_DIR / "records"
RECORD_CSV = RECORD_OUTPUT_DIR / "records.csv"


@dataclass
class DetectRecord:
    timestamp: str
    source_type: str
    source_name: str
    total: int
    counts: dict[str, int]
    elapsed_ms: float | str
    device: str
    image_path: str


class HerbDetectClient:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1280x800")
        self.root.minsize(1100, 700)

        self.server_url_var = tk.StringVar(value=DEFAULT_SERVER_URL)
        self.conf_var = tk.DoubleVar(value=DEFAULT_CONF)
        self.camera_index_var = tk.IntVar(value=0)
        self.interval_var = tk.IntVar(value=800)
        self.service_var = tk.StringVar(value="服务未检测")
        self.model_var = tk.StringVar(value="模型：1500数据集 exp6_cbam_bifpn_decoupled / best.pt")
        self.device_var = tk.StringVar(value="设备：-")
        self.stat_total_var = tk.StringVar(value="0")
        self.stat_kind_var = tk.StringVar(value="0")
        self.stat_time_var = tk.StringVar(value="-")
        self.stat_fps_var = tk.StringVar(value="-")

        self.views: dict[str, ttk.Frame] = {}
        self.nav_buttons: dict[str, ttk.Button] = {}
        self.active_view = ""

        self.image_source_path: Path | None = None
        self.image_source: Image.Image | None = None
        self.image_annotated: Image.Image | None = None
        self.image_result: dict | None = None
        self.image_photo = None

        self.camera = None
        self.camera_running = False
        self.camera_infer_busy = False
        self.camera_frame = None
        self.camera_annotated = None
        self.camera_photo = None
        self.last_camera_infer_at = 0.0
        self.last_camera_record_at = 0.0

        self.records: list[DetectRecord] = []

        self._ensure_output_dirs()
        self._build_ui()
        self.load_records()
        self.show_view("图片识别")
        self.root.after(300, self.check_service)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    @property
    def server_url(self) -> str:
        return self.server_url_var.get().rstrip("/")

    def _ensure_output_dirs(self):
        IMAGE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        RECORD_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def _build_ui(self):
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1)

        header = ttk.Frame(self.root, padding=(16, 12, 16, 8))
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text=APP_TITLE, font=("Microsoft YaHei UI", 18, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(header, textvariable=self.model_var, foreground="#5b6770").grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Label(header, textvariable=self.service_var, foreground="#0f766e").grid(row=0, column=1, sticky="e")
        ttk.Button(header, text="检测服务", command=self.check_service).grid(row=1, column=1, sticky="e", pady=(4, 0))

        sidebar = ttk.Frame(self.root, padding=(12, 8, 10, 12))
        sidebar.grid(row=1, column=0, sticky="ns")
        for idx, name in enumerate(("实时检测", "图片识别", "盘点记录", "系统设置")):
            button = ttk.Button(sidebar, text=name, command=lambda n=name: self.show_view(n), width=16)
            button.grid(row=idx, column=0, sticky="ew", pady=(0, 8))
            self.nav_buttons[name] = button

        metrics = ttk.LabelFrame(sidebar, text="当前统计", padding=10)
        metrics.grid(row=5, column=0, sticky="ew", pady=(12, 0))
        self._metric(metrics, "目标数", self.stat_total_var, 0)
        self._metric(metrics, "类别数", self.stat_kind_var, 1)
        self._metric(metrics, "耗时", self.stat_time_var, 2)
        self._metric(metrics, "FPS", self.stat_fps_var, 3)
        ttk.Label(sidebar, textvariable=self.device_var, foreground="#5b6770", wraplength=150).grid(row=6, column=0, sticky="ew", pady=(12, 0))

        content = ttk.Frame(self.root, padding=(0, 0, 16, 12))
        content.grid(row=1, column=1, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        self._build_realtime_view(content)
        self._build_image_view(content)
        self._build_records_view(content)
        self._build_settings_view(content)

    def _metric(self, parent, label: str, var: tk.StringVar, row: int):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text=label, foreground="#5b6770").grid(row=0, column=0, sticky="w")
        ttk.Label(frame, textvariable=var, font=("Microsoft YaHei UI", 12, "bold")).grid(row=0, column=1, sticky="e")

    def _build_realtime_view(self, parent: ttk.Frame):
        view = ttk.Frame(parent)
        view.grid(row=0, column=0, sticky="nsew")
        view.columnconfigure(0, weight=3)
        view.columnconfigure(1, weight=1)
        view.rowconfigure(0, weight=1)
        self.views["实时检测"] = view

        self.camera_canvas = tk.Canvas(view, bg="#111827", highlightthickness=0)
        self.camera_canvas.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.camera_canvas.bind("<Configure>", lambda _event: self.refresh_camera_canvas())

        panel = ttk.Frame(view)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(3, weight=1)

        controls = ttk.LabelFrame(panel, text="摄像头控制", padding=12)
        controls.grid(row=0, column=0, sticky="ew")
        controls.columnconfigure(1, weight=1)
        ttk.Label(controls, text="摄像头").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(controls, from_=0, to=5, textvariable=self.camera_index_var, width=6).grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.start_camera_btn = ttk.Button(controls, text="开始实时检测", command=self.start_camera)
        self.start_camera_btn.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.stop_camera_btn = ttk.Button(controls, text="停止", command=self.stop_camera, state="disabled")
        self.stop_camera_btn.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(controls, text="保存当前画面", command=self.save_camera_snapshot).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        self.camera_counts_tree = self._result_tree(panel, "实时计数", height=8, row=1)
        self.camera_detail_tree = self._detail_tree(panel, "实时检测明细", row=3)

    def _build_image_view(self, parent: ttk.Frame):
        view = ttk.Frame(parent)
        view.grid(row=0, column=0, sticky="nsew")
        view.columnconfigure(0, weight=3)
        view.columnconfigure(1, weight=1)
        view.rowconfigure(0, weight=1)
        self.views["图片识别"] = view

        self.image_canvas = tk.Canvas(view, bg="#111827", highlightthickness=0)
        self.image_canvas.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.image_canvas.bind("<Configure>", lambda _event: self.refresh_image_canvas())

        panel = ttk.Frame(view)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(3, weight=1)

        controls = ttk.LabelFrame(panel, text="图片识别", padding=12)
        controls.grid(row=0, column=0, sticky="ew")
        controls.columnconfigure(0, weight=1)
        ttk.Button(controls, text="选择图片", command=self.open_image).grid(row=0, column=0, sticky="ew")
        self.detect_image_btn = ttk.Button(controls, text="开始识别", command=self.detect_selected_image, state="disabled")
        self.detect_image_btn.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.save_image_btn = ttk.Button(controls, text="保存带框图片", command=self.save_image_result, state="disabled")
        self.save_image_btn.grid(row=2, column=0, sticky="ew", pady=(8, 0))

        self.image_counts_tree = self._result_tree(panel, "分类计数", height=8, row=1)
        self.image_detail_tree = self._detail_tree(panel, "检测明细", row=3)

    def _build_records_view(self, parent: ttk.Frame):
        view = ttk.Frame(parent)
        view.grid(row=0, column=0, sticky="nsew")
        view.columnconfigure(0, weight=1)
        view.rowconfigure(1, weight=1)
        self.views["盘点记录"] = view

        toolbar = ttk.Frame(view)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        toolbar.columnconfigure(0, weight=1)
        ttk.Label(toolbar, text=f"记录文件：{RECORD_CSV}", foreground="#5b6770").grid(row=0, column=0, sticky="w")
        ttk.Button(toolbar, text="刷新", command=self.load_records).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(toolbar, text="导出CSV", command=self.export_records_csv).grid(row=0, column=2, padx=(8, 0))

        columns = ("time", "type", "source", "total", "counts", "elapsed", "device", "image")
        self.records_tree = ttk.Treeview(view, columns=columns, show="headings")
        headings = {
            "time": "时间",
            "type": "来源",
            "source": "文件/画面",
            "total": "目标数",
            "counts": "分类计数",
            "elapsed": "耗时",
            "device": "设备",
            "image": "结果图",
        }
        widths = {"time": 150, "type": 80, "source": 160, "total": 70, "counts": 260, "elapsed": 80, "device": 80, "image": 240}
        for col in columns:
            self.records_tree.heading(col, text=headings[col])
            self.records_tree.column(col, width=widths[col], anchor="w")
        self.records_tree.grid(row=1, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(view, orient="vertical", command=self.records_tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.records_tree.configure(yscrollcommand=scrollbar.set)

    def _build_settings_view(self, parent: ttk.Frame):
        view = ttk.Frame(parent)
        view.grid(row=0, column=0, sticky="nsew")
        view.columnconfigure(0, weight=1)
        self.views["系统设置"] = view

        server_box = ttk.LabelFrame(view, text="后端服务", padding=14)
        server_box.grid(row=0, column=0, sticky="ew")
        server_box.columnconfigure(1, weight=1)
        ttk.Label(server_box, text="服务地址").grid(row=0, column=0, sticky="w")
        ttk.Entry(server_box, textvariable=self.server_url_var).grid(row=0, column=1, sticky="ew", padx=(10, 0))
        ttk.Button(server_box, text="检测连接", command=self.check_service).grid(row=0, column=2, padx=(10, 0))
        ttk.Label(server_box, text="本地默认端口固定为 8868，后续网页端可以复用同一个后端接口。", foreground="#5b6770").grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(8, 0)
        )

        infer_box = ttk.LabelFrame(view, text="推理参数", padding=14)
        infer_box.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        infer_box.columnconfigure(1, weight=1)
        ttk.Label(infer_box, text="置信度阈值").grid(row=0, column=0, sticky="w")
        ttk.Scale(infer_box, from_=0.05, to=0.90, variable=self.conf_var, command=lambda _v: self.update_conf_text()).grid(
            row=0, column=1, sticky="ew", padx=(10, 10)
        )
        self.conf_text = ttk.Label(infer_box, text=f"{self.conf_var.get():.2f}", width=6)
        self.conf_text.grid(row=0, column=2, sticky="e")
        ttk.Label(infer_box, text="实时检测间隔(ms)").grid(row=1, column=0, sticky="w", pady=(10, 0))
        ttk.Spinbox(infer_box, from_=200, to=3000, increment=100, textvariable=self.interval_var, width=10).grid(
            row=1, column=1, sticky="w", padx=(10, 0), pady=(10, 0)
        )

        info_box = ttk.LabelFrame(view, text="运行说明", padding=14)
        info_box.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        info = (
            "1. 先运行 start_local_client.bat，它会启动 127.0.0.1:8868 后端并打开本客户端。\n"
            "2. 图片识别适合单张饮片图片上传、定位、分类和计数。\n"
            "3. 实时检测会调用 Windows 摄像头，并按设定间隔把画面发送到本地后端推理。\n"
            "4. 盘点记录会保存识别时间、分类计数、耗时、设备和带框结果图。"
        )
        ttk.Label(info_box, text=info, justify="left", foreground="#374151").grid(row=0, column=0, sticky="w")

    def _result_tree(self, parent: ttk.Frame, title: str, height: int, row: int) -> ttk.Treeview:
        box = ttk.LabelFrame(parent, text=title, padding=10)
        box.grid(row=row, column=0, sticky="nsew", pady=(12, 0))
        box.columnconfigure(0, weight=1)
        tree = ttk.Treeview(box, columns=("name", "count"), show="headings", height=height)
        tree.heading("name", text="类别")
        tree.heading("count", text="数量")
        tree.column("name", width=150, anchor="w")
        tree.column("count", width=70, anchor="center")
        tree.grid(row=0, column=0, sticky="nsew")
        return tree

    def _detail_tree(self, parent: ttk.Frame, title: str, row: int) -> ttk.Treeview:
        box = ttk.LabelFrame(parent, text=title, padding=10)
        box.grid(row=row, column=0, sticky="nsew", pady=(12, 0))
        box.columnconfigure(0, weight=1)
        box.rowconfigure(0, weight=1)
        tree = ttk.Treeview(box, columns=("name", "conf", "box"), show="headings")
        tree.heading("name", text="类别")
        tree.heading("conf", text="置信度")
        tree.heading("box", text="定位框")
        tree.column("name", width=120, anchor="w")
        tree.column("conf", width=70, anchor="center")
        tree.column("box", width=180, anchor="w")
        tree.grid(row=0, column=0, sticky="nsew")
        return tree

    def show_view(self, name: str):
        self.active_view = name
        for view_name, frame in self.views.items():
            if view_name == name:
                frame.tkraise()
        for view_name, button in self.nav_buttons.items():
            button.state(["pressed"] if view_name == name else ["!pressed"])

    def update_conf_text(self):
        self.conf_text.config(text=f"{self.conf_var.get():.2f}")

    def check_service(self):
        self.service_var.set("正在检测服务...")

        def worker():
            try:
                response = requests.get(f"{self.server_url}/api/health", timeout=4)
                response.raise_for_status()
                data = response.json()
            except Exception as exc:
                self.root.after(0, lambda: self.service_var.set(f"服务连接失败：{exc}"))
                return
            model = str(data.get("model", ""))
            device = str(data.get("device", "-"))
            self.root.after(0, lambda: self.service_var.set(f"服务正常：{self.server_url}"))
            self.root.after(
                0,
                lambda: self.model_var.set(f"模型：1500数据集 exp6_cbam_bifpn_decoupled / {Path(model).name or 'best.pt'}"),
            )
            self.root.after(0, lambda: self.device_var.set(f"设备：{device}"))

        threading.Thread(target=worker, daemon=True).start()

    def open_image(self):
        path = filedialog.askopenfilename(
            title="选择饮片图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.webp"), ("所有文件", "*.*")],
        )
        if not path:
            return
        try:
            self.image_source_path = Path(path)
            self.image_source = Image.open(path).convert("RGB")
        except Exception as exc:
            messagebox.showerror("图片打开失败", str(exc))
            return
        self.image_annotated = None
        self.image_result = None
        self.detect_image_btn.config(state="normal")
        self.save_image_btn.config(state="disabled")
        self.clear_tree(self.image_counts_tree)
        self.clear_tree(self.image_detail_tree)
        self.refresh_image_canvas()

    def detect_selected_image(self):
        if self.image_source is None or self.image_source_path is None:
            messagebox.showinfo("提示", "请先选择图片。")
            return
        self.detect_image_btn.config(state="disabled")
        self.service_var.set("正在进行图片识别...")

        def worker():
            try:
                image_bytes, scale_x, scale_y = self.encode_for_upload(self.image_source)
                result = self.call_detect(image_bytes, self.image_source_path.name)
                result = self.scale_detection_boxes(result, scale_x, scale_y)
                annotated = self.draw_detections(self.image_source, result["detections"])
                image_path = self.save_annotated_file(annotated, "image")
                self.append_record("图片识别", self.image_source_path.name, result, image_path)
            except Exception as exc:
                self.root.after(0, lambda: messagebox.showerror("识别失败", str(exc)))
                self.root.after(0, lambda: self.service_var.set("图片识别失败"))
                self.root.after(0, lambda: self.detect_image_btn.config(state="normal"))
                return
            self.root.after(0, lambda: self.show_image_result(result, annotated))

        threading.Thread(target=worker, daemon=True).start()

    def call_detect(self, image_bytes: bytes, filename: str) -> dict:
        files = {"file": (filename, image_bytes, "image/jpeg")}
        data = {"conf": f"{self.conf_var.get():.2f}"}
        response = requests.post(f"{self.server_url}/api/detect", files=files, data=data, timeout=120)
        response.raise_for_status()
        result = response.json()
        if result.get("status") != "ok":
            raise RuntimeError(result.get("message", "后端返回异常"))
        return result

    def encode_for_upload(self, image: Image.Image) -> tuple[bytes, float, float]:
        upload_image = image.convert("RGB").copy()
        original_w, original_h = upload_image.size
        upload_image.thumbnail((UPLOAD_MAX_SIDE, UPLOAD_MAX_SIDE), Image.Resampling.LANCZOS)
        upload_w, upload_h = upload_image.size
        buffer = io.BytesIO()
        upload_image.save(buffer, format="JPEG", quality=88, optimize=True)
        scale_x = original_w / upload_w
        scale_y = original_h / upload_h
        return buffer.getvalue(), scale_x, scale_y

    def scale_detection_boxes(self, result: dict, scale_x: float, scale_y: float) -> dict:
        if scale_x == 1 and scale_y == 1:
            return result
        for item in result.get("detections", []):
            x1, y1, x2, y2 = item.get("box", [0, 0, 0, 0])
            item["box"] = [x1 * scale_x, y1 * scale_y, x2 * scale_x, y2 * scale_y]
        if self.image_source is not None:
            result["image"] = {"width": self.image_source.width, "height": self.image_source.height}
        return result

    def show_image_result(self, result: dict, annotated: Image.Image):
        self.image_result = result
        self.image_annotated = annotated
        self.update_stats(result)
        self.fill_result_trees(self.image_counts_tree, self.image_detail_tree, result)
        self.detect_image_btn.config(state="normal")
        self.save_image_btn.config(state="normal")
        self.service_var.set(f"图片识别完成：{result.get('total', 0)} 个目标")
        self.refresh_image_canvas()
        self.refresh_records_table()

    def start_camera(self):
        if self.camera_running:
            return
        index = self.camera_index_var.get()
        camera = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not camera.isOpened():
            camera.release()
            messagebox.showerror("摄像头打开失败", f"无法打开摄像头 {index}。")
            return
        self.camera = camera
        self.camera_running = True
        self.camera_infer_busy = False
        self.last_camera_infer_at = 0.0
        self.start_camera_btn.config(state="disabled")
        self.stop_camera_btn.config(state="normal")
        self.service_var.set("实时检测已启动")
        self.root.after(20, self.camera_loop)

    def stop_camera(self):
        self.camera_running = False
        self.camera_infer_busy = False
        if self.camera is not None:
            self.camera.release()
        self.camera = None
        self.start_camera_btn.config(state="normal")
        self.stop_camera_btn.config(state="disabled")
        self.service_var.set("实时检测已停止")

    def camera_loop(self):
        if not self.camera_running or self.camera is None:
            return
        ok, frame = self.camera.read()
        if ok:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.camera_frame = Image.fromarray(frame)
            if self.camera_annotated is None:
                self.camera_annotated = self.camera_frame
            now = time.perf_counter()
            interval = max(200, self.interval_var.get()) / 1000
            if not self.camera_infer_busy and now - self.last_camera_infer_at >= interval:
                self.last_camera_infer_at = now
                self.infer_camera_frame(self.camera_frame.copy())
            self.refresh_camera_canvas()
        self.root.after(30, self.camera_loop)

    def infer_camera_frame(self, frame: Image.Image):
        self.camera_infer_busy = True

        def worker():
            started = time.perf_counter()
            try:
                buffer = io.BytesIO()
                frame.save(buffer, format="JPEG", quality=82)
                result = self.call_detect(buffer.getvalue(), "camera.jpg")
                annotated = self.draw_detections(frame, result["detections"])
                fps = 1000 / max(float(result.get("elapsed_ms", 0.1)), 0.1)
                now = time.perf_counter()
                if result.get("total", 0) > 0 and now - self.last_camera_record_at > 5:
                    image_path = self.save_annotated_file(annotated, "camera")
                    self.append_record("实时检测", "camera", result, image_path)
                    self.last_camera_record_at = now
            except Exception as exc:
                self.root.after(0, lambda: self.service_var.set(f"实时检测失败：{exc}"))
                self.root.after(0, self.finish_camera_infer)
                return
            elapsed = time.perf_counter() - started
            self.root.after(0, lambda: self.show_camera_result(result, annotated, fps, elapsed))

        threading.Thread(target=worker, daemon=True).start()

    def show_camera_result(self, result: dict, annotated: Image.Image, fps: float, _elapsed: float):
        self.camera_annotated = annotated
        self.update_stats(result, fps=fps)
        self.fill_result_trees(self.camera_counts_tree, self.camera_detail_tree, result)
        self.service_var.set(f"实时检测中：{result.get('total', 0)} 个目标")
        self.refresh_camera_canvas()
        self.refresh_records_table()
        self.finish_camera_infer()

    def finish_camera_infer(self):
        self.camera_infer_busy = False

    def save_camera_snapshot(self):
        if self.camera_annotated is None:
            messagebox.showinfo("提示", "当前没有可保存的实时检测画面。")
            return
        path = self.save_annotated_file(self.camera_annotated, "camera_manual")
        messagebox.showinfo("保存成功", f"已保存：{path}")

    def save_image_result(self):
        if self.image_annotated is None:
            messagebox.showinfo("提示", "请先完成图片识别。")
            return
        path = filedialog.asksaveasfilename(
            title="保存带框图片",
            defaultextension=".jpg",
            filetypes=[("JPEG 图片", "*.jpg"), ("PNG 图片", "*.png")],
        )
        if not path:
            return
        self.image_annotated.save(path)
        messagebox.showinfo("保存成功", f"已保存：{path}")

    def save_annotated_file(self, image: Image.Image, prefix: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = IMAGE_OUTPUT_DIR / f"{prefix}_{timestamp}.jpg"
        image.save(path, quality=92)
        return str(path)

    def append_record(self, source_type: str, source_name: str, result: dict, image_path: str):
        record = DetectRecord(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            source_type=source_type,
            source_name=source_name,
            total=int(result.get("total", 0)),
            counts=dict(result.get("counts", {})),
            elapsed_ms=result.get("elapsed_ms", "-"),
            device=str(result.get("device", "-")),
            image_path=image_path,
        )
        self.records.append(record)
        write_header = not RECORD_CSV.exists()
        with RECORD_CSV.open("a", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            if write_header:
                writer.writerow(["time", "source_type", "source_name", "total", "counts", "elapsed_ms", "device", "image_path"])
            writer.writerow(
                [
                    record.timestamp,
                    record.source_type,
                    record.source_name,
                    record.total,
                    json.dumps(record.counts, ensure_ascii=False),
                    record.elapsed_ms,
                    record.device,
                    record.image_path,
                ]
            )

    def load_records(self):
        self.records = []
        if RECORD_CSV.exists():
            with RECORD_CSV.open("r", newline="", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        counts = json.loads(row.get("counts", "{}"))
                    except json.JSONDecodeError:
                        counts = {}
                    self.records.append(
                        DetectRecord(
                            timestamp=row.get("time", ""),
                            source_type=row.get("source_type", ""),
                            source_name=row.get("source_name", ""),
                            total=int(row.get("total") or 0),
                            counts=counts,
                            elapsed_ms=row.get("elapsed_ms", "-"),
                            device=row.get("device", "-"),
                            image_path=row.get("image_path", ""),
                        )
                    )
        self.refresh_records_table()

    def export_records_csv(self):
        if not RECORD_CSV.exists():
            messagebox.showinfo("提示", "还没有盘点记录。")
            return
        path = filedialog.asksaveasfilename(
            title="导出盘点记录",
            defaultextension=".csv",
            filetypes=[("CSV 文件", "*.csv")],
        )
        if not path:
            return
        Path(path).write_bytes(RECORD_CSV.read_bytes())
        messagebox.showinfo("导出成功", f"已导出：{path}")

    def refresh_records_table(self):
        if not hasattr(self, "records_tree"):
            return
        self.clear_tree(self.records_tree)
        for record in reversed(self.records):
            self.records_tree.insert(
                "",
                "end",
                values=(
                    record.timestamp,
                    record.source_type,
                    record.source_name,
                    record.total,
                    self.format_counts(record.counts),
                    record.elapsed_ms,
                    record.device,
                    record.image_path,
                ),
            )

    def update_stats(self, result: dict, fps: float | None = None):
        counts = result.get("counts", {})
        self.stat_total_var.set(str(result.get("total", 0)))
        self.stat_kind_var.set(str(len(counts)))
        self.stat_time_var.set(f"{result.get('elapsed_ms', '-')}ms")
        self.device_var.set(f"设备：{result.get('device', '-')}")
        if fps is not None:
            self.stat_fps_var.set(f"{fps:.1f}")

    def fill_result_trees(self, counts_tree: ttk.Treeview, detail_tree: ttk.Treeview, result: dict):
        counts = result.get("counts", {})
        self.clear_tree(counts_tree)
        for name, count in sorted(counts.items()):
            counts_tree.insert("", "end", values=(name, count))
        self.clear_tree(detail_tree)
        for item in result.get("detections", []):
            box = ", ".join(str(int(float(v))) for v in item.get("box", []))
            conf = f"{float(item.get('confidence', 0)) * 100:.1f}%"
            detail_tree.insert("", "end", values=(item.get("name", "-"), conf, box))

    def clear_tree(self, tree: ttk.Treeview):
        for item in tree.get_children():
            tree.delete(item)

    def draw_detections(self, image: Image.Image, detections: list[dict]) -> Image.Image:
        output = image.convert("RGB").copy()
        draw = ImageDraw.Draw(output)
        line_width = max(2, int(min(output.size) / 220))
        try:
            font = ImageFont.truetype("msyh.ttc", max(14, int(min(output.size) / 40)))
        except OSError:
            font = ImageFont.load_default()
        colors = [(22, 163, 74), (37, 99, 235), (217, 119, 6), (190, 18, 60), (124, 58, 237)]
        for idx, item in enumerate(detections):
            x1, y1, x2, y2 = [float(v) for v in item["box"]]
            color = colors[idx % len(colors)]
            label = f"{item['name']} {float(item['confidence']) * 100:.1f}%"
            draw.rectangle((x1, y1, x2, y2), outline=color, width=line_width)
            bbox = draw.textbbox((0, 0), label, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            label_y = max(0, y1 - text_h - 8)
            draw.rectangle((x1, label_y, x1 + text_w + 10, label_y + text_h + 8), fill=color)
            draw.text((x1 + 5, label_y + 4), label, fill=(255, 255, 255), font=font)
        return output

    def refresh_image_canvas(self):
        image = self.image_annotated or self.image_source
        self.render_to_canvas(self.image_canvas, image, "请选择图片进行识别", "image_photo")

    def refresh_camera_canvas(self):
        image = self.camera_annotated or self.camera_frame
        self.render_to_canvas(self.camera_canvas, image, "请点击开始实时检测", "camera_photo")

    def render_to_canvas(self, canvas: tk.Canvas, image: Image.Image | None, empty_text: str, photo_attr: str):
        canvas.delete("all")
        width = max(canvas.winfo_width(), 1)
        height = max(canvas.winfo_height(), 1)
        if image is None:
            canvas.create_text(width // 2, height // 2, text=empty_text, fill="#d1d5db", font=("Microsoft YaHei UI", 16))
            return
        preview = image.copy()
        preview.thumbnail((width, height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(preview)
        setattr(self, photo_attr, photo)
        canvas.create_image(width // 2, height // 2, image=photo, anchor="center")

    def format_counts(self, counts: dict[str, int]) -> str:
        if not counts:
            return "-"
        return "；".join(f"{name}:{count}" for name, count in sorted(counts.items()))

    def on_close(self):
        self.stop_camera()
        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        style = ttk.Style(root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except tk.TclError:
        pass
    HerbDetectClient(root)
    root.mainloop()


if __name__ == "__main__":
    main()
