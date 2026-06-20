# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_EXPERIMENTS = [
    "exp0_baseline",
    "exp1_neck_cbam",
    "exp2_bifpn",
    "exp3_cbam_bifpn",
    "exp4_cbam_bifpn_focal",
    "exp5_ghost_cbam_bifpn",
    "exp6_cbam_bifpn_decoupled",
    "exp7_all_improvements",
    "exp8_bifpn_neck_cbam",
    "exp9_bifpn_backbone_cbam",
    "exp10_bifpn_decoupled",
    "exp11_bifpn_focal",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Train exp0-exp11 sequentially.")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--start", default=None, help="Start from this experiment name.")
    parser.add_argument("--only", nargs="*", default=None, help="Train only selected experiment names.")
    args = parser.parse_args()

    experiments = args.only or DEFAULT_EXPERIMENTS
    if args.start:
        if args.start not in experiments:
            raise SystemExit(f"Unknown start experiment: {args.start}")
        experiments = experiments[experiments.index(args.start) :]

    for exp_name in experiments:
        exp_dir = ROOT / "experiments" / exp_name
        if not exp_dir.exists():
            raise FileNotFoundError(exp_dir)

        cmd = [
            sys.executable,
            str(ROOT / "experiments" / "run_exp.py"),
            str(exp_dir),
            "--epochs",
            str(args.epochs),
        ]
        print("=" * 80, flush=True)
        print(f"Training {exp_name}: {' '.join(cmd)}", flush=True)
        completed = subprocess.run(cmd, cwd=str(ROOT), check=False)
        if completed.returncode != 0:
            print(f"FAILED: {exp_name}", flush=True)
            return completed.returncode

    print("=" * 80, flush=True)
    print("All selected experiments finished.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
