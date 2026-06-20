# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPERIMENTS_DIR = ROOT / "experiments"
SUMMARY_PATH = EXPERIMENTS_DIR / "EXPERIMENT_RESULTS_SUMMARY.md"


def read_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def metric(row: dict[str, str], name: str) -> float:
    value = row.get(name, "0")
    return float(value) if value not in ("", None) else 0.0


def main() -> None:
    lines = [
        "# Exp0-Exp11 实验结果汇总",
        "",
        "| 实验 | 最优轮次 | Precision | Recall | mAP50 | mAP50-95 | last mAP50-95 | best.pt MB |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for exp_dir in sorted(EXPERIMENTS_DIR.glob("exp*")):
        result_csv = exp_dir / "trained_result" / "results.csv"
        best_pt = exp_dir / "trained_result" / "weights" / "best.pt"
        if not result_csv.exists():
            lines.append(f"| {exp_dir.name} | 未训练 | - | - | - | - | - | - |")
            continue

        rows = read_rows(result_csv)
        if not rows:
            lines.append(f"| {exp_dir.name} | 无结果 | - | - | - | - | - | - |")
            continue

        best_row = max(rows, key=lambda row: metric(row, "metrics/mAP50-95(B)"))
        last_row = rows[-1]
        best_size = best_pt.stat().st_size / 1024 / 1024 if best_pt.exists() else 0.0
        lines.append(
            "| {exp} | {epoch} | {p:.4f} | {r:.4f} | {map50:.4f} | {map5095:.4f} | {last:.4f} | {size:.2f} |".format(
                exp=exp_dir.name,
                epoch=best_row.get("epoch", "-"),
                p=metric(best_row, "metrics/precision(B)"),
                r=metric(best_row, "metrics/recall(B)"),
                map50=metric(best_row, "metrics/mAP50(B)"),
                map5095=metric(best_row, "metrics/mAP50-95(B)"),
                last=metric(last_row, "metrics/mAP50-95(B)"),
                size=best_size,
            )
        )

    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"summary: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
