# Ultralytics YOLO, AGPL-3.0 license
"""BiFPN feature fusion modules."""

import torch
import torch.nn as nn


__all__ = ("BiFPN_Add2", "BiFPN_Add3", "BiFPN_Concat2")


class BiFPN_Add2(nn.Module):
    """Weighted two-input feature fusion used by BiFPN."""

    def __init__(self, epsilon=1e-4):
        super().__init__()
        self.w = nn.Parameter(torch.ones(2, dtype=torch.float32), requires_grad=True)
        self.epsilon = epsilon

    def forward(self, x):
        w = torch.relu(self.w)
        weight = w / (w.sum() + self.epsilon)
        return weight[0] * x[0] + weight[1] * x[1]


class BiFPN_Add3(nn.Module):
    """Weighted three-input feature fusion used by BiFPN."""

    def __init__(self, epsilon=1e-4):
        super().__init__()
        self.w = nn.Parameter(torch.ones(3, dtype=torch.float32), requires_grad=True)
        self.epsilon = epsilon

    def forward(self, x):
        w = torch.relu(self.w)
        weight = w / (w.sum() + self.epsilon)
        return weight[0] * x[0] + weight[1] * x[1] + weight[2] * x[2]


class BiFPN_Concat2(nn.Module):
    """Weighted two-input fusion that preserves YOLOv8 Concat channel dimensions."""

    def __init__(self, dimension=1, epsilon=1e-4):
        super().__init__()
        self.d = dimension
        self.w = nn.Parameter(torch.ones(2, dtype=torch.float32), requires_grad=True)
        self.epsilon = epsilon

    def forward(self, x):
        w = torch.relu(self.w)
        weight = w / (w.sum() + self.epsilon)
        return torch.cat((weight[0] * x[0], weight[1] * x[1]), self.d)
