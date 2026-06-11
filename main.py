from pathlib import Path

from show_data import run_demo as show_data_demo
from step_ocr_task import run_demo as step_ocr_task_demo


BASE_DIR = Path(__file__).resolve().parent
CORRECTED_IMAGE = BASE_DIR / "chufang2_cut.jpg"


def main():
    yinpian_data = step_ocr_task_demo(CORRECTED_IMAGE)
    show_data_demo(yinpian_data)


if __name__ == "__main__":
    main()
