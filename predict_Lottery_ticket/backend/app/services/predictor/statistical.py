"""
统计分析预测模块
基于历史数据进行分析和预测
"""
import random
from collections import Counter
from typing import List, Dict, Tuple, Optional
import logging
import os
import sys

# 确保正确的导入路径
_current_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(_current_dir)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from app.core.database import get_db

logger = logging.getLogger(__name__)

# 彩票配置
LOTTERY_CONFIG = {
    "ssq": {
        "name": "双色球",
        "red_range": (1, 33),   # 红球范围
        "blue_range": (1, 16),   # 蓝球范围
        "red_count": 6,          # 红球数量
        "blue_count": 1,         # 蓝球数量
    },
    "dlt": {
        "name": "超级大乐透",
        "red_range": (1, 35),    # 前区红球范围
        "blue_range": (1, 12),   # 后区蓝球范围
        "red_count": 5,          # 前区红球数量
        "blue_count": 2,         # 后区蓝球数量
    },
}


class StatisticalPredictor:
    """统计预测器"""

    def __init__(self, lottery_type: str):
        if lottery_type not in LOTTERY_CONFIG:
            raise ValueError(f"不支持的彩种: {lottery_type}")

        self.lottery_type = lottery_type
        self.config = LOTTERY_CONFIG[lottery_type]
        self.db = get_db()

    def get_history_data(self, limit: int = 100) -> List[Dict]:
        """获取历史数据"""
        return self.db.get_history(self.lottery_type, limit=limit)

    def parse_balls(self, record: Dict) -> Tuple[List[int], List[int]]:
        """解析号码"""
        red_str = record["red_balls"]
        blue_str = record["blue_ball"]

        if self.lottery_type == "ssq":
            red_balls = [int(x) for x in red_str.split(",")]
            blue_balls = [int(blue_str)]
        else:  # dlt
            red_balls = [int(x) for x in red_str.split(",")]
            blue_balls = [int(x) for x in blue_str.split(",")]

        return red_balls, blue_balls

    def analyze_frequency(self, records: List[Dict]) -> Tuple[Counter, Counter]:
        """
        分析号码出现频率

        Returns:
            (red_counter, blue_counter): 红球和蓝球出现次数统计
        """
        red_counter = Counter()
        blue_counter = Counter()

        for record in records:
            red_balls, blue_balls = self.parse_balls(record)
            red_counter.update(red_balls)
            blue_counter.update(blue_balls)

        return red_counter, blue_counter

    def analyze_hot_cold(
        self,
        counter: Counter,
        top_n: int = 10
    ) -> Tuple[List[int], List[int]]:
        """
        分析热号和冷号

        Returns:
            (hot_numbers, cold_numbers): 热号和冷号列表
        """
        if not counter:
            return [], []

        # 按出现次数排序
        sorted_items = sorted(counter.items(), key=lambda x: x[1], reverse=True)

        # 前N个为热号
        hot_numbers = [num for num, _ in sorted_items[:top_n]]
        # 后N个为冷号
        cold_numbers = [num for num, _ in sorted_items[-top_n:]]

        return hot_numbers, cold_numbers

    def analyze_missing(self, records: List[Dict]) -> Dict[int, int]:
        """
        分析号码遗漏值（当前未出现的期数）

        Returns:
            {号码: 遗漏期数}
        """
        if not records:
            return {}

        # 记录每个号码最近一次出现的位置
        last_appear = {}
        for idx, record in enumerate(records):
            red_balls, blue_balls = self.parse_balls(record)
            all_balls = red_balls + blue_balls

            for ball in all_balls:
                if ball not in last_appear:
                    last_appear[ball] = idx

        # 计算遗漏值
        total = len(records)
        missing = {
            ball: total - pos
            for ball, pos in last_appear.items()
        }

        return missing

    def analyze_odd_even(self, records: List[Dict]) -> Dict[str, int]:
        """
        分析奇偶比分布

        Returns:
            {"3:3": 25, "4:2": 30, ...}
        """
        odd_even_dist = Counter()

        for record in records:
            red_balls, _ = self.parse_balls(record)
            odd_count = sum(1 for x in red_balls if x % 2 == 1)
            even_count = len(red_balls) - odd_count
            odd_even_dist[(odd_count, even_count)] += 1

        # 将 tuple 键转换为字符串
        return {f"{k[0]}:{k[1]}": v for k, v in odd_even_dist.items()}

    def analyze_range(self, records: List[Dict]) -> Dict[int, int]:
        """
        分析号码区间分布

        双色球: 1-11, 12-22, 23-33
        大乐透: 1-12, 13-24, 25-35
        """
        if self.lottery_type == "ssq":
            ranges = [(1, 11), (12, 22), (23, 33)]
        else:
            ranges = [(1, 12), (13, 24), (25, 35)]

        range_dist = {i: 0 for i in range(len(ranges))}

        for record in records:
            red_balls, _ = self.parse_balls(record)
            for ball in red_balls:
                for idx, (start, end) in enumerate(ranges):
                    if start <= ball <= end:
                        range_dist[idx] += 1
                        break

        return range_dist

    def analyze_missing_distribution(self, records: List[Dict]) -> Dict[str, int]:
        """
        分析号码遗漏值分布

        统计不同遗漏值区间的号码个数

        Returns:
            {"0-5": 8, "6-10": 6, "11-15": 5, "16-20": 3, "20+": 2}
        """
        if not records:
            return {}

        # 先获取每个号码的遗漏值
        missing = self.analyze_missing(records)

        # 统计各遗漏值区间的号码数量
        distribution = {
            "0-5": 0,
            "6-10": 0,
            "11-15": 0,
            "16-20": 0,
            "20+": 0
        }

        for ball, miss in missing.items():
            if miss <= 5:
                distribution["0-5"] += 1
            elif miss <= 10:
                distribution["6-10"] += 1
            elif miss <= 15:
                distribution["11-15"] += 1
            elif miss <= 20:
                distribution["16-20"] += 1
            else:
                distribution["20+"] += 1

        # 只返回有数据的区间
        return {k: v for k, v in distribution.items() if v > 0}

    def analyze_tail(self, records: List[Dict]) -> Dict[str, int]:
        """
        分析号码尾数分布

        统计红球个位数（尾数）的出现次数

        Returns:
            {"0": 12, "1": 15, "2": 22, "3": 18, "4": 15, "5": 12, "6": 10, "7": 30, "8": 18, "9": 12}
        """
        if not records:
            return {}

        tail_counter = Counter()

        for record in records:
            red_balls, _ = self.parse_balls(record)
            for ball in red_balls:
                tail = ball % 10
                tail_counter[tail] += 1

        # 转换为字符串键
        return {str(k): v for k, v in sorted(tail_counter.items())}

    def analyze_sum(self, records: List[Dict]) -> Dict[str, int]:
        """
        分析红球和值分布

        统计红球号码总和的区间分布

        Returns:
            {"60-79": 5, "80-99": 25, "100-119": 35, "120-139": 20, "140+": 5}
        """
        if not records:
            return {}

        # 定义和值区间
        ranges = ["60-79", "80-99", "100-119", "120-139", "140-159", "160-183"]
        range_keys = {
            (60, 79): "60-79",
            (80, 99): "80-99",
            (100, 119): "100-119",
            (120, 139): "120-139",
            (140, 159): "140-159",
            (160, 183): "160-183"
        }

        sum_dist = {r: 0 for r in ranges}

        for record in records:
            red_balls, _ = self.parse_balls(record)
            total = sum(red_balls)

            for (low, high), key in range_keys.items():
                if low <= total <= high:
                    sum_dist[key] += 1
                    break

        # 只返回有数据的区间
        return {k: v for k, v in sum_dist.items() if v > 0}

    def analyze_consecutive(self, records: List[Dict]) -> Dict[str, int]:
        """
        分析连号出现情况

        统计每期开奖号码中相邻号码的出现次数

        Returns:
            {"none": 45, "2": 35, "3": 8, "2+": 2}
            none: 无连号
            2: 1组2连号 (如 01,02)
            3: 1组3连号 (如 01,02,03)
            2+: 2组或更多连号
        """
        if not records:
            return {}

        stats = {
            "none": 0,
            "2": 0,
            "3": 0,
            "2+": 0
        }

        for record in records:
            red_balls, _ = self.parse_balls(record)
            red_balls = sorted(red_balls)

            # 统计连号组数
            consecutive_count = 0
            consecutive_groups = []

            for i in range(len(red_balls) - 1):
                if red_balls[i + 1] - red_balls[i] == 1:
                    # 记录连号段
                    if not consecutive_groups or red_balls[i] not in consecutive_groups[-1]:
                        consecutive_groups.append([red_balls[i], red_balls[i + 1]])
                    else:
                        consecutive_groups[-1].append(red_balls[i + 1])

            # 统计实际连号组数
            for group in consecutive_groups:
                group_len = len(group)
                if group_len == 2:
                    consecutive_count = max(consecutive_count, 2)
                elif group_len >= 3:
                    consecutive_count = max(consecutive_count, 3)

            if consecutive_count == 0:
                stats["none"] += 1
            elif consecutive_count == 2:
                stats["2"] += 1
            elif consecutive_count == 3:
                stats["3"] += 1
            else:
                stats["2+"] += 1

        # 只返回有数据的类别
        return {k: v for k, v in stats.items() if v > 0}

    def generate_prediction(
        self,
        method: str = "frequency",
        count: int = 1
    ) -> List[Dict]:
        """
        生成预测号码

        Args:
            method: 预测方法 (frequency/hot_cold/random/missing/smart)
            count: 生成注数

        Returns:
            预测结果列表
        """
        records = self.get_history_data(limit=100)

        if not records:
            logger.warning("没有足够的历史数据用于预测")
            return self._generate_random_prediction(count)

        predictions = []

        for _ in range(count):
            if method == "frequency":
                pred = self._predict_by_frequency(records)
            elif method == "hot_cold":
                pred = self._predict_by_hot_cold(records)
            elif method == "missing":
                pred = self._predict_by_missing(records)
            elif method == "smart":
                pred = self._predict_by_smart_strategy(records)
            else:
                pred = self._generate_random_prediction(1)[0]

            predictions.append(pred)

        return predictions

    def _predict_by_smart_strategy(self, records: List[Dict]) -> Dict:
        """
        智能综合策略预测

        综合多维度统计分析，自动计算最优号码组合：
        1. 号码频率权重
        2. 冷热号平衡
        3. 遗漏值分析
        4. 奇偶比分布
        5. 尾数分布
        6. 连号避免
        7. 区间分布
        """
        # 获取各项统计数据
        red_counter, blue_counter = self.analyze_frequency(records)
        red_missing = self.analyze_missing(records)
        odd_even_dist = self.analyze_odd_even(records)
        tail_dist = self.analyze_tail(records)
        consecutive_stats = self.analyze_consecutive(records)

        # 1. 频率得分 (0-100)
        red_freq_scores = self._calc_frequency_scores(red_counter)
        blue_freq_scores = self._calc_frequency_scores(blue_counter)

        # 2. 遗漏值得分 (遗漏值越接近平均值越好)
        red_missing_scores = self._calc_missing_scores(red_missing, self.config["red_range"][1])
        blue_missing_scores = self._calc_missing_scores(red_missing, self.config["blue_range"][1])

        # 3. 尾数分布得分 (避免同尾号过多)
        tail_scores = self._calc_tail_scores(tail_dist)

        # 4. 奇偶比得分 (根据历史最常见比例)
        odd_even_scores = self._calc_odd_even_scores(odd_even_dist)

        # 综合权重计算
        red_weights = {}
        for n in range(1, self.config["red_range"][1] + 1):
            freq = red_freq_scores.get(n, 50)
            miss = red_missing_scores.get(n, 50)
            tail = tail_scores.get(n % 10, 50)
            odd = odd_even_scores.get(n, 50)

            # 权重分配: 频率40%, 遗漏25%, 尾数20%, 奇偶15%
            red_weights[n] = freq * 0.40 + miss * 0.25 + tail * 0.20 + odd * 0.15

        blue_weights = {}
        for n in range(1, self.config["blue_range"][1] + 1):
            freq = blue_freq_scores.get(n, 50)
            miss = blue_missing_scores.get(n, 50)
            # 蓝球尾数权重较低
            blue_weights[n] = freq * 0.60 + miss * 0.40

        # 归一化权重
        red_weights = self._normalize_weights(red_weights)
        blue_weights = self._normalize_weights(blue_weights)

        # 使用加权随机选择，生成多组候选
        candidates = []
        for _ in range(20):  # 生成20组候选
            red_nums = self._weighted_select(red_weights, self.config["red_range"][1], self.config["red_count"])
            blue_nums = self._weighted_select(blue_weights, self.config["blue_range"][1], self.config["blue_count"])
            candidates.append((red_nums, blue_nums))

        # 选择最优候选（综合评分最高）
        best_candidate = max(candidates, key=lambda c: self._evaluate_candidate(c[0], c[1], red_counter, blue_counter, consecutive_stats))

        return {
            "red_balls": [f"{n:02d}" for n in sorted(best_candidate[0])],
            "blue_balls": [f"{n:02d}" for n in sorted(best_candidate[1])],
            "method": "smart"
        }

    def _calc_frequency_scores(self, counter: Counter) -> Dict[int, float]:
        """计算频率得分 (0-100)"""
        if not counter:
            return {}

        max_freq = max(counter.values()) if counter else 1
        min_freq = min(counter.values()) if counter else 0

        scores = {}
        for num in counter:
            # 归一化到 0-100
            if max_freq > min_freq:
                scores[num] = 50 + 50 * (counter[num] - min_freq) / (max_freq - min_freq)
            else:
                scores[num] = 75  # 默认中等分数

        return scores

    def _calc_missing_scores(self, missing: Dict, ball_range: int) -> Dict[int, float]:
        """计算遗漏值得分 (遗漏值越接近理论平均值越好)"""
        if not missing:
            return {n: 70 for n in range(1, ball_range + 1)}

        # 理论平均遗漏值 = 总期数 / 号码个数
        total = sum(missing.values()) / len(missing) if missing else 10

        scores = {}
        for n in range(1, ball_range + 1):
            miss = missing.get(n, total * 2)
            # 遗漏值越接近平均值，分数越高
            diff = abs(miss - total)
            scores[n] = max(20, 100 - diff * 5)

        return scores

    def _calc_tail_scores(self, tail_dist: Dict) -> Dict[int, float]:
        """计算尾数得分 (避免选择同尾号过多的组合)"""
        if not tail_dist:
            return {n: 70 for n in range(10)}

        # 统计每个尾数已出现的次数
        tail_count = {int(k): v for k, v in tail_dist.items()}

        scores = {}
        for t in range(10):
            count = tail_count.get(t, 0)
            # 出现次数少的尾数分数高
            max_count = max(tail_count.values()) if tail_count else 1
            scores[t] = 30 + 70 * (1 - count / max_count) if max_count > 0 else 70

        return scores

    def _calc_odd_even_scores(self, odd_even_dist: Dict) -> Dict[int, float]:
        """计算奇偶得分 (根据历史最常见的奇偶比)"""
        if not odd_even_dist:
            return {n: 70 for n in range(1, 34)}

        # 找出最常见的奇偶比
        most_common = max(odd_even_dist.items(), key=lambda x: x[1])[0]
        odd_count, even_count = map(int, most_common.split(':'))

        scores = {}
        for n in range(1, 34):
            is_odd = n % 2 == 1
            # 如果该位置的奇偶性与最常见的比例匹配，给高分
            expected_odd_ratio = odd_count / (odd_count + even_count) if (odd_count + even_count) > 0 else 0.5

            if is_odd:
                scores[n] = 50 + 50 * expected_odd_ratio
            else:
                scores[n] = 50 + 50 * (1 - expected_odd_ratio)

        return scores

    def _normalize_weights(self, weights: Dict[int, float]) -> Dict[int, float]:
        """归一化权重为概率分布"""
        total = sum(weights.values())
        if total == 0:
            # 如果全是0，返回均匀分布
            count = len(weights)
            return {k: 1.0 / count for k in weights}
        return {k: v / total for k, v in weights.items()}

    def _weighted_select(self, weights: Dict[int, float], ball_range: int, count: int) -> List[int]:
        """基于权重随机选择号码"""
        numbers = list(range(1, ball_range + 1))
        probs = [weights.get(n, 0) for n in numbers]

        # 如果所有权重为0，使用均匀分布
        if sum(probs) == 0:
            probs = [1.0 / ball_range] * ball_range

        selected = random.choices(numbers, weights=probs, k=count)
        selected = sorted(set(selected))

        # 如果去重后数量不够，随机补充
        while len(selected) < count:
            remaining = [n for n in numbers if n not in selected]
            if remaining:
                selected.append(random.choice(remaining))
            selected = sorted(selected)

        return selected

    def _evaluate_candidate(self, red_nums: List[int], blue_nums: List[int],
                           red_counter: Counter, blue_counter: Counter,
                           consecutive_stats: Dict) -> float:
        """
        评估候选号码组合的优劣

        返回综合评分 (越高越好)
        """
        score = 0

        # 1. 频率得分 (号码总出现次数)
        score += sum(red_counter.get(n, 0) for n in red_nums)
        score += sum(blue_counter.get(n, 0) for n in blue_nums) * 2  # 蓝球权重稍高

        # 2. 连号惩罚 (避免过多连号)
        red_sorted = sorted(red_nums)
        consecutive_count = 0
        for i in range(len(red_sorted) - 1):
            if red_sorted[i + 1] - red_sorted[i] == 1:
                consecutive_count += 1
        score -= consecutive_count * 5  # 每组连号扣5分

        # 3. 尾数多样性奖励 (不同尾数越多越好)
        red_tails = len(set(n % 10 for n in red_nums))
        score += red_tails * 3  # 每个不同尾数加3分

        # 4. 区间分布奖励 (号码分布在不同区间)
        if self.lottery_type == "ssq":
            ranges = [(1, 11), (12, 22), (23, 33)]
        else:
            ranges = [(1, 12), (13, 24), (25, 35)]

        range_count = 0
        for start, end in ranges:
            if any(start <= n <= end for n in red_nums):
                range_count += 1
        score += range_count * 4  # 每个有号码的区间加4分

        return score

    def _predict_by_frequency(self, records: List[Dict]) -> Dict:
        """基于频率的预测"""
        red_counter, blue_counter = self.analyze_frequency(records)

        # 红球：使用加权随机选择，频率高的概率大
        red_numbers = list(range(1, self.config["red_range"][1] + 1))
        red_weights = [red_counter.get(n, 0.5) for n in red_numbers]

        # 归一化权重
        total = sum(red_weights)
        red_weights = [w / total for w in red_weights]

        selected_red = random.choices(red_numbers, weights=red_weights, k=self.config["red_count"])
        selected_red = sorted(set(selected_red))  # 去重并排序

        # 如果去重后数量不够，随机补充
        while len(selected_red) < self.config["red_count"]:
            remaining = [n for n in red_numbers if n not in selected_red]
            if remaining:
                selected_red.append(random.choice(remaining))
            selected_red = sorted(selected_red)

        # 蓝球：类似加权随机
        blue_numbers = list(range(1, self.config["blue_range"][1] + 1))
        blue_weights = [blue_counter.get(n, 0.5) for n in blue_numbers]
        total = sum(blue_weights)
        blue_weights = [w / total for w in blue_weights]

        selected_blue = random.choices(blue_numbers, weights=blue_weights, k=self.config["blue_count"])
        selected_blue = sorted(set(selected_blue))

        while len(selected_blue) < self.config["blue_count"]:
            remaining = [n for n in blue_numbers if n not in selected_blue]
            if remaining:
                selected_blue.append(random.choice(remaining))
            selected_blue = sorted(selected_blue)

        return {
            "red_balls": [f"{n:02d}" for n in selected_red],
            "blue_balls": [f"{n:02d}" for n in selected_blue],
            "method": "frequency"
        }

    def _predict_by_hot_cold(self, records: List[Dict]) -> Dict:
        """基于冷热号的预测"""
        red_counter, blue_counter = self.analyze_frequency(records)
        red_hot, _ = self.analyze_hot_cold(red_counter, top_n=15)
        _, blue_hot = self.analyze_hot_cold(blue_counter, top_n=8)

        # 红球：优先从热号中选择3-4个，其余随机
        red_numbers = list(range(1, self.config["red_range"][1] + 1))

        if red_hot:
            selected_red = random.sample(red_hot, min(3, len(red_hot)))
        else:
            selected_red = []

        # 补充到所需数量
        while len(selected_red) < self.config["red_count"]:
            remaining = [n for n in red_numbers if n not in selected_red]
            if remaining:
                selected_red.append(random.choice(remaining))

        selected_red = sorted(selected_red)

        # 蓝球：优先从热号中选择
        blue_numbers = list(range(1, self.config["blue_range"][1] + 1))

        if blue_hot:
            selected_blue = random.sample(blue_hot, min(1, len(blue_hot)))
        else:
            selected_blue = []

        while len(selected_blue) < self.config["blue_count"]:
            remaining = [n for n in blue_numbers if n not in selected_blue]
            if remaining:
                selected_blue.append(random.choice(remaining))

        selected_blue = sorted(selected_blue)

        return {
            "red_balls": [f"{n:02d}" for n in selected_red],
            "blue_balls": [f"{n:02d}" for n in selected_blue],
            "method": "hot_cold"
        }

    def _predict_by_missing(self, records: List[Dict]) -> Dict:
        """基于遗漏值的预测（选择遗漏值适中的号码）"""
        missing = self.analyze_missing(records)

        red_range = range(1, self.config["red_range"][1] + 1)
        blue_range = range(1, self.config["blue_range"][1] + 1)

        # 遗漏值排序，选择中间值
        red_missing = {n: missing.get(n, 50) for n in red_range}
        blue_missing = {n: missing.get(n, 50) for n in blue_range}

        # 遗漏值在平均值附近的号码权重较高
        red_mid = sorted(red_missing.values())[len(red_missing) // 2]
        blue_mid = sorted(blue_missing.values())[len(blue_missing) // 2]

        red_weights = [1 / (1 + abs(v - red_mid)) for v in red_missing.values()]
        blue_weights = [1 / (1 + abs(v - blue_mid)) for v in blue_missing.values()]

        total_red = sum(red_weights)
        red_weights = [w / total_red for w in red_weights]
        total_blue = sum(blue_weights)
        blue_weights = [w / total_blue for w in blue_weights]

        selected_red = random.choices(list(red_range), weights=red_weights, k=self.config["red_count"])
        selected_red = sorted(set(selected_red))

        while len(selected_red) < self.config["red_count"]:
            remaining = [n for n in red_range if n not in selected_red]
            if remaining:
                selected_red.append(random.choice(remaining))
            selected_red = sorted(selected_red)

        selected_blue = random.choices(list(blue_range), weights=blue_weights, k=self.config["blue_count"])
        selected_blue = sorted(set(selected_blue))

        while len(selected_blue) < self.config["blue_count"]:
            remaining = [n for n in blue_range if n not in selected_blue]
            if remaining:
                selected_blue.append(random.choice(remaining))
            selected_blue = sorted(selected_blue)

        return {
            "red_balls": [f"{n:02d}" for n in selected_red],
            "blue_balls": [f"{n:02d}" for n in selected_blue],
            "method": "missing"
        }

    def _generate_random_prediction(self, count: int) -> List[Dict]:
        """生成随机预测（无历史数据时使用）"""
        predictions = []

        for _ in range(count):
            red_range = range(1, self.config["red_range"][1] + 1)
            blue_range = range(1, self.config["blue_range"][1] + 1)

            selected_red = sorted(random.sample(red_range, self.config["red_count"]))
            selected_blue = sorted(random.sample(blue_range, self.config["blue_count"]))

            predictions.append({
                "red_balls": [f"{n:02d}" for n in selected_red],
                "blue_balls": [f"{n:02d}" for n in selected_blue],
                "method": "random"
            })

        return predictions

    def get_statistics(self) -> Dict:
        """获取统计数据"""
        records = self.get_history_data(limit=100)

        if not records:
            return {"error": "暂无足够数据进行统计分析"}

        red_counter, blue_counter = self.analyze_frequency(records)
        odd_even_dist = self.analyze_odd_even(records)
        range_dist = self.analyze_range(records)

        # 最热和最冷的号码
        red_hot, red_cold = self.analyze_hot_cold(red_counter, top_n=10)
        blue_hot, blue_cold = self.analyze_hot_cold(blue_counter, top_n=6)

        return {
            "lottery_type": self.lottery_type,
            "lottery_name": self.config["name"],
            "total_records": len(records),
            "red_frequency": dict(red_counter.most_common(20)),
            "blue_frequency": dict(blue_counter.most_common(10)),
            "red_hot": red_hot,
            "red_cold": red_cold,
            "blue_hot": blue_hot,
            "blue_cold": blue_cold,
            "odd_even_distribution": odd_even_dist,
            "range_distribution": range_dist,
            # 新增统计数据
            "missing_distribution": self.analyze_missing_distribution(records),
            "tail_distribution": self.analyze_tail(records),
            "sum_distribution": self.analyze_sum(records),
            "consecutive_stats": self.analyze_consecutive(records),
        }


def predict(lottery_type: str, method: str = "frequency", count: int = 1) -> List[Dict]:
    """
    预测接口函数

    Args:
        lottery_type: 彩种类型
        method: 预测方法
        count: 生成注数

    Returns:
        预测结果列表
    """
    predictor = StatisticalPredictor(lottery_type)
    return predictor.generate_prediction(method=method, count=count)


def get_statistics(lottery_type: str) -> Dict:
    """
    获取统计数据

    Args:
        lottery_type: 彩种类型

    Returns:
        统计数据
    """
    predictor = StatisticalPredictor(lottery_type)
    return predictor.get_statistics()
