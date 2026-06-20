from ultralytics import YOLO
import torch

import constant


BEST_MODEL_PATH = constant.RUNS_DETECT_DIR / "train" / "weights" / "best.pt"


def main():
    if not BEST_MODEL_PATH.exists():
        raise FileNotFoundError(f"Best model not found: {BEST_MODEL_PATH}")

    device = 0 if torch.cuda.is_available() else "cpu"
    model = YOLO(str(BEST_MODEL_PATH))
    metrics = model.val(
        data=str(constant.DATA_YAML),
        imgsz=640,
        batch=4,
        device=device,
        workers=0,
        project=str(constant.RUNS_DETECT_DIR),
        name="val",
        exist_ok=True,
    )

    print(f"mAP50: {metrics.box.map50:.4f}")
    print(f"mAP50-95: {metrics.box.map:.4f}")


if __name__ == "__main__":
    main()
