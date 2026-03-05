# -*- coding: utf-8 -*-
"""
Direct test for Blue routes
"""
import asyncio
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

from scrapers.taipei_bus_scraper import TaipeiBusScraper

async def test_route(route_name):
    print(f"\n{'='*60}")
    print(f"Testing route: {route_name}")
    print(f"{'='*60}")

    try:
        async with TaipeiBusScraper(headless=True) as scraper:
            # Test get_route_id
            print("\n1. Testing get_route_id...")
            try:
                route_id = await scraper.get_route_id(route_name)
                print(f"   [OK] Found ID: {route_id}")
            except Exception as e:
                print(f"   [FAIL] get_route_id failed: {e}")
                import traceback
                traceback.print_exc()
                return

            # Test get_route_info
            print("\n2. Testing get_route_info...")
            try:
                route_info = await scraper.get_route_info(route_name, direction=0)
                print(f"   [OK] Route name: {route_info.route_name}")
                print(f"   [OK] Stops count: {len(route_info.stops)}")
                if route_info.stops:
                    stops_str = ', '.join([s.name for s in route_info.stops[:3]])
                    print(f"   [OK] First 3 stops: {stops_str}")
            except Exception as e:
                print(f"   [FAIL] get_route_info failed: {e}")
                import traceback
                traceback.print_exc()

    except Exception as e:
        print(f"[FAIL] Overall error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    await test_route("藍15")
    await asyncio.sleep(2)
    await test_route("藍22")
    await asyncio.sleep(2)
    await test_route("藍23")

if __name__ == "__main__":
    # Set UTF-8 for Windows
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    asyncio.run(main())
