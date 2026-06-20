# Exp0-Exp7 实验索引

每个实验目录都包含：

```text
model.yaml
train_this_exp.py
train_experiment.py
constant.py
yolo_local.py
src_snapshot/
```

其中 `src_snapshot/` 保存了创建实验时的模型相关源码快照。

## 实验状态

| 实验 | 模型方案 | 当前状态 |
| --- | --- | --- |
| exp0_baseline | 原始 YOLOv8n | 已复制训练结果 |
| exp1_neck_cbam | YOLOv8n + Neck CBAM | 已实现，待训练 |
| exp2_bifpn | YOLOv8n + BiFPN | 已实现，待训练 |
| exp3_cbam_bifpn | YOLOv8n + CBAM + BiFPN | 已复制训练结果 |
| exp4_cbam_bifpn_focal | Exp3 + Focal Loss | 已实现，待训练 |
| exp5_ghost_cbam_bifpn | GhostNet + CBAM + BiFPN | 已实现，待训练 |
| exp6_cbam_bifpn_decoupled | CBAM + BiFPN + DecoupledDetect | 已实现，待训练 |
| exp7_all_improvements | Ghost + CBAM + BiFPN + Focal + Decoupled | 已复制训练结果 |

## 运行方式

从项目根目录运行某个实验：

```powershell
.\.venv\python.exe .\experiments\run_exp.py .\experiments\exp1_neck_cbam
```

或者运行某个实验目录中的入口：

```powershell
.\.venv\python.exe .\experiments\exp1_neck_cbam\train_this_exp.py
```

训练输出统一保存到：

```text
runs/detect/
```

已训练实验的结果副本保存到：

```text
experiments/<exp_name>/trained_result/
```
