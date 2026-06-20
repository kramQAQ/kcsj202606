import shutil
from pathlib import Path

import yaml
from sklearn.model_selection import train_test_split

import constant


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}


def load_class_names():
    if constant.SOURCE_CLASSES_FILE.exists():
        class_names = [
            line.strip()
            for line in constant.SOURCE_CLASSES_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if class_names:
            return class_names
    return constant.CLASS_NAMES


def find_image_for_label(label_path):
    for suffix in IMAGE_SUFFIXES:
        image_path = constant.SOURCE_IMAGE_DIR / f"{label_path.stem}{suffix}"
        if image_path.exists():
            return image_path
    return None


def find_mismatches():
    images = {
        path.stem
        for path in constant.SOURCE_IMAGE_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    }
    labels = {
        path.stem
        for path in constant.SOURCE_LABEL_DIR.glob("*.txt")
        if path.name.lower() != "classes.txt"
    }
    return sorted(images - labels), sorted(labels - images)


def validate_label_file(label_path, class_count):
    bad_lines = []
    for line_number, line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue

        parts = line.split()
        if len(parts) != 5:
            bad_lines.append((line_number, "expected 5 columns"))
            continue

        try:
            class_id = int(parts[0])
            values = [float(value) for value in parts[1:]]
        except ValueError:
            bad_lines.append((line_number, "non numeric value"))
            continue

        if class_id < 0 or class_id >= class_count:
            bad_lines.append((line_number, f"class id {class_id} out of range"))
        if any(value < 0 or value > 1 for value in values):
            bad_lines.append((line_number, "bbox value out of 0..1 range"))

    if bad_lines:
        details = ", ".join(f"line {line}: {reason}" for line, reason in bad_lines)
        raise ValueError(f"Invalid label file {label_path}: {details}")


def write_data_yaml(class_names):
    data = {
        "path": str(constant.DATASETS_DIR).replace("\\", "/"),
        "train": "images/train",
        "val": "images/val",
        "nc": len(class_names),
        "names": class_names,
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
        image_path = find_image_for_label(label_path)
        if image_path is None:
            raise FileNotFoundError(f"Image not found for label {label_path.name}")

        shutil.copy2(image_path, image_out / image_path.name)
        shutil.copy2(label_path, label_out / label_path.name)


def split_dataset(test_size=0.3, random_state=42):
    if not constant.SOURCE_IMAGE_DIR.exists():
        raise FileNotFoundError(f"Image folder not found: {constant.SOURCE_IMAGE_DIR}")
    if not constant.SOURCE_LABEL_DIR.exists():
        raise FileNotFoundError(f"Label folder not found: {constant.SOURCE_LABEL_DIR}")

    class_names = load_class_names()
    images_without_labels, labels_without_images = find_mismatches()
    if images_without_labels or labels_without_images:
        if images_without_labels:
            print("Images missing labels:")
            for name in images_without_labels:
                print(f"  {name}")
        if labels_without_images:
            print("Labels missing images:")
            for name in labels_without_images:
                print(f"  {name}")
        raise SystemExit("Dataset validation failed. Please fix missing files first.")

    label_paths = sorted(
        path
        for path in constant.SOURCE_LABEL_DIR.glob("*.txt")
        if path.name.lower() != "classes.txt"
    )
    if not label_paths:
        raise SystemExit(f"No label files found in {constant.SOURCE_LABEL_DIR}")

    for label_path in label_paths:
        validate_label_file(label_path, len(class_names))

    prepare_dirs()
    train_labels, val_labels = train_test_split(
        label_paths,
        test_size=test_size,
        random_state=random_state,
        shuffle=True,
    )

    copy_split_files(train_labels, "train")
    copy_split_files(val_labels, "val")
    write_data_yaml(class_names)

    print(f"source images: {constant.SOURCE_IMAGE_DIR}")
    print(f"source labels: {constant.SOURCE_LABEL_DIR}")
    print(f"classes: {len(class_names)}")
    print(f"train set size: {len(train_labels)}")
    print(f"val set size: {len(val_labels)}")
    print(f"data.yaml: {constant.DATA_YAML}")
    print(f"datasets: {constant.DATASETS_DIR}")


if __name__ == "__main__":
    split_dataset()
