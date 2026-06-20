# Exp0-Exp7 实验工作指导

## 1. 实验目标

本轮实验用于系统验证 YOLOv8n 在中药饮片检测任务上的不同算法改进方向。实验按照从稳定到激进的顺序展开，避免一次性堆叠过多模块导致无法判断具体改进来源。

核心原则：

1. Exp0 作为基准模型。
2. Exp1-Exp3 优先验证稳定结构改进。
3. Exp4-Exp7 作为扩展或消融实验。
4. 每个 Exp 目录中保存一份对应模型源码，便于复现实验和写报告。

## 2. 实验顺序

| 实验编号 | 实验名称 | 主要改进方向 | 推荐优先级 |
| --- | --- | --- | --- |
| Exp0 | Baseline YOLOv8n | 原始 YOLOv8n 基准模型 | 必做 |
| Exp1 | YOLOv8n + Neck CBAM | 注意力机制 | 必做 |
| Exp2 | YOLOv8n + BiFPN | 特征融合增强 | 必做 |
| Exp3 | YOLOv8n + CBAM + BiFPN | 注意力 + 特征融合 | 主改进模型 |
| Exp4 | Exp3 + Focal Loss | 损失函数优化 | 选做 |
| Exp5 | GhostNet + CBAM + BiFPN | 骨干网络轻量化 | 选做 |
| Exp6 | Exp3 + Decoupled Head | 检测头优化 | 选做 |
| Exp7 | 综合改进版 | 五类改进综合尝试 | 选做/消融 |

## 3. 各实验说明

### Exp0：Baseline YOLOv8n

目的：建立对比基准。

结构：

```text
YOLOv8n 原始 Backbone
YOLOv8n 原始 Neck
YOLOv8n 原始 Detect Head
默认 BCE 分类损失
```

训练建议：

```powershell
.\.venv\python.exe .\train.py
```

### Exp1：YOLOv8n + Neck CBAM

目的：单独验证注意力机制是否能增强饮片纹理、轮廓特征。

结构：

```text
Backbone 保持 YOLOv8n 原始结构
Neck 中 C2f 替换为 C2fCBAM
Head 保持 Detect
```

预期：

```text
可能提升 Recall
可能略微增加参数量
若注意力过强，Precision 可能轻微下降
```

### Exp2：YOLOv8n + BiFPN

目的：单独验证加权多尺度特征融合是否有效。

结构：

```text
Backbone 保持 YOLOv8n 原始结构
Neck 中 Concat 替换为 BiFPN_Concat2
Head 保持 Detect
```

预期：

```text
对小目标、堆叠目标可能更友好
预训练权重继承稳定
参数量几乎不增加
```

### Exp3：YOLOv8n + CBAM + BiFPN

目的：作为当前主改进模型。

结构：

```text
C2fCBAM
BiFPN_Concat2
Detect
BCE Loss
```

当前已完成正式训练，验证结果：

| 模型 | Precision | Recall | mAP50 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: |
| YOLOv8n | 0.97905 | 0.94257 | 0.98786 | 0.80993 |
| CBAM+BiFPN | 0.95735 | 0.95253 | 0.98018 | 0.80977 |

结论：Recall 提升，mAP50-95 基本持平，适合作为最终报告中的主改进模型。

### Exp4：Exp3 + Focal Loss

目的：验证损失函数优化是否能改善难易样本不均衡问题。

注意：

前期实验中 Focal Loss 导致分类损失过小，模型分类学习不足，因此该实验只建议作为消融实验，不建议作为最终主模型。

### Exp5：GhostNet + CBAM + BiFPN

目的：验证骨干网络轻量化方向。

结构：

```text
GhostConv
C2fGhost
CBAM
BiFPN
Detect
```

预期：

```text
参数量和计算量可能下降
但预训练权重继承会变差
小数据集上精度可能下降
```

### Exp6：Exp3 + Decoupled Head

目的：验证检测头解耦是否能提升分类与回归任务的学习效果。

结构：

```text
CBAM
BiFPN
DecoupledDetect
```

风险：

```text
Detect Head 结构变化会影响预训练权重继承
小数据集上可能不稳定
```

### Exp7：综合改进版

目的：覆盖所有实质性改进方向。

结构：

```text
GhostNet/C2fGhost
CBAM
BiFPN
Focal Loss
DecoupledDetect
```

用途：

```text
用于证明五类改进方向均已代码落地
不建议作为最终精度最优模型
```

## 4. 推荐执行路线

建议按以下顺序执行：

```text
Exp0 -> Exp1 -> Exp2 -> Exp3 -> Exp4 -> Exp5 -> Exp6 -> Exp7
```

其中：

```text
Exp0-Exp3 必须完成
Exp4-Exp7 用于消融和报告补充
```

## 5. 结果记录建议

每个实验完成后记录：

```text
best.pt 路径
Precision
Recall
mAP50
mAP50-95
Params
GFLOPs
模型大小
推理速度
是否有效继承 yolov8n.pt
```

建议将结果统一补充到：

```text
EXPERIMENT_COMPARE.md
```

