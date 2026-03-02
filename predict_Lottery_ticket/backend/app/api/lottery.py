"""
API路由 - 彩票数据相关
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import logging

from ..services.crawler import crawl_all_lotteries, LOTTERY_CONFIG
from ..services.predictor import predict, get_statistics
from ..services.verifier import get_verifier
from ..core.database import get_db
from ..models.schemas import LotteryRecord, LotteryType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/lottery", tags=["彩票数据"])


# ==================== 响应模型 ====================

class LotteryTypesResponse(BaseModel):
    """彩种列表响应"""
    types: List[LotteryType]


class HistoryResponse(BaseModel):
    """历史数据响应"""
    lottery_type: str
    total: int
    data: List[dict]


class CrawlResponse(BaseModel):
    """爬取响应"""
    success: bool
    message: str
    ssq_count: int = 0
    dlt_count: int = 0


# ==================== API端点 ====================

@router.get("/types", response_model=LotteryTypesResponse)
async def get_lottery_types():
    """获取支持的彩种列表"""
    types = [
        LotteryType(
            code="ssq",
            name="双色球",
            red_count=6,
            blue_count=1
        ),
        LotteryType(
            code="dlt",
            name="超级大乐透",
            red_count=5,
            blue_count=2
        ),
    ]
    return LotteryTypesResponse(types=types)


@router.post("/crawl", response_model=CrawlResponse)
async def crawl_data(limit: int = Query(50, ge=1, le=500, description="爬取期数")):
    """
    手动触发数据爬取

    从 datachart.500.com 爬取最新开奖数据
    """
    db = get_db()
    results = {"ssq_count": 0, "dlt_count": 0, "errors": []}

    try:
        # 爬取所有彩种数据
        all_data = await crawl_all_lotteries(limit=limit)

        # 存储到数据库
        for lottery_type, records in all_data.items():
            if records:
                count = db.insert_records(records)
                results[f"{lottery_type}_count"] = count

        return CrawlResponse(
            success=True,
            message=f"爬取完成: 双色球 {results['ssq_count']} 期, 大乐透 {results['dlt_count']} 期",
            ssq_count=results["ssq_count"],
            dlt_count=results["dlt_count"]
        )

    except Exception as e:
        logger.error(f"爬取数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"爬取失败: {str(e)}")


# ==================== 预测相关API ====================

class PredictRequest(BaseModel):
    """预测请求"""
    lottery_type: str
    method: str = Query("smart", description="预测方法: frequency/hot_cold/missing/smart")
    count: int = Query(1, ge=1, le=10, description="生成注数")


class PredictResponse(BaseModel):
    """预测响应"""
    success: bool
    lottery_type: str
    lottery_name: str
    predictions: List[dict]
    method: str


@router.post("/predict", response_model=PredictResponse)
async def create_prediction(request: PredictRequest):
    """
    生成预测号码

    支持的预测方法:
    - smart: 智能综合策略（推荐）- 综合多维度分析自动生成最优预测
    - frequency: 基于号码频率
    - hot_cold: 基于冷热号分析
    - missing: 基于遗漏值分析
    """
    if request.lottery_type not in LOTTERY_CONFIG:
        raise HTTPException(status_code=400, detail=f"不支持的彩种: {request.lottery_type}")

    try:
        predictions = predict(
            lottery_type=request.lottery_type,
            method=request.method,
            count=request.count
        )

        return PredictResponse(
            success=True,
            lottery_type=request.lottery_type,
            lottery_name=LOTTERY_CONFIG[request.lottery_type]["name"],
            predictions=predictions,
            method=request.method
        )

    except Exception as e:
        logger.error(f"预测失败: {e}")
        raise HTTPException(status_code=500, detail=f"预测失败: {str(e)}")


# ==================== 预测保存与验证API ====================

class SavePredictionRequest(BaseModel):
    """保存预测请求"""
    lottery_type: str
    predictions: List[dict]


class SavePredictionResponse(BaseModel):
    """保存预测响应"""
    success: bool
    message: str
    count: int


class VerifyRequest(BaseModel):
    """验证请求"""
    lottery_type: str
    limit: int = Query(100, ge=1, le=500, description="验证期数")


class VerifyResponse(BaseModel):
    """验证响应"""
    success: bool
    lottery_type: str
    total_predictions: int
    verified_count: int
    no_draw_count: int
    total_wins: int
    win_rate: float
    prize_stats: List[dict]
    detailed_results: List[dict]


@router.post("/predictions", response_model=SavePredictionResponse)
async def save_predictions(request: SavePredictionRequest):
    """
    保存预测号码

    批量保存用户生成的预测号码
    """
    if request.lottery_type not in LOTTERY_CONFIG:
        raise HTTPException(status_code=400, detail=f"不支持的彩种: {request.lottery_type}")

    if not request.predictions:
        raise HTTPException(status_code=400, detail="预测号码不能为空")

    try:
        db = get_db()
        # 确保每个预测对象都有 lottery_type
        for pred in request.predictions:
            if "lottery_type" not in pred:
                pred["lottery_type"] = request.lottery_type
        count = db.save_predictions(request.predictions)

        return SavePredictionResponse(
            success=True,
            message=f"成功保存 {count} 注预测",
            count=count
        )

    except Exception as e:
        logger.error(f"保存预测失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存预测失败: {str(e)}")


@router.get("/predictions")
async def get_all_predictions():
    """
    获取所有预测记录

    获取所有彩种的用户预测记录
    """
    try:
        db = get_db()

        ssq_predictions = db.get_predictions("ssq")
        dlt_predictions = db.get_predictions("dlt")

        return {
            "success": True,
            "total": len(ssq_predictions) + len(dlt_predictions),
            "predictions": ssq_predictions + dlt_predictions
        }

    except Exception as e:
        logger.error(f"获取预测失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取预测失败: {str(e)}")


@router.get("/predictions/{lottery_type}")
async def get_predictions(lottery_type: str):
    """
    获取预测列表

    获取指定彩种的用户预测记录
    """
    if lottery_type not in LOTTERY_CONFIG:
        raise HTTPException(status_code=400, detail=f"不支持的彩种: {lottery_type}")

    try:
        db = get_db()
        predictions = db.get_predictions(lottery_type)
        count = db.get_prediction_count(lottery_type)

        return {
            "success": True,
            "lottery_type": lottery_type,
            "total": count,
            "predictions": predictions
        }

    except Exception as e:
        logger.error(f"获取预测失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取预测失败: {str(e)}")


@router.delete("/predictions/{lottery_type}")
async def clear_predictions(lottery_type: str):
    """
    清空预测记录

    删除指定彩种的所有预测记录
    """
    if lottery_type not in LOTTERY_CONFIG:
        raise HTTPException(status_code=400, detail=f"不支持的彩种: {lottery_type}")

    try:
        db = get_db()
        count = db.clear_predictions(lottery_type)

        return {
            "success": True,
            "message": f"已清空 {count} 条预测记录"
        }

    except Exception as e:
        logger.error(f"清空预测失败: {e}")
        raise HTTPException(status_code=500, detail=f"清空预测失败: {str(e)}")


@router.post("/verify", response_model=VerifyResponse)
async def verify_predictions(request: VerifyRequest):
    """
    验证预测号码

    将保存的预测号码与对应期号的开奖记录进行比对，统计中奖情况
    """
    if request.lottery_type not in LOTTERY_CONFIG:
        raise HTTPException(status_code=400, detail=f"不支持的彩种: {request.lottery_type}")

    try:
        db = get_db()
        verifier = get_verifier()

        # 获取预测记录
        predictions = db.get_predictions(request.lottery_type)
        if not predictions:
            raise HTTPException(status_code=400, detail="暂无预测记录，请先生成并保存预测")

        # 获取历史开奖记录，构建期号到开奖记录的映射
        history = db.get_history(request.lottery_type, limit=request.limit, offset=0)
        if not history:
            raise HTTPException(status_code=400, detail="暂无历史开奖数据，请先爬取数据")

        # 构建 issue_map: 期号 -> 开奖记录
        issue_map = {record["issue"]: record for record in history}

        # 执行验证
        result = verifier.verify(request.lottery_type, predictions, issue_map)

        return VerifyResponse(
            success=True,
            **result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证失败: {e}")
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")


@router.get("/verification-stats/{lottery_type}")
async def get_verification_stats(lottery_type: str):
    """
    获取验证统计

    获取指定彩种的验证统计数据（简化版）
    """
    if lottery_type not in LOTTERY_CONFIG:
        raise HTTPException(status_code=400, detail=f"不支持的彩种: {lottery_type}")

    try:
        db = get_db()
        verifier = get_verifier()

        # 获取预测记录
        predictions = db.get_predictions(lottery_type)
        if not predictions:
            return {
                "success": True,
                "lottery_type": lottery_type,
                "has_predictions": False,
                "message": "暂无预测记录"
            }

        # 获取历史记录数量
        history_count = db.get_count(lottery_type)

        return {
            "success": True,
            "lottery_type": lottery_type,
            "has_predictions": True,
            "prediction_count": len(predictions),
            "history_count": history_count,
            "message": f"有 {len(predictions)} 注预测，可验证 {history_count} 期"
        }

    except Exception as e:
        logger.error(f"获取验证统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取验证统计失败: {str(e)}")


# ==================== 历史数据相关API ====================
# 注意: 这些路由必须在预测/验证等具体路由之后定义，避免路径冲突

@router.get("/{lottery_type}/history", response_model=HistoryResponse)
async def get_history(
    lottery_type: str,
    limit: int = Query(50, ge=1, le=500, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """获取历史开奖数据"""
    # 验证彩种
    if lottery_type not in LOTTERY_CONFIG:
        raise HTTPException(status_code=400, detail=f"不支持的彩种: {lottery_type}")

    db = get_db()

    # 检查是否有数据
    count = db.get_count(lottery_type)
    if count == 0:
        return HistoryResponse(
            lottery_type=lottery_type,
            total=0,
            data=[],
            message="暂无数据，请先爬取"
        )

    # 获取数据
    data = db.get_history(lottery_type, limit=limit, offset=offset)

    return HistoryResponse(
        lottery_type=lottery_type,
        total=count,
        data=data
    )


@router.get("/{lottery_type}/latest")
async def get_latest(lottery_type: str):
    """获取最新一期开奖数据"""
    if lottery_type not in LOTTERY_CONFIG:
        raise HTTPException(status_code=400, detail=f"不支持的彩种: {lottery_type}")

    db = get_db()
    latest = db.get_latest_issue(lottery_type)

    if not latest:
        raise HTTPException(status_code=404, detail="暂无数据")

    return latest


@router.delete("/{lottery_type}/clear")
async def clear_data(lottery_type: str):
    """清空指定彩种的所有数据"""
    if lottery_type not in LOTTERY_CONFIG:
        raise HTTPException(status_code=400, detail=f"不支持的彩种: {lottery_type}")

    db = get_db()
    count = db.clear(lottery_type)

    return {"success": True, "message": f"已清空 {count} 条记录"}


@router.get("/statistics/{lottery_type}")
async def get_lottery_statistics(lottery_type: str):
    """
    获取彩票统计分析数据

    包含:
    - 号码出现频率
    - 热号/冷号
    - 奇偶比分布
    - 区间分布
    """
    if lottery_type not in LOTTERY_CONFIG:
        raise HTTPException(status_code=400, detail=f"不支持的彩种: {lottery_type}")

    try:
        stats = get_statistics(lottery_type)
        return stats

    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")
