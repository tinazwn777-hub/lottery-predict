"""
数据库模型定义
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LotteryRecord(BaseModel):
    """彩票开奖记录"""
    id: Optional[int] = None
    lottery_type: str = Field(..., description="彩种类型: ssq/dlt")
    issue: str = Field(..., description="期号")
    red_balls: str = Field(..., description="红球号码,逗号分隔")
    blue_ball: str = Field(..., description="蓝球号码,逗号分隔")
    open_date: str = Field(..., description="开奖日期")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    class Config:
        from_attributes = True


class LotteryType(BaseModel):
    """彩种信息"""
    code: str  # ssq, dlt
    name: str  # 双色球, 超级大乐透
    red_count: int  # 红球数量
    blue_count: int  # 蓝球数量


# 彩种配置
LOTTERY_TYPES = {
    "ssq": LotteryType(
        code="ssq",
        name="双色球",
        red_count=6,
        blue_count=1
    ),
    "dlt": LotteryType(
        code="dlt",
        name="超级大乐透",
        red_count=5,
        blue_count=2
    ),
}
