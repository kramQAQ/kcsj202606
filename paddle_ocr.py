from pathlib import Path

from paddleocr import PaddleOCR


def create_ocr():
    return PaddleOCR(
        use_angle_cls=True,
        lang="ch",
        ocr_version="PP-OCRv4",
        show_log=False,
        use_gpu=False,
    )


def clean_text(text):
    return text.replace(" ", "").replace("锛?,", "").replace("銆?,", "")


def ocr_image(image_path, paddle_ocr=None):
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    paddle_ocr = paddle_ocr or create_ocr()
    result = paddle_ocr.ocr(str(image_path), cls=True)
    texts = []

    for page in result or []:
        if page is None:
            continue
        for line in page:
            texts.append(clean_text(line[1][0]))
    return texts


def main():
    image_path = Path(__file__).with_name("chufang1.png")
    print(ocr_image(image_path))


if __name__ == "__main__":
    main()

