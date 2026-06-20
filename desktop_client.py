# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

import constant
from detect_core import DEFAULT_CONF, MODEL_PATH, draw_detections, load_model, predict_image


class HerbDetectClient:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("中医药饮片智能检测与识别系统")
        self.root.geometry("1180x760")
        self.root.minsize(980, 640)

        self.model = None
        self.source_image: Image.Image | None = None
        self.annotated_image: Image.Image | None = None
        self.source_path: Path | None = None
        self.result: dict | None = None
        self.preview_photo = None

        self.conf_var = tk.DoubleVar(value=DEFAULT_CONF)
        self.status_var = tk.StringVar(value="正在加载 exp2_bifpn 模型...")
        self.total_var = tk.StringVar(value="0")
        self.kind_var = tk.StringVar(value="0")
        self.time_var = tk.StringVar(value="-")

        self._build_ui()
        self.root.after(100, self._load_model_async)

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        header = ttk.Frame(self.root, padding=(14, 12, 14, 8))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        title = ttk.Label(header, text="中医药饮片智能检测与识别系统", font=("Microsoft YaHei UI", 18, "bold"))
        title.grid(row=0, column=0, sticky="w")
        subtitle = ttk.Label(
            header,
            text=f"模型：exp2_bifpn | 权重：{MODEL_PATH}",
            foreground="#66736c",
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))

        body = ttk.Frame(self.root, padding=(14, 0, 14, 10))
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        image_panel = ttk.Frame(body)
        image_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        image_panel.columnconfigure(0, weight=1)
        image_panel.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(image_panel, bg="#151a18", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda _event: self._refresh_preview())

        side = ttk.Frame(body)
        side.grid(row=0, column=1, sticky="nsew")
        side.columnconfigure(0, weight=1)
        side.rowconfigure(5, weight=1)

        controls = ttk.LabelFrame(side, text="识别控制", padding=12)
        controls.grid(row=0, column=0, sticky="ew")
        controls.columnconfigure(0, weight=1)

        ttk.Button(controls, text="上传图片", command=self.open_image).grid(row=0, column=0, sticky="ew")
        self.detect_btn = ttk.Button(controls, text="开始识别", command=self.detect_current_image, state="disabled")
        self.detect_btn.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.save_btn = ttk.Button(controls, text="导出盘点结果", command=self.export_csv, state="disabled")
        self.save_btn.grid(row=2, column=0, sticky="ew", pady=(8, 0))

        ttk.Label(controls, text="置信度阈值").grid(row=3, column=0, sticky="w", pady=(12, 0))
        conf_row = ttk.Frame(controls)
        conf_row.grid(row=4, column=0, sticky="ew", pady=(4, 0))
        conf_row.columnconfigure(0, weight=1)
        ttk.Scale(conf_row, from_=0.10, to=0.80, variable=self.conf_var, command=self._update_conf_label).grid(
            row=0, column=0, sticky="ew"
        )
        self.conf_label = ttk.Label(conf_row, text=f"{DEFAULT_CONF:.2f}", width=5)
        self.conf_label.grid(row=0, column=1, sticky="e", padx=(8, 0))

        metrics = ttk.LabelFrame(side, text="盘点概览", padding=12)
        metrics.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        metrics.columnconfigure((0, 1, 2), weight=1)
        self._metric(metrics, "目标数", self.total_var, 0)
        self._metric(metrics, "种类数", self.kind_var, 1)
        self._metric(metrics, "耗时", self.time_var, 2)

        counts_box = ttk.LabelFrame(side, text="分类计数", padding=10)
        counts_box.grid(row=2, column=0, sticky="nsew", pady=(12, 0))
        counts_box.columnconfigure(0, weight=1)
        counts_box.rowconfigure(0, weight=1)
        self.counts_tree = ttk.Treeview(counts_box, columns=("name", "count"), show="headings", height=8)
        self.counts_tree.heading("name", text="类别")
        self.counts_tree.heading("count", text="数量")
        self.counts_tree.column("name", width=130, anchor="w")
        self.counts_tree.column("count", width=60, anchor="center")
        self.counts_tree.grid(row=0, column=0, sticky="nsew")

        detail_box = ttk.LabelFrame(side, text="检测明细", padding=10)
        detail_box.grid(row=5, column=0, sticky="nsew", pady=(12, 0))
        detail_box.columnconfigure(0, weight=1)
        detail_box.rowconfigure(0, weight=1)
        self.detail_tree = ttk.Treeview(detail_box, columns=("name", "conf", "box"), show="headings")
        self.detail_tree.heading("name", text="类别")
        self.detail_tree.heading("conf", text="置信度")
        self.detail_tree.heading("box", text="定位框")
        self.detail_tree.column("name", width=100, anchor="w")
        self.detail_tree.column("conf", width=70, anchor="center")
        self.detail_tree.column("box", width=180, anchor="w")
        self.detail_tree.grid(row=0, column=0, sticky="nsew")

        footer = ttk.Frame(self.root, padding=(14, 0, 14, 12))
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status_var, foreground="#66736c").grid(row=0, column=0, sticky="w")

    def _metric(self, parent, label: str, value_var: tk.StringVar, column: int):
        frame = ttk.Frame(parent, padding=6)
        frame.grid(row=0, column=column, sticky="ew")
        ttk.Label(frame, textvariable=value_var, font=("Microsoft YaHei UI", 16, "bold")).pack()
        ttk.Label(frame, text=label, foreground="#66736c").pack()

    def _load_model_async(self):
        def worker():
            try:
                self.model = load_model()
                self.root.after(0, lambda: self.status_var.set("模型加载完成，请上传饮片图片。"))
            except Exception as exc:
                self.root.after(0, lambda: messagebox.showerror("模型加载失败", str(exc)))
                self.root.after(0, lambda: self.status_var.set("模型加载失败。"))

        threading.Thread(target=worker, daemon=True).start()

    def _update_conf_label(self, _value=None):
        self.conf_label.config(text=f"{self.conf_var.get():.2f}")

    def open_image(self):
        path = filedialog.askopenfilename(
            title="选择饮片图片",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.webp"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return

        try:
            self.source_path = Path(path)
            self.source_image = Image.open(path).convert("RGB")
        except Exception as exc:
            messagebox.showerror("图片打开失败", str(exc))
            return

        self.annotated_image = None
        self.result = None
        self._clear_results()
        self.detect_btn.config(state="normal" if self.model else "disabled")
        self.save_btn.config(state="disabled")
        self.status_var.set(f"已上传图片：{self.source_path.name}")
        self._refresh_preview()

    def detect_current_image(self):
        if self.model is None:
            messagebox.showinfo("提示", "模型仍在加载，请稍后。")
            return
        if self.source_image is None:
            messagebox.showinfo("提示", "请先上传图片。")
            return

        self.detect_btn.config(state="disabled")
        self.save_btn.config(state="disabled")
        self.status_var.set("正在识别，请稍候...")

        def worker():
            try:
                result = predict_image(self.model, self.source_image, self.conf_var.get())
                annotated = draw_detections(self.source_image, result["detections"])
            except Exception as exc:
                self.root.after(0, lambda: messagebox.showerror("识别失败", str(exc)))
                self.root.after(0, lambda: self.status_var.set("识别失败。"))
                self.root.after(0, lambda: self.detect_btn.config(state="normal"))
                return
            self.root.after(0, lambda: self._show_result(result, annotated))

        threading.Thread(target=worker, daemon=True).start()

    def _show_result(self, result: dict, annotated: Image.Image):
        self.result = result
        self.annotated_image = annotated
        self.total_var.set(str(result["total"]))
        self.kind_var.set(str(len(result["counts"])))
        self.time_var.set(f"{result['elapsed_ms']}ms")

        self._fill_tree(self.counts_tree, [(name, count) for name, count in sorted(result["counts"].items())])
        detail_rows = []
        for item in result["detections"]:
            box = ", ".join(str(int(v)) for v in item["box"])
            detail_rows.append((item["name"], f"{item['confidence'] * 100:.1f}%", box))
        self._fill_tree(self.detail_tree, detail_rows)

        self.detect_btn.config(state="normal")
        self.save_btn.config(state="normal" if result["detections"] else "disabled")
        self.status_var.set(f"识别完成：共 {result['total']} 个目标，{len(result['counts'])} 类饮片。")
        self._refresh_preview()

    def _fill_tree(self, tree: ttk.Treeview, rows):
        for item in tree.get_children():
            tree.delete(item)
        for row in rows:
            tree.insert("", "end", values=row)

    def _clear_results(self):
        self.total_var.set("0")
        self.kind_var.set("0")
        self.time_var.set("-")
        self._fill_tree(self.counts_tree, [])
        self._fill_tree(self.detail_tree, [])

    def _refresh_preview(self):
        image = self.annotated_image or self.source_image
        self.canvas.delete("all")
        if image is None:
            self.canvas.create_text(
                self.canvas.winfo_width() / 2,
                self.canvas.winfo_height() / 2,
                text="上传饮片图片后开始识别",
                fill="#d9e4de",
                font=("Microsoft YaHei UI", 16),
            )
            return

        canvas_w = max(1, self.canvas.winfo_width())
        canvas_h = max(1, self.canvas.winfo_height())
        preview = image.copy()
        preview.thumbnail((canvas_w - 24, canvas_h - 24), Image.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(preview)
        x = canvas_w // 2
        y = canvas_h // 2
        self.canvas.create_image(x, y, image=self.preview_photo, anchor="center")

    def export_csv(self):
        if not self.result or not self.source_path:
            return

        default_name = f"inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path = filedialog.asksaveasfilename(
            title="导出盘点结果",
            initialfile=default_name,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(["source_image", self.source_path])
                writer.writerow(["model", MODEL_PATH])
                writer.writerow(["confidence_threshold", self.result["conf"]])
                writer.writerow([])
                writer.writerow(["category", "count"])
                for name, count in sorted(self.result["counts"].items()):
                    writer.writerow([name, count])
                writer.writerow([])
                writer.writerow(["category", "confidence", "x1", "y1", "x2", "y2"])
                for item in self.result["detections"]:
                    writer.writerow([item["name"], item["confidence"], *item["box"]])
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))
            return

        self.status_var.set(f"盘点结果已导出：{path}")


def main():
    root = tk.Tk()
    try:
        root.call("source", "azure.tcl")
        root.call("set_theme", "light")
    except tk.TclError:
        pass
    HerbDetectClient(root)
    root.mainloop()


if __name__ == "__main__":
    main()
