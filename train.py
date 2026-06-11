from ultralytics import YOLO

import constant


def main():
    model = YOLO(str(constant.MODEL_PATH))
    model.train(
        data=str(constant.DATA_YAML),
        epochs=100,
        imgsz=640,
        batch=4,
        workers=0,
        project=str(constant.RUNS_DETECT_DIR),
        name="train",
        exist_ok=True,
    )


if __name__ == "__main__":
    main()
