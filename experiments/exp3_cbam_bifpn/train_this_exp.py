from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
EXP_DIR = Path(__file__).resolve().parent

cmd = [str(ROOT / ".venv" / "python.exe"), str(ROOT / "experiments" / "run_exp.py"), str(EXP_DIR)]
raise SystemExit(subprocess.call(cmd, cwd=str(ROOT)))
