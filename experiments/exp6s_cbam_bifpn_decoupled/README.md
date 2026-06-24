# exp6s_cbam_bifpn_decoupled

YOLOv8s-scale version of exp6.

Changes from exp6:

- Keeps CBAM backbone blocks.
- Keeps BiFPN feature fusion.
- Keeps DecoupledDetect head.
- Changes model scale from YOLOv8n width `0.25` to YOLOv8s width `0.50`.

Recommended cloud training:

```bash
python -u train_exp6s_1500.py --epochs 150 --batch 64 --workers 8 2>&1 | tee logs/exp6s_1500_$(date +%Y%m%d_%H%M%S).log
```
