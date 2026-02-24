"""
数据采集模块
从 https://datachart.500.com/ 爬取历史开奖数据
"""
import subprocess
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

# 彩票类型配置
LOTTERY_CONFIG = {
    "ssq": {  # 双色球
        "name": "双色球",
        "base_url": "https://datachart.500.com/ssq/history/newinc/history.php",
        "red_balls": 6,  # 红球数量
        "blue_balls": 1,  # 蓝球数量
    },
    "dlt": {  # 超级大乐透
        "name": "超级大乐透",
        "base_url": "https://datachart.500.com/dlt/history/newinc/history.php",
        "red_balls": 5,  # 前区红球
        "blue_balls": 2,  # 后区蓝球
    },
}


class LotteryCrawler:
    """彩票数据爬虫"""

    def __init__(self, timeout: int = 60):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://datachart.500.com/",
        }

    async def fetch_history(
        self,
        lottery_type: str,
        limit: int = 50,
        sort: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取历史开奖数据

        Args:
            lottery_type: 彩票类型 (ssq/dlt)
            limit: 获取期数
            sort: 排序方式 0=降序(最新), 1=升序(最旧)

        Returns:
            开奖数据列表
        """
        if lottery_type not in LOTTERY_CONFIG:
            raise ValueError(f"不支持的彩种: {lottery_type}")

        config = LOTTERY_CONFIG[lottery_type]
        url = f"{config['base_url']}?limit={limit}&sort={sort}"

        logger.info(f"正在爬取 {config['name']} 数据，共 {limit} 期...")

        # 使用curl获取页面（更稳定）
        try:
            result = subprocess.run(
                ['curl', '-s', '--max-time', '30', '--compressed', url],
                capture_output=True,
                timeout=35
            )
            if result.returncode != 0:
                raise Exception(f"curl failed: {result.stderr.decode('utf-8', errors='ignore')}")
            # 使用gbk解码，因为网站使用gbk编码
            html = result.stdout.decode('gbk', errors='ignore')
        except Exception as e:
            logger.error(f"获取 {config['name']} 数据失败: {e}")
            raise

        # 解析HTML数据
        data = self._parse_html(html, lottery_type, config)
        logger.info(f"成功解析 {len(data)} 条数据")
        return data

    def _parse_html(
        self,
        html: str,
        lottery_type: str,
        config: Dict
    ) -> List[Dict[str, Any]]:
        """解析HTML页面"""
        soup = BeautifulSoup(html, "html.parser")

        # 查找数据表格 - 通过id="tablelist"
        table = soup.find("table", id="tablelist")

        if not table:
            logger.warning("未找到数据表格 tablelist")
            return []

        results = []

        # 优先查找tbody#tdata，如果不存在则查找所有tr
        tbody = table.find("tbody", id="tdata")
        if tbody:
            rows = tbody.find_all("tr")
        else:
            # 兼容：跳过表头行，查找数据行
            rows = table.find_all("tr")[2:]  # 跳过前两行表头

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 8:
                continue

            try:
                # 根据彩种类型解析不同格式
                if lottery_type == "ssq":
                    record = self._parse_ssq_row(cells)
                elif lottery_type == "dlt":
                    record = self._parse_dlt_row(cells)
                else:
                    continue

                if record:
                    record["lottery_type"] = lottery_type
                    record["created_at"] = datetime.now().isoformat()
                    results.append(record)

            except Exception as e:
                logger.debug(f"解析行数据失败: {e}")
                continue

        return results

    def _parse_ssq_row(self, cells) -> Optional[Dict]:
        """解析双色球数据行"""
        # 双色球数据行结构 (16列):
        # [0]=期号, [1-6]=红球, [7]=蓝球, [8]=空,
        # [9]=奖池, [10]=一等奖注数, [11]=一等奖奖金, [12]=二等奖注数, [13]=二等奖奖金, [14]=总投注额, [15]=开奖日期

        issue = cells[0].get_text(strip=True)
        if not issue or not issue.isdigit() or len(issue) < 4:
            return None

        # 红球 (6个) - cells[1] 到 cells[6]
        red_balls = [
            cells[1].get_text(strip=True).zfill(2),
            cells[2].get_text(strip=True).zfill(2),
            cells[3].get_text(strip=True).zfill(2),
            cells[4].get_text(strip=True).zfill(2),
            cells[5].get_text(strip=True).zfill(2),
            cells[6].get_text(strip=True).zfill(2),
        ]

        # 蓝球 (1个) - cells[7]
        blue_ball = cells[7].get_text(strip=True).zfill(2)

        # 开奖日期 - 双色球在最后一列 [15]
        open_date = ""
        if len(cells) > 15:
            text = cells[15].get_text(strip=True)
            if text and '-' in text:
                open_date = text

        return {
            "issue": issue,
            "red_balls": ",".join(red_balls),
            "blue_ball": blue_ball,
            "open_date": open_date,
        }

    def _parse_dlt_row(self, cells) -> Optional[Dict]:
        """解析大乐透数据行"""
        # 大乐透数据行结构 (15列):
        # [0]=期号, [1-5]=前区, [6-7]=后区, [8]=奖池, [9]=一等奖注数, [10]=一等奖奖金,
        # [11]=二等奖注数, [12]=二等奖奖金, [13]=总投注额, [14]=开奖日期

        issue = cells[0].get_text(strip=True)
        if not issue or not issue.isdigit() or len(issue) < 4:
            return None

        # 前区红球 (5个) - cells[1] 到 cells[5]
        red_balls = [
            cells[1].get_text(strip=True).zfill(2),
            cells[2].get_text(strip=True).zfill(2),
            cells[3].get_text(strip=True).zfill(2),
            cells[4].get_text(strip=True).zfill(2),
            cells[5].get_text(strip=True).zfill(2),
        ]

        # 后区蓝球 (2个) - cells[6] 到 cells[7]
        blue_balls = [
            cells[6].get_text(strip=True).zfill(2),
            cells[7].get_text(strip=True).zfill(2),
        ]

        # 开奖日期 - 大乐透在 [14] 位置
        open_date = ""
        if len(cells) > 14:
            text = cells[14].get_text(strip=True)
            if text and '-' in text:
                open_date = text

        return {
            "issue": issue,
            "red_balls": ",".join(red_balls),
            "blue_ball": ",".join(blue_balls),
            "open_date": open_date,
        }


async def crawl_all_lotteries(limit: int = 50) -> Dict[str, List[Dict]]:
    """
    爬取所有支持彩种的历史数据
    """
    crawler = LotteryCrawler()
    results = {}

    for lottery_type in ["ssq", "dlt"]:
        try:
            data = await crawler.fetch_history(lottery_type, limit=limit)
            results[lottery_type] = data
        except Exception as e:
            logger.error(f"爬取 {lottery_type} 失败: {e}")
            results[lottery_type] = []

    return results


if __name__ == "__main__":
    # 测试爬虫
    import json

    async def test():
        logging.basicConfig(level=logging.INFO)

        crawler = LotteryCrawler()

        # 测试双色球
        print("=" * 50)
        print("测试爬取双色球数据...")
        ssq_data = await crawler.fetch_history("ssq", limit=5)
        print(f"双色球: 获取到 {len(ssq_data)} 条数据")
        if ssq_data:
            print(json.dumps(ssq_data[0], indent=2, ensure_ascii=False))

        # 测试大乐透
        print("=" * 50)
        print("测试爬取大乐透数据...")
        dlt_data = await crawler.fetch_history("dlt", limit=5)
        print(f"大乐透: 获取到 {len(dlt_data)} 条数据")
        if dlt_data:
            print(json.dumps(dlt_data[0], indent=2, ensure_ascii=False))

    asyncio.run(test())
