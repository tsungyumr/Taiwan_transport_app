"""
測試動態路線 ID 搜尋功能
=======================

這個腳本測試修改後的動態搜尋功能，
驗證是否能正確找到各路線的真實 ID。

使用方法:
    cd backend
    python test_dynamic_search.py
"""

import asyncio
import sys
from scrapers.taipei_bus_scraper import TaipeiBusScraper

# 測試的路線列表
TEST_ROUTES = [
    "藍15",    # 已知正確的
    "藍1",
    "藍5",
    "307",     # 幹線公車
    "235",
    "232",
    "紅5",
    "紅30",
    "綠1",
    "棕12",
]


async def test_route_search(route_name: str, scraper: TaipeiBusScraper):
    """測試單個路線的 ID 搜尋"""
    print(f"\n{'='*50}")
    print(f"測試路線: {route_name}")
    print(f"{'='*50}")

    try:
        # 呼叫動態搜尋
        route_id = await scraper.get_route_id(route_name)
        print(f"✅ 找到 ID: {route_id}")

        # 嘗試取得路線資訊驗證
        route_info = await scraper.get_route_info(route_name, direction=0)
        print(f"✅ 路線名稱: {route_info.route_name}")
        print(f"✅ 站點數量: {len(route_info.stops)}")

        if route_info.stops:
            print(f"   前3站: {', '.join([s.name for s in route_info.stops[:3]])}")

        return True

    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return False


async def main():
    """主測試函數"""
    print("🚌 動態路線 ID 搜尋測試")
    print("=" * 60)

    success_count = 0
    fail_count = 0

    async with TaipeiBusScraper(headless=True) as scraper:
        for route in TEST_ROUTES:
            success = await test_route_search(route, scraper)
            if success:
                success_count += 1
            else:
                fail_count += 1

            # 每個路線測試間隔，避免對網站造成壓力
            await asyncio.sleep(1)

    print("\n" + "=" * 60)
    print("📊 測試結果統計")
    print("=" * 60)
    print(f"✅ 成功: {success_count}/{len(TEST_ROUTES)}")
    print(f"❌ 失敗: {fail_count}/{len(TEST_ROUTES)}")

    if fail_count == 0:
        print("\n🎉 所有測試通過！動態搜尋功能運作正常。")
    else:
        print(f"\n⚠️ 有 {fail_count} 個路線測試失敗，請檢查日誌。")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
