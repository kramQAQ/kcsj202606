from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SOURCE_DATASET_DIR = BASE_DIR / "2_1_dataset"
SOURCE_IMAGE_DIR = SOURCE_DATASET_DIR / "image"
SOURCE_LABEL_DIR = SOURCE_DATASET_DIR / "label"
SOURCE_CLASSES_FILE = SOURCE_LABEL_DIR / "classes.txt"
DATASETS_DIR = BASE_DIR / "datasets"
DATA_YAML = BASE_DIR / "data.yaml"
MODEL_PATH = BASE_DIR / "yolov8n.pt"
RUNS_DETECT_DIR = BASE_DIR / "runs" / "detect"

CLASS_NAMES = [
    "zexie",
    "niuxi",
    "gaoliangjiang",
    "mudanpi",
    "yuzhu",
    "baizhi",
    "baishao",
    "dazao",
    "danshen",
    "gancao",
    "baixianpi",
    "baihe",
    "sangzhi",
    "jiegeng",
    "banlangen",
]
