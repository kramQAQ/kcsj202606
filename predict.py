from pathlib import Path
from datetime import datetime

from ultralytics import YOLO
import torch

import constant


DEFAULT_SOURCE = constant.SOURCE_IMAGE_DIR / "2_1_001.jpg"


def find_best_model_path():
    train_dirs = sorted(
        constant.RUNS_DETECT_DIR.glob("train_cpu_*"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for train_dir in train_dirs:
        best_path = train_dir / "weights" / "best.pt"
        if best_path.exists():
            return best_path
    return constant.RUNS_DETECT_DIR / "train" / "weights" / "best.pt"


def main(source=DEFAULT_SOURCE):
    source = Path(source)
    best_model_path = find_best_model_path()
    if not best_model_path.exists():
        raise FileNotFoundError(f"Best model not found: {best_model_path}")
    if not source.exists():
        raise FileNotFoundError(f"Predict source not found: {source}")

    device = "cpu"
    result_name = f"predict_cpu_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    model = YOLO(str(best_model_path))
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

    print(f"model: {best_model_path}")
    print(f"predict source: {source}")
    print(f"predict result dir: {constant.RUNS_DETECT_DIR / result_name}")


if __name__ == "__main__":
    main()
