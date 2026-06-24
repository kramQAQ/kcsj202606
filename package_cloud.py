# -*- coding: utf-8 -*-
from __future__ import annotations

import shutil
import zipfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "tmp"

INCLUDE_FILES = [
    ".gitignore",
    "CLOUD_AUG_RUN_GUIDE.md",
    "constant.py",
    "data.yaml",
    "data_aug.yaml",
    "data_aug_1500.yaml",
    "data_aug_1500_v2.yaml",
    "requirements.txt",
    "train_all_exps.py",
    "summarize_experiments.py",
    "yolo_local.py",
    "yolov8n.pt",
    "yolov8n-bifpn.yaml",
    "yolov8n-cbam-bifpn.yaml",
    "yolov8n-cbam-bifpn-decoupled.yaml",
    "yolov8n-ghost-cbam-bifpn.yaml",
    "yolov8n-herb-improve.yaml",
    "yolov8n-neck-cbam.yaml",
]

INCLUDE_DIRS = [
    "analysis_outputs",
    "datasets",
    "datasets_aug",
    "datasets_aug_1500",
    "datasets_aug_1500_v2",
    "experiments",
    "ultralytics",
]

EXCLUDE_DIR_NAMES = {
    ".git",
    ".idea",
    ".venv",
    "__pycache__",
    ".ultralytics",
    "runs",
    "aug_train_results",
    "tmp",
}

EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".cache"}


def should_skip(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDE_DIR_NAMES for part in rel.parts):
        return True
    if path.suffix.lower() in EXCLUDE_SUFFIXES:
        return True
    if "trained_result" in rel.parts:
        return True
    return False


def add_file(zf: zipfile.ZipFile, path: Path) -> None:
    if path.exists() and path.is_file() and not should_skip(path):
        zf.write(path, path.relative_to(ROOT).as_posix())


def add_dir(zf: zipfile.ZipFile, directory: Path) -> None:
    if not directory.exists():
        return
    for path in directory.rglob("*"):
        if path.is_file() and not should_skip(path):
            zf.write(path, path.relative_to(ROOT).as_posix())


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    archive = OUT_DIR / f"kcsj_cloud_project_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for file_name in INCLUDE_FILES:
            add_file(zf, ROOT / file_name)
        for dir_name in INCLUDE_DIRS:
            add_dir(zf, ROOT / dir_name)

    size_mb = archive.stat().st_size / 1024 / 1024
    print(f"archive: {archive}")
    print(f"size_mb: {size_mb:.2f}")


if __name__ == "__main__":
    main()
