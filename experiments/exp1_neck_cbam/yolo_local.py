import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LOCAL_ULTRALYTICS = ROOT / "ultralytics"

if str(LOCAL_ULTRALYTICS) not in sys.path:
    sys.path.insert(0, str(LOCAL_ULTRALYTICS))
