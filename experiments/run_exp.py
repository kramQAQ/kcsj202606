import argparse
import os
import shutil
from datetime import datetime
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT))

import yolo_local  # noqa: E402,F401
from ultralytics import YOLO  # noqa: E402

import constant  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("exp_dir", help="Experiment directory, e.g. experiments/exp1_neck_cbam")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--data", default=str(constant.DATA_YAML), help="Dataset YAML path, e.g. data.yaml or data_aug.yaml")
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--no-pretrained", action="store_true")
    parser.add_argument("--pretrained-weights", default=str(constant.MODEL_PATH))
    args = parser.parse_args()

    exp_dir = Path(args.exp_dir).resolve()
    model_yaml = exp_dir / "model.yaml"
    if not model_yaml.exists():
        raise FileNotFoundError(model_yaml)

    device = 0 if torch.cuda.is_available() else "cpu"
    device_name = "gpu" if device == 0 else "cpu"
    run_name = f"{exp_dir.name}_{device_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.environ["YOLO_USE_FOCAL_LOSS"] = "1" if "focal" in exp_dir.name else "0"

    model = YOLO(str(model_yaml), task="detect")
    if not args.no_pretrained:
        pretrained_weights = Path(args.pretrained_weights)
        if not pretrained_weights.is_absolute():
            pretrained_weights = ROOT / pretrained_weights
        if pretrained_weights.exists():
            model = model.load(str(pretrained_weights))
        else:
            print(f"WARNING: pretrained weights not found: {pretrained_weights}. Training from scratch.", flush=True)

    model.train(
        data=str(Path(args.data).resolve()),
        epochs=args.epochs,
        imgsz=640,
        batch=args.batch,
        device=device,
        workers=args.workers,
        plots=False,
        project=str(constant.RUNS_DETECT_DIR),
        name=run_name,
        exist_ok=False,
    )

    print(f"experiment: {exp_dir.name}")
    print(f"device: {device}")
    run_dir = constant.RUNS_DETECT_DIR / run_name
    print(f"run: {run_dir}")

    result_dir = exp_dir / "trained_result"
    if result_dir.exists():
        shutil.rmtree(result_dir)
    result_dir.mkdir(parents=True, exist_ok=True)
    for name in ("weights", "args.yaml", "results.csv", "results.png"):
        source = run_dir / name
        target = result_dir / name
        if source.exists():
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)
    (result_dir / "SOURCE.txt").write_text(f"source_run: {run_dir}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
