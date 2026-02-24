"""
预测服务模块
"""
from .statistical import StatisticalPredictor, predict, get_statistics, LOTTERY_CONFIG

__all__ = [
    "StatisticalPredictor",
    "predict",
    "get_statistics",
    "LOTTERY_CONFIG",
]
