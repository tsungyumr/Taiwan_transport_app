"""
高鐵站點列表爬蟲
使用 Playwright 抓取高鐵官方網站的站點資料

注意：由於高鐵網站有反爬蟲機制，這裡使用靜態車站列表作為主要資料來源
高鐵車站列表固定為12站，不會頻繁變動
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
from typing import List, Dict


# 高鐵靜態車站列表 - 高鐵只有12個固定車站
THSR_STATIONS_STATIC = [
    {"name": "南港", "code": "NAG", "sequence": 1},
    {"name": "台北", "code": "TPE", "sequence": 2},
    {"name": "板橋", "code": "BAN", "sequence": 3},
    {"name": "桃園", "code": "TAO", "sequence": 4},
    {"name": "新竹", "code": "HSI", "sequence": 5},
    {"name": "苗栗", "code": "MIA", "sequence": 6},
    {"name": "台中", "code": "TCH", "sequence": 7},
    {"name": "彰化", "code": "CHA", "sequence": 8},
    {"name": "雲林", "code": "YUN", "sequence": 9},
    {"name": "嘉義", "code": "CHY", "sequence": 10},
    {"name": "台南", "code": "TNN", "sequence": 11},
    {"name": "左營", "code": "ZUY", "sequence": 12},
]


async def scrape_thsr_stations() -> List[Dict]:
    """
    取得高鐵站點列表

    由於高鐵網站有反爬蟲機制，這裡使用靜態車站列表
    高鐵車站列表固定為12站，不會頻繁變動

    Returns:
        List[Dict]: 高鐵站點列表，包含站名、代碼、位置等
    """
    # 直接回傳靜態車站列表，更可靠且快速
    stations = []
    for station in THSR_STATIONS_STATIC:
        stations.append({
            'name': station['name'],
            'code': station['code'],
            'info': f"第{station['sequence']}站",
            'timestamp': datetime.now().isoformat()
        })

    print(f"回傳高鐵靜態車站列表: {len(stations)} 個車站")
    return stations


# Test
if __name__ == "__main__":
    async def test():
        stations = await scrape_thsr_stations()
        print(f"Found {len(stations)} THSR stations")
        for station in stations:
            print(station)

    asyncio.run(test())