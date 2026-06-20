# Exp0-Exp7 逐一训练结果汇总

本轮训练使用本地 GPU 完成，数据集为 `2_1_dataset` 划分后的 `datasets`，训练配置为 100 epochs、imgsz=640、batch=4。已训练或复用的结果均保存到各实验目录的 `trained_result` 中。

## 结果总表

| 实验 | 改进内容 | 最优轮次 | Precision | Recall | mAP50 | mAP50-95 | last mAP50-95 | best.pt 大小 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| exp0_baseline | 原始 YOLOv8n | 87 | 0.9792 | 0.9427 | 0.9879 | 0.8084 | 0.7960 | 5.96 MB |
| exp1_neck_cbam | Neck 加 CBAM | 98 | 0.9615 | 0.9677 | 0.9713 | 0.8085 | 0.8078 | 6.17 MB |
| exp2_bifpn | Neck 替换为 BiFPN | 84 | 0.9453 | 0.9584 | 0.9829 | 0.8174 | 0.8093 | 5.96 MB |
| exp3_cbam_bifpn | CBAM + BiFPN | 95 | 0.9574 | 0.9524 | 0.9819 | 0.8082 | 0.8035 | 6.35 MB |
| exp4_cbam_bifpn_focal | CBAM + BiFPN + Focal Loss | 30 | 0.1759 | 0.3007 | 0.1567 | 0.1332 | 0.1149 | 6.34 MB |
| exp5_ghost_cbam_bifpn | Ghost 轻量化 + CBAM + BiFPN | 99 | 0.2668 | 0.4256 | 0.3724 | 0.2367 | 0.2276 | 4.19 MB |
| exp6_cbam_bifpn_decoupled | CBAM + BiFPN + Decoupled Head | 77 | 0.7998 | 0.9534 | 0.9174 | 0.7079 | 0.6902 | 6.78 MB |
| exp7_all_improvements | Ghost + CBAM + BiFPN + Focal + Decoupled Head | 90 | 0.0954 | 0.3843 | 0.1832 | 0.1167 | 0.1055 | 4.62 MB |

## 初步结论

1. 当前最优模型是 `exp2_bifpn`，mAP50-95 达到 0.8174，高于原始 YOLOv8n 的 0.8084。
2. `exp1_neck_cbam` 与基准基本持平，Recall 更高，说明注意力机制对召回有帮助，但单独加入 CBAM 没有显著提升综合精度。
3. `exp3_cbam_bifpn` 与基准接近，但没有超过 `exp2_bifpn`，说明在当前小数据集上，CBAM 与 BiFPN 同时叠加并不一定更优。
4. `exp4_cbam_bifpn_focal` 精度明显下降，说明当前 Focal Loss 参数或实现方式不适合直接作为正式方案，需要重新调整 alpha、gamma 或只对分类分支做更谨慎的加权。
5. `exp5_ghost_cbam_bifpn` 模型最小，但精度损失明显，适合作为轻量化对比实验，不建议作为最终检测模型。
6. `exp6_cbam_bifpn_decoupled` 比 exp4/exp5 稳定，但仍低于基准，说明 Decoupled Head 在当前样本规模下没有带来收益。
7. `exp7_all_improvements` 多项改动叠加后效果最差，证明改进不能简单堆叠，需要逐项消融筛选。

## 推荐采用

正式模型建议优先使用：

```text
E:\homework\2026\kcsj\experiments\exp2_bifpn\trained_result\weights\best.pt
```

报告中可以把 `exp2_bifpn` 作为最终改进模型，把 `exp0_baseline` 作为原始模型对照，其余实验作为消融分析。
