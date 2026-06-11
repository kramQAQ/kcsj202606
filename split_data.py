import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml
from sklearn.model_selection import train_test_split

import constant


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def find_mismatches(pics_dir):
    images = {p.stem for p in pics_dir.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES}
    labels = {p.stem for p in pics_dir.glob("*.xml")}
    return sorted(images - labels), sorted(labels - images)


def voc_box_to_yolo(box, image_width, image_height):
    xmin = float(box.findtext("xmin"))
    ymin = float(box.findtext("ymin"))
    xmax = float(box.findtext("xmax"))
    ymax = float(box.findtext("ymax"))

    x_center = ((xmin + xmax) / 2) / image_width
    y_center = ((ymin + ymax) / 2) / image_height
    width = (xmax - xmin) / image_width
    height = (ymax - ymin) / image_height
    return x_center, y_center, width, height


def convert_xml_to_yolo(xml_path, class_to_id):
    root = ET.parse(xml_path).getroot()
    size = root.find("size")
    image_width = int(size.findtext("width"))
    image_height = int(size.findtext("height"))

    lines = []
    for obj in root.findall("object"):
        class_name = obj.findtext("name").strip()
        if class_name not in class_to_id:
            raise ValueError(f"Unknown class {class_name!r} in {xml_path}")

        box = obj.find("bndbox")
        x_center, y_center, width, height = voc_box_to_yolo(box, image_width, image_height)
        lines.append(
            "{} {:.6f} {:.6f} {:.6f} {:.6f}".format(
                class_to_id[class_name],
                x_center,
                y_center,
                width,
                height,
            )
        )
    return lines


def write_data_yaml():
    data = {
        "path": str(constant.DATASETS_DIR).replace("\\", "/"),
        "train": "images/train",
        "val": "images/val",
        "nc": len(constant.CLASS_NAMES),
        "names": constant.CLASS_NAMES,
    }
    with constant.DATA_YAML.open("w", encoding="utf-8") as file:
        yaml.safe_dump(data, file, allow_unicode=True, sort_keys=False)


def prepare_dirs():
    if constant.DATASETS_DIR.exists():
        shutil.rmtree(constant.DATASETS_DIR)

    for path in [
        constant.DATASETS_DIR / "images" / "train",
        constant.DATASETS_DIR / "images" / "val",
        constant.DATASETS_DIR / "labels" / "train",
        constant.DATASETS_DIR / "labels" / "val",
    ]:
        path.mkdir(parents=True, exist_ok=True)


def copy_split_files(label_paths, split_name):
    image_out = constant.DATASETS_DIR / "images" / split_name
    label_out = constant.DATASETS_DIR / "labels" / split_name

    for label_path in label_paths:
        image_path = next(
            (
                constant.PICS_DIR / f"{label_path.stem}{suffix}"
                for suffix in [".jpg", ".jpeg", ".png"]
                if (constant.PICS_DIR / f"{label_path.stem}{suffix}").exists()
            ),
            None,
        )
        if image_path is None:
            raise FileNotFoundError(f"Image not found for label {label_path.name}")

        shutil.copy2(image_path, image_out / image_path.name)
        shutil.copy2(label_path, label_out / label_path.name)


def split_dataset(test_size=0.3, random_state=42):
    pics_dir = constant.PICS_DIR
    if not pics_dir.exists():
        raise FileNotFoundError(f"Dataset folder not found: {pics_dir}")

    images_without_xml, xml_without_images = find_mismatches(pics_dir)
    if images_without_xml or xml_without_images:
        if images_without_xml:
            print("以下图片缺少对应的 XML 标注文件:")
            for name in images_without_xml:
                print(f"  {name}")
        if xml_without_images:
            print("以下 XML 标注文件缺少对应图片:")
            for name in xml_without_images:
                print(f"  {name}")
        raise SystemExit("数据集校验失败，请补齐缺失文件后再运行。")

    prepare_dirs()
    class_to_id = {name: index for index, name in enumerate(constant.CLASS_NAMES)}

    converted_label_dir = constant.DATASETS_DIR / "converted_labels"
    converted_label_dir.mkdir(parents=True, exist_ok=True)

    xml_paths = sorted(pics_dir.glob("*.xml"))
    converted_labels = []
    for xml_path in xml_paths:
        yolo_lines = convert_xml_to_yolo(xml_path, class_to_id)
        label_path = converted_label_dir / f"{xml_path.stem}.txt"
        label_path.write_text("\n".join(yolo_lines), encoding="utf-8")
        converted_labels.append(label_path)

    train_labels, val_labels = train_test_split(
        converted_labels,
        test_size=test_size,
        random_state=random_state,
        shuffle=True,
    )

    copy_split_files(train_labels, "train")
    copy_split_files(val_labels, "val")
    write_data_yaml()

    print(f"train set size: {len(train_labels)}")
    print(f"val set size: {len(val_labels)}")
    print(f"data.yaml: {constant.DATA_YAML}")
    print(f"datasets: {constant.DATASETS_DIR}")


if __name__ == "__main__":
    split_dataset()
