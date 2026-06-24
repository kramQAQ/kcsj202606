from datetime import datetime
from pathlib import Path

import torch
import yolo_local  # noqa: F401
from ultralytics import YOLO

import constant


def train_experiment(model_yaml, exp_name, load_pretrained=True, epochs=100):
    device = 0 if torch.cuda.is_available() else "cpu"
    device_name = "gpu" if device == 0 else "cpu"
    run_name = f"{exp_name}_{device_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    model = YOLO(str(Path(model_yaml)), task="detect")
    if load_pretrained:
        model = model.load(str(constant.MODEL_PATH))

    model.train(
        data=str(constant.DATA_YAML),
        epochs=epochs,
        imgsz=640,
        batch=4,
        device=device,
        workers=0,
        plots=False,
        project=str(constant.RUNS_DETECT_DIR),
        name=run_name,
        exist_ok=False,
    )
    print(f"device: {device}")
    print(f"train result dir: {constant.RUNS_DETECT_DIR / run_name}")
