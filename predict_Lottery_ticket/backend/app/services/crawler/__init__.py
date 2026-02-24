"""
爬虫模块 __init__.py
"""
from .spider import LotteryCrawler, crawl_all_lotteries, LOTTERY_CONFIG

__all__ = ["LotteryCrawler", "crawl_all_lotteries", "LOTTERY_CONFIG"]
