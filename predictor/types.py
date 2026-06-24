"""预测引擎共享数据类型。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScoreLine:
    home: int
    away: int
    probability: float
