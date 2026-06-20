from datetime import datetime
from pathlib import Path

import torch
import yolo_local  # noqa: F401
from ultralytics import YOLO

import constant


DEFAULT_SOURCE = constant.SOURCE_IMAGE_DIR / "2_1_001.jpg"


def find_best_model_path():
    train_dirs = sorted(
        constant.RUNS_DETECT_DIR.glob("train_improve_*"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for train_dir in train_dirs:
        best_path = train_dir / "weights" / "best.pt"
        if best_path.exists():
            return best_path
    raise FileNotFoundError("No improved best.pt found. Run train_improve.py first.")


def main(source=DEFAULT_SOURCE):
    source = Path(source)
    best_model_path = find_best_model_path()
    if not source.exists():
        raise FileNotFoundError(f"Predict source not found: {source}")

    device = 0 if torch.cuda.is_available() else "cpu"
    device_name = "gpu" if device == 0 else "cpu"
    result_name = f"predict_improve_{device_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    model = YOLO(str(best_model_path), task="detect")
    model.predict(
        source=str(source),
        imgsz=640,
        conf=0.25,
        device=device,
        save=True,
        project=str(constant.RUNS_DETECT_DIR),
        name=result_name,
        exist_ok=False,
    )
    print(f"device: {device}")
    print(f"model: {best_model_path}")
    print(f"predict source: {source}")
    print(f"predict result dir: {constant.RUNS_DETECT_DIR / result_name}")


if __name__ == "__main__":
    main()
