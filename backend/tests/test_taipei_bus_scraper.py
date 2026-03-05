"""
台北市公車爬蟲測試
Test for Taipei Bus Scraper

這個測試檔案用於驗證 taipei_bus_scraper.py 的各項功能是否正常運作。
"""

import asyncio
import json
import sys
from pathlib import Path

# 將上層目錄加入模組搜尋路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.taipei_bus_scraper import (
    TaipeiBusScraper,
    BusScraperError,
    format_eta
)


async def test_search_routes():
    """測試搜尋路線功能"""
    print("\n" + "=" * 60)
    print("測試 1: 搜尋路線")
    print("=" * 60)

    async with TaipeiBusScraper(headless=True) as scraper:
        # 測試搜尋特定路線
        keyword = "307"
        print(f"\n搜尋關鍵字: '{keyword}'")

        routes = await scraper.search_routes(keyword)

        print(f"找到 {len(routes)} 條符合的路線")

        assert len(routes) > 0, f"應該要找到 '{keyword}' 相關的路線"

        for route in routes[:3]:
            print(f"  - {route.route_name}: {route.description}")
            assert route.route_id, "路線ID不應為空"
            assert route.route_name, "路線名稱不應為空"

        print("✓ 搜尋路線測試通過")
        return routes[0].route_id if routes else None


async def test_get_route_info(route_id: str):
    """測試取得路線詳細資訊"""
    print("\n" + "=" * 60)
    print("測試 2: 取得路線詳細資訊")
    print("=" * 60)

    async with TaipeiBusScraper(headless=True) as scraper:
        print(f"\n取得路線 ID: {route_id}")

        route = await scraper.get_route_info(route_id)

        print(f"路線名稱: {route.route_name}")
        print(f"業者: {route.operator or '未知'}")
        print(f"方向: {'去程' if route.direction == 0 else '返程'}")
        print(f"站牌數量: {len(route.stops)}")

        # 驗證資料完整性
        assert route.route_id == route_id, "路線ID應該相符"
        assert len(route.stops) > 0, "應該要有站牌資料"

        # 驗證站牌資料
        for stop in route.stops[:5]:
            print(f"  {stop.sequence}. {stop.name} (ETA: {format_eta(stop.eta)})")
            assert stop.sequence > 0, "站序應該大於0"
            assert stop.name, "站名不應為空"

        print("✓ 取得路線詳細資訊測試通過")
        return route


async def test_get_both_directions(route_id: str):
    """測試取得雙向路線資訊"""
    print("\n" + "=" * 60)
    print("測試 3: 取得雙向路線資訊")
    print("=" * 60)

    async with TaipeiBusScraper(headless=True) as scraper:
        print(f"\n取得路線 ID: {route_id} 的雙向資訊")

        routes = await scraper.get_route_both_directions(route_id)

        print(f"成功取得 {len(routes)} 個方向的資料")

        for direction, route_data in routes.items():
            direction_name = "去程" if direction == 0 else "返程"
            print(f"  {direction_name}: {route_data.route_name}, {len(route_data.stops)} 站")

        # 驗證至少有一個方向的資料
        assert len(routes) > 0, "應該至少有一個方向的資料"

        print("✓ 取得雙向路線資訊測試通過")


async def test_error_handling():
    """測試錯誤處理"""
    print("\n" + "=" * 60)
    print("測試 4: 錯誤處理")
    print("=" * 60)

    async with TaipeiBusScraper(headless=True) as scraper:
        # 測試無效的路線ID
        print("\n測試無效的路線ID...")
        try:
            await scraper.get_route_info("INVALID_ROUTE_ID_99999")
            assert False, "應該要拋出例外"
        except BusScraperError as e:
            print(f"  預期的錯誤: {e}")
            print("✓ 錯誤處理測試通過")


async def test_data_export(route):
    """測試資料匯出功能"""
    print("\n" + "=" * 60)
    print("測試 5: 資料匯出")
    print("=" * 60)

    # 測試 to_dict 方法
    route_dict = route.to_dict()

    print(f"\n路線資料結構:")
    print(f"  - route_id: {route_dict['route_id']}")
    print(f"  - route_name: {route_dict['route_name']}")
    print(f"  - total_stops: {route_dict['total_stops']}")
    print(f"  - stops: {len(route_dict['stops'])} 個站牌")

    # 驗證 JSON 序列化
    try:
        json_str = json.dumps(route_dict, ensure_ascii=False, indent=2)
        print(f"\nJSON 序列化成功，長度: {len(json_str)} 字元")

        # 驗證 JSON 反序列化
        parsed = json.loads(json_str)
        assert parsed['route_id'] == route.route_id, "JSON 反序列化後 route_id 應該相符"

        print("✓ 資料匯出測試通過")
    except Exception as e:
        print(f"✗ JSON 序列化失敗: {e}")
        raise


async def run_all_tests():
    """執行所有測試"""
    print("\n" + "█" * 60)
    print("開始執行台北市公車爬蟲測試")
    print("█" * 60)

    try:
        # 測試 1: 搜尋路線
        route_id = await test_search_routes()

        if not route_id:
            print("\n✗ 無法取得路線ID，停止測試")
            return False

        # 測試 2: 取得路線詳細資訊
        route = await test_get_route_info(route_id)

        # 測試 3: 取得雙向路線資訊
        await test_get_both_directions(route_id)

        # 測試 4: 錯誤處理
        await test_error_handling()

        # 測試 5: 資料匯出
        await test_data_export(route)

        print("\n" + "█" * 60)
        print("所有測試通過！✓")
        print("█" * 60)
        return True

    except AssertionError as e:
        print(f"\n✗ 測試斷言失敗: {e}")
        return False
    except Exception as e:
        print(f"\n✗ 測試執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
