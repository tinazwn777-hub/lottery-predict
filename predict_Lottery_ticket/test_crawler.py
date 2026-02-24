# -*- coding: utf-8 -*-
import asyncio
import sys
import json
sys.path.insert(0, '.')

from backend.app.services.crawler.spider import LotteryCrawler

async def test():
    crawler = LotteryCrawler()

    # 测试双色球
    print('='*50)
    print('Testing SSQ crawler...')
    ssq_data = await crawler.fetch_history('ssq', limit=5)
    print(f'SSQ: Got {len(ssq_data)} records')
    if ssq_data:
        print(json.dumps(ssq_data[0], indent=2, ensure_ascii=False))

    # 测试大乐透
    print('='*50)
    print('Testing DLT crawler...')
    dlt_data = await crawler.fetch_history('dlt', limit=5)
    print(f'DLT: Got {len(dlt_data)} records')
    if dlt_data:
        print(json.dumps(dlt_data[0], indent=2, ensure_ascii=False))

asyncio.run(test())
