# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from datetime import datetime


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / f"kcsj_cloud_project_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

INCLUDE_ITEMS = [
    "constant.py",
    "split_data.py",
    "train_all_exps.py",
    "summarize_experiments.py",
    "CLOUD_RUN_GUIDE.md",
    "data.yaml",
    "yolov8n.pt",
    "requirements.txt",
    "data",
    "datasets",
    "experiments",
    "ultralytics",
]

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "runs",
    "tmp",
    ".idea",
    ".agents",
    ".codex",
}


def iter_files(path: Path):
    if path.is_file():
        yield path
        return

    for file in path.rglob("*"):
        if not file.is_file():
            continue
        rel_parts = file.relative_to(ROOT).parts
        if any(part in EXCLUDE_DIRS for part in rel_parts):
            continue
        yield file


def main() -> None:
    skipped: list[tuple[str, str]] = []

    with ZipFile(OUTPUT, "w", ZIP_DEFLATED, compresslevel=6) as zip_file:
        for item in INCLUDE_ITEMS:
            path = ROOT / item
            if not path.exists():
                skipped.append((str(path), "missing"))
                continue

            for file in iter_files(path):
                try:
                    zip_file.write(file, file.relative_to(ROOT).as_posix())
                except OSError as exc:
                    skipped.append((str(file), str(exc)))

    print(f"created: {OUTPUT}")
    print(f"size_mb: {OUTPUT.stat().st_size / 1024 / 1024:.2f}")
    print(f"skipped: {len(skipped)}")
    for file, reason in skipped[:30]:
        print(f"{file} | {reason}")


if __name__ == "__main__":
    main()
