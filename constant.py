from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PICS_DIR = BASE_DIR / "pics"
DATASETS_DIR = BASE_DIR / "datasets"
DATA_YAML = BASE_DIR / "data.yaml"
MODEL_PATH = BASE_DIR / "yolov8n.pt"
RUNS_DETECT_DIR = BASE_DIR / "runs" / "detect"

CLASS_NAMES = [
    "jiegeng",
    "danshen",
    "banlangen",
    "baixianpi",
    "zexie",
    "sangzhi",
    "niuxi",
    "baishao",
    "gancaopian",
    "mudanpi",
    "gaoliangjiang",
    "baizhi",
    "baihe",
    "yuzhu",
    "dazao",
]
