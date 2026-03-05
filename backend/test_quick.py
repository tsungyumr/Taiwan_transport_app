# -*- coding: utf-8 -*-
"""Quick test for blue routes"""
import asyncio
import sys
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from scrapers.taipei_bus_scraper import TaipeiBusScraper

async def test_route(route_name):
    print(f"\n{'='*60}")
    print(f"Testing: {route_name}")
    print(f"{'='*60}")

    try:
        async with TaipeiBusScraper(headless=True) as scraper:
            # Test get_route_id
            print("\n1. Testing get_route_id...")
            try:
                route_id = await scraper.get_route_id(route_name)
                print(f"   [OK] Found ID: {route_id}")
            except Exception as e:
                print(f"   [FAIL] {e}")
                return False

            # Test get_route_info
            print("\n2. Testing get_route_info...")
            try:
                route_info = await scraper.get_route_info(route_name, direction=0)
                print(f"   [OK] Route: {route_info.route_name}")
                print(f"   [OK] Stops: {len(route_info.stops)}")
                if route_info.stops:
                    stops = ', '.join([s.name for s in route_info.stops[:3]])
                    print(f"   [OK] First 3: {stops}")
                return True
            except Exception as e:
                print(f"   [FAIL] {e}")
                return False

    except Exception as e:
        print(f"[FAIL] {e}")
        return False

async def main():
    results = []
    for route in ["藍15", "藍22", "藍23"]:
        success = await test_route(route)
        results.append((route, success))
        await asyncio.sleep(2)

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for route, success in results:
        status = "OK" if success else "FAIL"
        print(f"  {route}: {status}")

if __name__ == "__main__":
    asyncio.run(main())
