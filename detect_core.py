# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont
import torch

import constant


BASE_DIR = Path(__file__).resolve().parent
LOCAL_ULTRALYTICS_DIR = BASE_DIR / "ultralytics"
os.environ.setdefault("YOLO_CONFIG_DIR", str(BASE_DIR / ".ultralytics"))
if LOCAL_ULTRALYTICS_DIR.exists() and str(LOCAL_ULTRALYTICS_DIR) not in sys.path:
    sys.path.insert(0, str(LOCAL_ULTRALYTICS_DIR))

from ultralytics import YOLO


MODEL_PATH = (
    BASE_DIR
    / "res1500"
    / "detect"
    / "exp6_cbam_bifpn_decoupled_gpu_20260621_180615"
    / "weights"
    / "best.pt"
)
DEFAULT_CONF = 0.25
DEFAULT_IMGSZ = 640
DEFAULT_OVERLAP_IOU = 0.55
INFERENCE_DEVICE = 0 if torch.cuda.is_available() else "cpu"
USE_HALF = torch.cuda.is_available()


def load_model(model_path: Path = MODEL_PATH) -> YOLO:
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    model = YOLO(str(model_path))
    if torch.cuda.is_available():
        warmup_image = Image.new("RGB", (DEFAULT_IMGSZ, DEFAULT_IMGSZ), (0, 0, 0))
        model.predict(
            warmup_image,
            imgsz=DEFAULT_IMGSZ,
            conf=DEFAULT_CONF,
            device=INFERENCE_DEVICE,
            half=USE_HALF,
            verbose=False,
        )
    return model


def clamp_conf(conf: float | str | None) -> float:
    if conf is None:
        return DEFAULT_CONF
    try:
        value = float(conf)
    except (TypeError, ValueError):
        return DEFAULT_CONF
    return min(max(value, 0.01), 0.95)


def box_iou(box_a: list[float], box_b: list[float]) -> float:
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter_area
    return inter_area / union if union > 0 else 0.0


def suppress_overlapping_detections(
    detections: list[dict[str, Any]],
    iou_threshold: float = DEFAULT_OVERLAP_IOU,
) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    for item in sorted(detections, key=lambda det: det["confidence"], reverse=True):
        if all(box_iou(item["box"], kept_item["box"]) < iou_threshold for kept_item in kept):
            kept.append(item)
    return kept


def predict_image(model: YOLO, image: Image.Image, conf: float | str | None = None) -> dict[str, Any]:
    rgb_image = image.convert("RGB")
    threshold = clamp_conf(conf)
    started = time.perf_counter()
    results = model.predict(
        rgb_image,
        imgsz=DEFAULT_IMGSZ,
        conf=threshold,
        device=INFERENCE_DEVICE,
        half=USE_HALF,
        verbose=False,
    )
    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)

    detections = []
    result = results[0]
    for box in result.boxes:
        cls_id = int(box.cls[0])
        name = constant.CLASS_NAMES[cls_id] if cls_id < len(constant.CLASS_NAMES) else str(cls_id)
        confidence = round(float(box.conf[0]), 4)
        x1, y1, x2, y2 = [round(float(v), 2) for v in box.xyxy[0]]
        detections.append(
            {
                "class_id": cls_id,
                "name": name,
                "confidence": confidence,
                "box": [x1, y1, x2, y2],
            }
        )

    detections = suppress_overlapping_detections(detections)
    counts: dict[str, int] = {}
    for item in detections:
        name = item["name"]
        counts[name] = counts.get(name, 0) + 1

    return {
        "image": {"width": rgb_image.width, "height": rgb_image.height},
        "detections": detections,
        "counts": counts,
        "total": len(detections),
        "elapsed_ms": elapsed_ms,
        "conf": threshold,
    }


def draw_detections(image: Image.Image, detections: list[dict[str, Any]]) -> Image.Image:
    output = image.convert("RGB").copy()
    draw = ImageDraw.Draw(output)
    line_width = max(2, int(min(output.size) / 220))
    try:
        font = ImageFont.truetype("arial.ttf", max(14, int(min(output.size) / 38)))
    except OSError:
        font = ImageFont.load_default()

    for item in detections:
        x1, y1, x2, y2 = item["box"]
        label = f"{item['name']} {item['confidence'] * 100:.1f}%"
        draw.rectangle((x1, y1, x2, y2), outline=(24, 150, 94), width=line_width)
        bbox = draw.textbbox((0, 0), label, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        label_y = max(0, y1 - text_h - 8)
        draw.rectangle((x1, label_y, x1 + text_w + 10, label_y + text_h + 8), fill=(24, 150, 94))
        draw.text((x1 + 5, label_y + 4), label, fill=(255, 255, 255), font=font)

    return output
