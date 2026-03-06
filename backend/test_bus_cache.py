"""
公車快取系統測試腳本
"""

import asyncio
import sys

# 添加項目根目錄到路徑
sys.path.insert(0, r'D:\source\Taiwan_transport_app\backend')

from cache.bus_cache_manager import TaipeiBusCacheManager


async def test_cache_manager():
    """測試快取管理器"""
    print("=" * 50)
    print("開始測試公車快取系統")
    print("=" * 50)

    # 建立快取管理器（設定為5秒更新一次，方便測試）
    manager = TaipeiBusCacheManager(update_interval=5)

    # 啟動快取管理器
    print("\n1. 啟動快取管理器...")
    await manager.start()
    print("✓ 快取管理器已啟動")

    # 等待第一次更新完成
    print("\n2. 等待第一次資料更新（約10秒）...")
    await asyncio.sleep(10)

    # 查詢快取狀態
    print("\n3. 查詢快取狀態...")
    status = await manager.get_cache_status()
    print(f"   快取狀態: {status}")

    # 測試取得路線列表
    print("\n4. 測試取得路線列表...")
    routes = await manager.get_all_routes()
    if routes:
        print(f"   ✓ 取得 {len(routes)} 條路線")
        print(f"   前5條路線: {[r.route_name for r in routes[:5]]}")
    else:
        print("   ✗ 未取得路線資料")

    # 測試取得特定路線資料
    print("\n5. 測試取得特定路線資料（藍15）...")
    route_data = await manager.get_route_data("藍15", direction=0)
    if route_data:
        print(f"   ✓ 取得路線資料: {route_data.route_name}")
        print(f"   站點數: {len(route_data.stops)}")
        print(f"   車輛數: {len(route_data.buses)}")
    else:
        print("   ✗ 快取中沒有藍15資料，嘗試手動更新...")
        success = await manager.refresh_route("藍15", 0)
        print(f"   手動更新結果: {'成功' if success else '失敗'}")

        # 再次查詢
        route_data = await manager.get_route_data("藍15", direction=0)
        if route_data:
            print(f"   ✓ 更新後取得路線資料: {route_data.route_name}")

    # 測試快取過期機制
    print("\n6. 等待快取過期並自動更新（約10秒）...")
    await asyncio.sleep(10)

    # 再次查詢狀態
    print("\n7. 再次查詢快取狀態...")
    status = await manager.get_cache_status()
    print(f"   快取狀態: {status}")

    # 停止快取管理器
    print("\n8. 停止快取管理器...")
    await manager.stop()
    print("✓ 快取管理器已停止")

    print("\n" + "=" * 50)
    print("測試完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_cache_manager())
