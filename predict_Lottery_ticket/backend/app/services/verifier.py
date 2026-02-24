"""
预测验证服务
将用户保存的预测号码与对应期号的开奖记录进行比对，统计中奖情况
"""
from typing import List, Dict, Any, Tuple, Callable, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class PrizeLevel:
    """中奖等级定义"""

    # 双色球中奖等级定义 (红球匹配数, 蓝球匹配数)
    SSQ_PRIZE_LEVELS = {
        (6, 1): "一等奖",
        (6, 0): "二等奖",
        (5, 1): "三等奖",
        (5, 0): "四等奖",
        (4, 1): "四等奖",
        (4, 0): "五等奖",
        (3, 1): "五等奖",
        (2, 1): "六等奖",
        (1, 1): "六等奖",
        (0, 1): "六等奖",
    }

    # 大乐透中奖等级定义 (前区匹配数, 后区匹配数)
    DLT_PRIZE_LEVELS = {
        (5, 2): "一等奖",
        (5, 1): "二等奖",
        (5, 0): "三等奖",
        (4, 2): "四等奖",
        (4, 1): "五等奖",
        (4, 0): "六等奖",
        (3, 2): "六等奖",
        (3, 1): "七等奖",
        (2, 2): "七等奖",
        (3, 0): "八等奖",
        (2, 1): "八等奖",
        (1, 2): "八等奖",
        (2, 0): "九等奖",
        (1, 1): "九等奖",
        (0, 2): "九等奖",
    }

    @classmethod
    def get_prize_level(cls, lottery_type: str, red_match: int, blue_match: int) -> Tuple[str, int]:
        """
        获取中奖等级

        Args:
            lottery_type: 彩种类型 (ssq/dlt)
            red_match: 红球/前区匹配数量
            blue_match: 蓝球/后区匹配数量

        Returns:
            (中奖等级名称, 奖级数字) 未中奖返回 ("未中奖", 0)
        """
        levels = cls.SSQ_PRIZE_LEVELS if lottery_type == "ssq" else cls.DLT_PRIZE_LEVELS
        prize = levels.get((red_match, blue_match), None)

        if prize is None:
            return "未中奖", 0

        # 根据奖级名称返回数字
        prize_map = {
            "一等奖": 1,
            "二等奖": 2,
            "三等奖": 3,
            "四等奖": 4,
            "五等奖": 5,
            "六等奖": 6,
            "七等奖": 7,
            "八等奖": 8,
            "九等奖": 9,
        }
        return prize, prize_map.get(prize, 0)


