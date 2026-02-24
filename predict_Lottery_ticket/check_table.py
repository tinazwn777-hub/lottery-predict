# -*- coding: utf-8 -*-
import httpx
import asyncio
from bs4 import BeautifulSoup
import sys
import io

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def check_table():
    # 双色球
    url = 'https://datachart.500.com/ssq/history/newinc/history.php?limit=3&sort=0'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        resp = await client.get(url)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table', id='tablelist')
        if table:
            rows = table.find_all('tr')
            print('SSQ: {} rows'.format(len(rows)))
            for i, row in enumerate(rows[:4]):
                cells = row.find_all(['td', 'th'])
                print('Row {}: {} cells'.format(i, len(cells)))
                for j, c in enumerate(cells[:15]):
                    txt = c.get_text(strip=True)
                    print('  [{}] {}'.format(j, txt[:20]))

    print('='*50)

    # 大乐透
    url = 'https://datachart.500.com/dlt/history/newinc/history.php?limit=3&sort=0'
    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        resp = await client.get(url)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table', id='tablelist')
        if table:
            rows = table.find_all('tr')
            print('DLT: {} rows'.format(len(rows)))
            for i, row in enumerate(rows[:4]):
                cells = row.find_all(['td', 'th'])
                print('Row {}: {} cells'.format(i, len(cells)))
                for j, c in enumerate(cells[:15]):
                    txt = c.get_text(strip=True)
                    print('  [{}] {}'.format(j, txt[:20]))

asyncio.run(check_table())
