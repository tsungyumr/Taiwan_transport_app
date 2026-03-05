"""
台北市公車爬蟲簡易測試
Simple test for Taipei Bus Scraper
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.taipei_bus_scraper import TaipeiBusScraper, BusScraperError


async def simple_test():
    """簡易測試 - 直接測試核心 API 功能"""
    print("=" * 60)
    print("Taipei Bus Scraper Test")
    print("=" * 60)

    async with TaipeiBusScraper(headless=True, timeout=45) as scraper:
        # Test: Get route info (Bus 307)
        print("\n[Test] Getting Bus 307 info...")
        try:
            # Route ID for 307
            route_id = "0100030700"
            route = await scraper.get_route_info(route_id)

            print(f"Success!")
            print(f"  Route name: {route.route_name}")
            print(f"  Total stops: {len(route.stops)}")

            if route.stops:
                print(f"\n  First 5 stops:")
                for stop in route.stops[:5]:
                    eta_str = "Arriving" if stop.eta == 0 else (f"{stop.eta} min" if stop.eta else "Not departed")
                    print(f"    {stop.sequence}. {stop.name} ({eta_str})")

                # Export to JSON for verification
                output_file = Path(__file__).parent / "test_output.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(route.to_dict(), f, ensure_ascii=False, indent=2)
                print(f"\nData exported to: {output_file}")

            print("\n[PASS] Test completed successfully!")
            return True

        except Exception as e:
            print(f"\n[FAIL] Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = asyncio.run(simple_test())
    sys.exit(0 if success else 1)