class Verifier:
    """预测验证器"""

    def __init__(self):
        self.prize_level = PrizeLevel()

    def _parse_balls(self, balls_str: str) -> set:
        """解析球号字符串为集合"""
        if not balls_str:
            return set()
        return set(int(x.strip()) for x in balls_str.split(",") if x.strip())

    def _count_matches(self, pred_balls: str, draw_balls: str) -> int:
        """计算预测号码与开奖号码的匹配数量"""
        pred_set = self._parse_balls(pred_balls)
        draw_set = self._parse_balls(draw_balls)
        return len(pred_set & draw_set)

    def verify_ssq(
        self,
        predictions: List[Dict[str, Any]],
        issue_map: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        验证双色球预测

        Args:
            predictions: 预测记录列表，每个预测需要包含 target_issue
            issue_map: 期号到开奖记录的映射

        Returns:
            验证结果统计
        """
        prize_counts = defaultdict(int)
        detailed_results = []
        total_verifications = 0
        no_draw_count = 0  # 没有对应开奖结果的预测数量

        for pred in predictions:
            target_issue = pred.get("target_issue")
            if not target_issue:
                continue

            total_verifications += 1

            # 查找对应期号的开奖记录
            record = issue_map.get(target_issue)
            if not record:
                no_draw_count += 1
                detailed_results.append({
                    "prediction_id": pred.get("id"),
                    "target_issue": target_issue,
                    "pred_red": pred["red_balls"],
                    "pred_blue": pred["blue_balls"],
                    "issue": None,
                    "draw_red": None,
                    "draw_blue": None,
                    "open_date": None,
                    "red_matches": 0,
                    "blue_matches": 0,
                    "prize": "未开奖",
                    "prize_level": 0,
                })
                continue

            pred_red = pred["red_balls"]
            pred_blue = pred["blue_balls"]

            draw_red = record["red_balls"]
            draw_blue = record["blue_ball"]

            # 计算匹配数量
            red_matches = self._count_matches(pred_red, draw_red)
            blue_matches = self._count_matches(pred_blue, draw_blue)

            # 获取中奖等级
            prize_name, prize_level = self.prize_level.get_prize_level("ssq", red_matches, blue_matches)

            if prize_level > 0:
                prize_counts[prize_name] += 1

            detailed_results.append({
                "prediction_id": pred.get("id"),
                "target_issue": target_issue,
                "pred_red": pred_red,
                "pred_blue": pred_blue,
                "issue": record["issue"],
                "draw_red": draw_red,
                "draw_blue": draw_blue,
                "open_date": record.get("open_date", ""),
                "red_matches": red_matches,
                "blue_matches": blue_matches,
                "prize": prize_name,
                "prize_level": prize_level,
            })

        return self._build_result("ssq", predictions, prize_counts, detailed_results, total_verifications, no_draw_count)

    def verify_dlt(
        self,
        predictions: List[Dict[str, Any]],
        issue_map: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        验证大乐透预测

        Args:
            predictions: 预测记录列表
            issue_map: 期号到开奖记录的映射

        Returns:
            验证结果统计
        """
        prize_counts = defaultdict(int)
        detailed_results = []
        total_verifications = 0
        no_draw_count = 0

        for pred in predictions:
            target_issue = pred.get("target_issue")
            if not target_issue:
                continue

            total_verifications += 1

            # 查找对应期号的开奖记录
            record = issue_map.get(target_issue)
            if not record:
                no_draw_count += 1
                detailed_results.append({
                    "prediction_id": pred.get("id"),
                    "target_issue": target_issue,
                    "pred_front": pred["red_balls"],
                    "pred_back": pred["blue_balls"],
                    "issue": None,
                    "draw_front": None,
                    "draw_back": None,
                    "open_date": None,
                    "front_matches": 0,
                    "back_matches": 0,
                    "prize": "未开奖",
                    "prize_level": 0,
                })
                continue

            pred_front = pred["red_balls"]  # 前区
            pred_back = pred["blue_balls"]  # 后区

            draw_front = record["red_balls"]
            draw_back = record["blue_ball"]

            # 计算匹配数量
            front_matches = self._count_matches(pred_front, draw_front)
            back_matches = self._count_matches(pred_back, draw_back)

            # 获取中奖等级
            prize_name, prize_level = self.prize_level.get_prize_level("dlt", front_matches, back_matches)

            if prize_level > 0:
                prize_counts[prize_name] += 1

            detailed_results.append({
                "prediction_id": pred.get("id"),
                "target_issue": target_issue,
                "pred_front": pred_front,
                "pred_back": pred_back,
                "issue": record["issue"],
                "draw_front": draw_front,
                "draw_back": draw_back,
                "open_date": record.get("open_date", ""),
                "front_matches": front_matches,
                "back_matches": back_matches,
                "prize": prize_name,
                "prize_level": prize_level,
            })

        return self._build_result("dlt", predictions, prize_counts, detailed_results, total_verifications, no_draw_count)

    def _build_result(
        self,
        lottery_type: str,
        predictions: List[Dict[str, Any]],
        prize_counts: Dict[str, int],
        detailed_results: List[Dict[str, Any]],
        total_verifications: int,
        no_draw_count: int
    ) -> Dict[str, Any]:
        """构建验证结果"""
        # 计算总中奖次数
        total_wins = sum(prize_counts.values())

        # 计算总中奖率（只计算有开奖结果的）
        valid_verifications = total_verifications - no_draw_count
        win_rate = (total_wins / valid_verifications * 100) if valid_verifications > 0 else 0

        # 按奖级排序的中奖统计
        prize_order = ["一等奖", "二等奖", "三等奖", "四等奖", "五等奖", "六等奖", "七等奖", "八等奖", "九等奖"]
        prize_stats = []
        for prize in prize_order:
            if prize in prize_counts:
                count = prize_counts[prize]
                rate = (count / valid_verifications * 100) if valid_verifications > 0 else 0
                prize_stats.append({
                    "prize": prize,
                    "count": count,
                    "rate": round(rate, 2),
                })

        return {
            "lottery_type": lottery_type,
            "total_predictions": len(predictions),
            "verified_count": valid_verifications,
            "no_draw_count": no_draw_count,
            "total_wins": total_wins,
            "win_rate": round(win_rate, 2),
            "prize_stats": prize_stats,
            "detailed_results": detailed_results,
        }

    def verify(
        self,
        lottery_type: str,
        predictions: List[Dict[str, Any]],
        issue_map: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        验证预测

        Args:
            lottery_type: 彩种类型
            predictions: 预测记录列表
            issue_map: 期号到开奖记录的映射

        Returns:
            验证结果统计
        """
        if lottery_type == "ssq":
            return self.verify_ssq(predictions, issue_map)
        elif lottery_type == "dlt":
            return self.verify_dlt(predictions, issue_map)
        else:
            raise ValueError(f"不支持的彩种类型: {lottery_type}")


# 全局验证器实例
verifier = Verifier()


def get_verifier() -> Verifier:
    """获取验证器实例"""
    return verifier
