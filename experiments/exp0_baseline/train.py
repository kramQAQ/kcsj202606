from ultralytics import YOLO
from datetime import datetime

import constant


def main():
    device = "cpu"
    train_name = f"train_cpu_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    model = YOLO(str(constant.MODEL_PATH))
    model.train(
        data=str(constant.DATA_YAML),
        epochs=100,
        imgsz=640,
        batch=4,
        device=device,
        workers=0,
        project=str(constant.RUNS_DETECT_DIR),
        name=train_name,
        exist_ok=False,
    )
    print(f"train result dir: {constant.RUNS_DETECT_DIR / train_name}")


if __name__ == "__main__":
    main()
