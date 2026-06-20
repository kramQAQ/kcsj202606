# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import io
import socket
import threading
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from PIL import Image

import constant
from detect_core import DEFAULT_CONF, MODEL_PATH, load_model, predict_image


MAX_UPLOAD_BYTES = 8 * 1024 * 1024

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

model = None
model_lock = threading.Lock()


def get_lan_ip() -> str:
    """Return the LAN IP that phones on the same Wi-Fi can usually reach."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


@app.get("/")
def index():
    return render_template(
        "mobile_detect.html",
        class_names=constant.CLASS_NAMES,
        default_conf=DEFAULT_CONF,
    )


@app.get("/api/health")
def health():
    return jsonify(
        status="ok",
        model=str(MODEL_PATH),
        classes=constant.CLASS_NAMES,
    )


@app.post("/api/detect")
def detect():
    if "file" not in request.files:
        return jsonify(status="error", message="No image file uploaded."), 400

    uploaded = request.files["file"]
    if not uploaded.filename:
        return jsonify(status="error", message="Uploaded image filename is empty."), 400

    try:
        image_bytes = uploaded.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return jsonify(status="error", message="Failed to parse image. Please take another photo."), 400

    # This project targets 1-3 users taking photos, not continuous video. Serializing
    # inference keeps small CPU/RAM servers and laptops responsive under brief bursts.
    with model_lock:
        result = predict_image(model, image, request.form.get("conf"))

    return jsonify(
        status="ok",
        image=result["image"],
        detections=result["detections"],
        counts=result["counts"],
        total=result["total"],
        elapsed_ms=result["elapsed_ms"],
    )


def main():
    global model

    parser = argparse.ArgumentParser(description="Mobile herb detection demo server.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=8868, type=int)
    args = parser.parse_args()

    print(f"Loading model: {MODEL_PATH}")
    model = load_model()

    lan_ip = get_lan_ip()
    print("Server ready.")
    print(f"Local:   http://127.0.0.1:{args.port}")
    print(f"Phone:   http://{lan_ip}:{args.port}")
    print("Tip: phone camera access is most reliable after HTTPS deployment.")

    app.run(host=args.host, port=args.port, threaded=True, debug=False)


if __name__ == "__main__":
    main()
