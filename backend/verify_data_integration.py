"""
新北市公車資料整合驗證
測試資料載入、搜尋與關聯功能
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from services.ntpc_bus_service import NTPCBusService


async def test_data_loading():
    """測試資料載入"""
    print("\n【測試資料載入】")

    service = NTPCBusService('./data/ntpc_bus')

    # 載入現有資料（不下載）
    service.load_data()

    # 驗證路線資料
    routes = service.get_all_routes()
    print(f"  載入路線數量: {len(routes)}")
    assert len(routes) > 0, "應該有路線資料"

    # 顯示前5個路線
    print("\n  前5個路線:")
    for i, route in enumerate(routes[:5], 1):
        print(f"    {i}. {route.route_id} - {route.name_zh} ({route.provider_name})")
        print(f"       {route.departure_zh} → {route.destination_zh}")

    # 驗證站牌資料
    total_stops = sum(len(stops) for stops in service._stops.values())
    print(f"\n  載入站牌數量: {total_stops}")

    # 驗證到站預估資料
    print(f"  載入到站預估數量: {len(service._estimations)}")

    await service.close()
    print("  [OK] 資料載入測試通過")


async def test_route_search():
    """測試路線搜尋"""
    print("\n【測試路線搜尋】")

    service = NTPCBusService('./data/ntpc_bus')
    service.load_data()

    # 搜尋特定路線
    test_keywords = ['935', '台北', '板橋']

    for keyword in test_keywords:
        results = service.search_routes(keyword)
        print(f"\n  搜尋 '{keyword}': 找到 {len(results)} 個結果")

        for route in results[:3]:
            print(f"    - {route.route_id}: {route.departure_zh} → {route.destination_zh}")

    await service.close()
    print("  [OK] 路線搜尋測試通過")


async def test_route_stops():
    """測試路線站牌查詢"""
    print("\n【測試路線站牌查詢】")

    service = NTPCBusService('./data/ntpc_bus')
    service.load_data()

    # 找一個有站牌的路線
    found = False
    for route in service.get_all_routes():
        stops = service.get_route_stops(route.route_id, direction=0)
        if stops:
            found = True
            print(f"\n  路線 {route.route_id} ({route.name_zh})")
            print(f"  方向: 往{route.destination_zh}")
            print(f"  站牌數量: {len(stops)}")
            print("\n  前10個站牌:")

            for i, stop in enumerate(stops[:10], 1):
                print(f"    {stop.sequence:2d}. {stop.name_zh}")

            break

    if not found:
        print("  [WARN] 未找到有站牌的路線")

    await service.close()
    print("  [OK] 路線站牌查詢測試通過")


async def test_route_with_eta():
    """測試路線站牌與到站時間整合"""
    print("\n【測試路線站牌與到站時間整合】")

    service = NTPCBusService('./data/ntpc_bus')
    service.load_data()

    # 找一個有站牌的路線
    found = False
    for route in service.get_all_routes():
        stops_with_eta = service.get_route_stops_with_eta(route.route_id, direction=0)
        if stops_with_eta:
            found = True
            print(f"\n  路線 {route.route_id} ({route.name_zh})")
            print(f"  方向: 往{route.destination_zh}")
            print("\n  前10個站牌與到站時間:")

            for stop in stops_with_eta[:10]:
                status_icon = {
                    'not_started': '-',
                    'arriving': '>>',
                    'near': '>',
                    'normal': ' '
                }.get(stop.status, ' ')

                print(f"    {stop.sequence:2d}. [{status_icon:2s}] {stop.name_zh:15s} - {stop.estimate_text}")

            break

    if not found:
        print("  [WARN] 未找到有站牌的路線")

    await service.close()
    print("  [OK] 路線站牌與到站時間整合測試通過")


async def test_route_details():
    """測試路線詳細資訊"""
    print("\n【測試路線詳細資訊】")

    service = NTPCBusService('./data/ntpc_bus')
    service.load_data()

    # 取得路線摘要
    summaries = service.get_route_summaries()
    print(f"  路線摘要數量: {len(summaries)}")

    # 顯示前3個路線摘要
    print("\n  前3個路線摘要:")
    for i, summary in enumerate(summaries[:3], 1):
        print(f"    {i}. {summary.route_id}")
        print(f"       業者: {summary.provider_name}")
        print(f"       起迄: {summary.departure_zh} → {summary.destination_zh}")
        if summary.first_bus_time:
            print(f"       首末班: {summary.first_bus_time} - {summary.last_bus_time}")
        if summary.headway_desc:
            print(f"       發車間距: {summary.headway_desc}")

    await service.close()
    print("  [OK] 路線詳細資訊測試通過")


async def test_statistics():
    """測試資料統計"""
    print("\n【測試資料統計】")

    service = NTPCBusService('./data/ntpc_bus')
    service.load_data()

    routes = service.get_all_routes()

    # 統計資訊
    print(f"\n  總路線數: {len(routes)}")

    # 業者統計
    operators = {}
    for route in routes:
        op = route.provider_name
        operators[op] = operators.get(op, 0) + 1

    print(f"\n  前5大業者:")
    sorted_ops = sorted(operators.items(), key=lambda x: x[1], reverse=True)[:5]
    for op, count in sorted_ops:
        print(f"    - {op}: {count} 條路線")

    # 站牌統計
    total_stops = sum(len(stops) for stops in service._stops.values())
    avg_stops_per_route = total_stops / len(routes) if routes else 0
    print(f"\n  總站牌數: {total_stops}")
    print(f"  平均每路線站牌數: {avg_stops_per_route:.1f}")

    # 到站預估統計
    estimations = service._estimations
    print(f"\n  到站預估數: {len(estimations)}")

    await service.close()
    print("  [OK] 資料統計測試通過")


async def main():
    """主程式"""
    print("=" * 60)
    print("新北市公車資料整合驗證")
    print("=" * 60)

    try:
        await test_data_loading()
        await test_route_search()
        await test_route_stops()
        await test_route_with_eta()
        await test_route_details()
        await test_statistics()

        print("\n" + "=" * 60)
        print("所有測試通過！資料整合功能運作正常。")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n[FAIL] 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(asyncio.run(main()))
