# 中医药饮片智能检测与识别系统

本项目基于改进 YOLOv8 实现中医药饮片图像的定位、分类识别与计数。当前正式部署模型采用 `exp2_bifpn`，即在 YOLOv8n 的 Neck 中引入 BiFPN 加权特征融合。

## 当前模型

推荐模型权重：

```text
experiments/exp2_bifpn/trained_result/weights/best.pt
```

实验结果摘要：

| 模型 | 改进内容 | Precision | Recall | mAP50 | mAP50-95 |
| --- | --- | ---: | ---: | ---: | ---: |
| exp0_baseline | YOLOv8n | 0.9792 | 0.9427 | 0.9879 | 0.8084 |
| exp2_bifpn | YOLOv8n + BiFPN | 0.9453 | 0.9584 | 0.9829 | 0.8174 |

## 环境安装

推荐 Python 3.10。

```bash
pip install -r requirements.txt
```

如果使用已有虚拟环境：

```powershell
.\.venv\python.exe -m pip install -r requirements.txt
```

## 启动网页识别服务

```powershell
.\.venv\python.exe .\main.py
```

默认端口为 `8868`。启动后终端会输出本机和局域网访问地址，例如：

```text
Local:   http://127.0.0.1:8868
Phone:   http://172.20.10.3:8868
```

网页端功能：

- 上传图片或调用手机相册/相机拍照
- 调用后端 YOLO 模型推理
- 显示检测框、类别、置信度
- 统计每类饮片数量和总数

说明：手机浏览器实时摄像头通常要求 HTTPS。局域网 HTTP 下若实时摄像头被浏览器拦截，可使用页面中的“相册/相机”入口拍照上传。

## 启动本地桌面客户端

```powershell
.\.venv\python.exe .\desktop_client.py
```

桌面客户端功能：

- 本地上传饮片图片
- 使用 `exp2_bifpn` 模型离线推理
- 绘制定位框、类别和置信度
- 统计饮片总数与分类数量
- 导出 CSV 盘点结果，便于药房盘点和仓储管理留档

## 模型训练与验证

基础训练入口：

```powershell
.\.venv\python.exe .\train.py
```

验证入口：

```powershell
.\.venv\python.exe .\val.py
```

单图预测入口：

```powershell
.\.venv\python.exe .\predict.py
```

实验管理与消融结果保存在 `experiments/`，其中 `exp2_bifpn` 为当前推荐部署模型。训练相关代码、模型结构、数据集配置和实验结果未被整理操作修改。

## 目录说明

```text
main.py                         Web 识别服务入口
desktop_client.py               本地上传图片识别客户端
detect_core.py                  模型加载、推理、画框和计数核心逻辑
templates/mobile_detect.html    手机/网页端识别页面
constant.py                     数据集路径和类别配置
data.yaml                       YOLO 数据集配置
datasets/                       训练/验证数据
2_1_dataset/                    原始饮片数据
experiments/                    实验配置、训练结果和消融对比
ultralytics/                    项目内 Ultralytics 源码与自定义模块
yolov8n.pt                      YOLOv8n 预训练权重
```

## 类别

当前支持 15 类饮片：

```text
zexie, niuxi, gaoliangjiang, mudanpi, yuzhu,
baizhi, baishao, dazao, danshen, gancao,
baixianpi, baihe, sangzhi, jiegeng, banlangen
```
