# Base + BiFPN 二次消融实验设计

前一轮 `exp0-exp7` 的结果显示，`exp2_bifpn` 在 mAP50-95 上取得当前最高结果。因此后续消融实验以 `Base + BiFPN` 为共同基础，逐项增加其他模块，判断这些模块在最优基础模型上是否仍然带来收益。

## 实验组设计

| 实验 | 基础模型 | 新增改动 | 目的 |
|---|---|---|---|
| exp2_bifpn | YOLOv8n + BiFPN | 无 | 作为二次消融的基准 |
| exp8_bifpn_neck_cbam | YOLOv8n + BiFPN | 仅在 Neck 的 C2f 后加入 CBAM | 验证注意力机制放在特征融合阶段是否有效 |
| exp9_bifpn_backbone_cbam | YOLOv8n + BiFPN | 仅在 Backbone 的 C2f 后加入 CBAM | 验证注意力机制放在主干特征提取阶段是否有效 |
| exp10_bifpn_decoupled | YOLOv8n + BiFPN | Detect 替换为 DecoupledDetect | 验证解耦检测头是否提升分类与回归效果 |
| exp11_bifpn_focal | YOLOv8n + BiFPN | 启用 Focal Loss | 验证损失函数优化是否改善难易样本不均衡 |

## 训练命令

```powershell
.\.venv\python.exe .\experiments\run_exp.py .\experiments\exp8_bifpn_neck_cbam
.\.venv\python.exe .\experiments\run_exp.py .\experiments\exp9_bifpn_backbone_cbam
.\.venv\python.exe .\experiments\run_exp.py .\experiments\exp10_bifpn_decoupled
.\.venv\python.exe .\experiments\run_exp.py .\experiments\exp11_bifpn_focal
```

## 报告写法建议

报告中可以先说明第一轮消融发现 `BiFPN` 是最有效模块，然后开展第二轮消融：以 `Base + BiFPN` 为基础，继续测试注意力机制、检测头优化和损失函数优化。这样可以形成“先筛选有效模块，再围绕有效模块继续优化”的实验逻辑。

如果 `exp8-exp11` 中没有超过 `exp2_bifpn`，也可以作为有效结论写入报告：说明在当前小样本数据集上，BiFPN 已经带来主要收益，继续叠加 CBAM、Focal Loss 或 Decoupled Head 可能增加训练难度，导致泛化性能下降。
