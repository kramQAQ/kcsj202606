import torch
import yolo_local  # noqa: F401
from ultralytics import YOLO

import constant


def find_best_model_path():
    train_dirs = sorted(
        constant.RUNS_DETECT_DIR.glob("train_cbam_bifpn_*"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for train_dir in train_dirs:
        best_path = train_dir / "weights" / "best.pt"
        if best_path.exists():
            return best_path
    raise FileNotFoundError("No CBAM+BiFPN best.pt found. Run train_cbam_bifpn.py first.")


def main():
    device = 0 if torch.cuda.is_available() else "cpu"
    best_model_path = find_best_model_path()
    model = YOLO(str(best_model_path), task="detect")
    metrics = model.val(
        data=str(constant.DATA_YAML),
        imgsz=640,
        batch=4,
        device=device,
        workers=0,
        plots=False,
        project=str(constant.RUNS_DETECT_DIR),
        name="val_cbam_bifpn",
        exist_ok=True,
    )
    print(f"device: {device}")
    print(f"model: {best_model_path}")
    print(f"mAP50: {metrics.box.map50:.4f}")
    print(f"mAP50-95: {metrics.box.map:.4f}")


if __name__ == "__main__":
    main()
