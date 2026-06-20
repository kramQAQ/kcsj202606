from datetime import datetime

import torch
import yolo_local  # noqa: F401
from ultralytics import YOLO

import constant


MODEL_YAML = constant.BASE_DIR / "yolov8n-herb-improve.yaml"


def main():
    device = 0 if torch.cuda.is_available() else "cpu"
    device_name = "gpu" if device == 0 else "cpu"
    train_name = f"train_improve_{device_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    model = YOLO(str(MODEL_YAML), task="detect")
    model.train(
        data=str(constant.DATA_YAML),
        epochs=100,
        imgsz=640,
        batch=4,
        device=device,
        workers=0,
        plots=False,
        project=str(constant.RUNS_DETECT_DIR),
        name=train_name,
        exist_ok=False,
    )
    print(f"device: {device}")
    print(f"train result dir: {constant.RUNS_DETECT_DIR / train_name}")


if __name__ == "__main__":
    main()
