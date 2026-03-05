#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試從 eBus 網站抓取所有公車路線
"""
import asyncio
import sys
import os

# 添加 backend 目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.taipei_bus_scraper import TaipeiBusScraper


async def test_fetch_all_routes():
    """測試抓取所有路線"""
    print("=" * 60)
    print("測試從 eBus 網站抓取所有公車路線")
    print("=" * 60)

    async with TaipeiBusScraper(headless=False, timeout=30) as scraper:
        # 取得所有路線
        routes = await scraper.get_all_routes()

        print(f"\n總共抓取到 {len(routes)} 條路線")
        print("\n" + "=" * 60)

        # 搜尋藍色路線
        blue_routes = [r for r in routes if r.route_name.startswith('藍')]
        print(f"\n找到 {len(blue_routes)} 條藍色路線:")
        for route in sorted(blue_routes, key=lambda x: x.route_name):
            print(f"  {route.route_name}: {route.route_id} ({route.category})")

        # 檢查是否有藍13
        blue13 = [r for r in routes if r.route_name == '藍13']
        print("\n" + "=" * 60)
        if blue13:
            print(f"✓ 找到藍13: {blue13[0].route_id}")
        else:
            print("✗ 在 eBus 網站上找不到藍13")
            print("\n可能原因:")
            print("  1. 藍13可能不是大台北公車系統的路線")
            print("  2. 可能是新北市公車或其他系統")
            print("  3. 路線可能已停駛或更名")

        # 顯示所有路線的前50條
        print("\n" + "=" * 60)
        print("前50條路線預覽:")
        print("=" * 60)
        for route in routes[:50]:
            print(f"  {route.route_name:10} | {route.route_id} | {route.category}")

        # 搜尋特定路線（如果提供）
        if len(sys.argv) > 1:
            search_term = sys.argv[1]
            print(f"\n" + "=" * 60)
            print(f"搜尋路線 '{search_term}':")
            print("=" * 60)
            matching = [r for r in routes if search_term in r.route_name]
            if matching:
                for route in matching:
                    print(f"  {route.route_name}: {route.route_id}")
            else:
                print(f"  找不到包含 '{search_term}' 的路線")

    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_fetch_all_routes())
