# RTX 5090 云端训练操作说明

## 1. 上传前本地检查

当前项目已经切换为读取新数据：

```text
data/images
data/labels
```

本地已验证划分结果：

```text
训练集：734 张
验证集：315 张
类别数：15
```

## 2. 打包建议

如果云服务器不准备联网安装依赖，需要把项目代码、数据、权重、虚拟环境一起打包。建议包含：

```text
.venv
constant.py
split_data.py
train_all_exps.py
summarize_experiments.py
data
datasets
data.yaml
experiments
ultralytics
yolov8n.pt
requirements.txt
```

不建议包含旧训练输出：

```text
runs
__pycache__
.git
```

## 3. 云端解压后检查

进入项目根目录后先执行：

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

如果显示 RTX 5090 且 `torch.cuda.is_available()` 为 `True`，再继续。

## 4. 重新划分数据

```bash
python split_data.py
```

确认输出为：

```text
train set size: 734
val set size: 315
```

## 5. 冒烟测试

先用 1 epoch 确认训练链路正常：

```bash
python train_all_exps.py --epochs 1 --only exp0_baseline exp2_bifpn exp11_bifpn_focal
```

## 6. 正式训练 exp0-exp11

建议使用 tmux：

```bash
tmux new -s kcsj_train
python train_all_exps.py --epochs 100
```

如果中途失败，可以从某个实验继续：

```bash
python train_all_exps.py --epochs 100 --start exp6_cbam_bifpn_decoupled
```

## 7. 汇总结果

训练完成后运行：

```bash
python summarize_experiments.py
```

结果会生成：

```text
experiments/EXPERIMENT_RESULTS_SUMMARY.md
```

报告中优先使用该表格进行消融实验分析。
