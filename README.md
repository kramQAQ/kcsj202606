# 基于改进 YOLOv8 的中医药饮片智能检测与识别系统

本项目用于中医药饮片图像检测、处方图像 OCR 识别和结果展示。仓库中包含示例图片、YOLO 数据集、训练入口、OCR 处理逻辑和 Tkinter 展示界面。

## 环境要求

推荐使用 Python 3.10。不要把 `.venv` 上传到 GitHub，其他人可以根据 `requirements.txt` 重新安装依赖。

如果使用 Conda：

```bash
conda create -n kcsj python=3.10
conda activate kcsj
pip install -r requirements.txt
```

如果使用 Python 自带虚拟环境：

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## 运行主程序

```bash
python main.py
```

主程序会读取 `chufang2_cut.jpg`，调用 PaddleOCR 识别处方信息，并用 Tkinter 界面展示处理结果。

## OCR 服务

如果需要启动 HTTP OCR 服务：

```bash
python ocr_server.py
```

服务默认监听：

```text
http://0.0.0.0:8866
```

接口包括：

- `POST /ocr_img`：上传图片文件识别
- `GET /ocr_filepath?file=图片路径`：按本地图片路径识别

注意：`ocr_server.py` 中 PaddleOCR 当前设置为 `use_gpu=True`。如果电脑没有可用 GPU 或 CUDA/Paddle GPU 环境，请把它改为 `use_gpu=False`。

## 训练 YOLO

训练入口：

```bash
python train.py
```

训练配置读取：

- `data.yaml`
- `datasets/images/train`
- `datasets/images/val`
- `datasets/labels/train`
- `datasets/labels/val`
- 初始权重 `yolov8n.pt`

训练输出会写入 `runs/`，该目录已被 `.gitignore` 忽略，不会提交到仓库。

## 相机采集说明

`camera.py` 和 `ui_cam.py` 使用了 `gxipy`，这是大恒图像工业相机 SDK 的 Python 包，通常不能只靠 `pip install -r requirements.txt` 自动安装。

如果需要使用相机功能，请先安装对应相机驱动和 Galaxy SDK，并确认 Python 环境中可以正常：

```python
import gxipy
```

不使用相机功能时，可以直接运行 `main.py`、`ocr_server.py` 或 `train.py`。

## 目录说明

```text
main.py              主程序入口
paddle_ocr.py        PaddleOCR 封装
step_ocr_task.py     处方图像裁剪、识别和结构化处理
show_data.py         Tkinter 展示界面
train.py             YOLO 训练入口
data.yaml            YOLO 数据集配置
datasets/            YOLO 训练/验证数据
pics/                原始图片和标注文件
ultralytics/         项目内附带的 Ultralytics 代码
yolov8n.pt           YOLOv8 初始权重
```

## 常见问题

如果安装 PaddleOCR 或 PaddlePaddle 很慢，可以先配置 pip 镜像源。

如果运行 OCR 时首次下载模型较慢，等待下载完成即可；模型缓存通常保存在用户目录下。

如果安装 `torch` 失败，请根据自己的系统、CUDA 版本或 CPU 环境，到 PyTorch 官网选择合适的安装命令后再安装其余依赖。
