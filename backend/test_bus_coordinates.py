"""
測試公車路線經緯度資料取得
測試路線：藍15
"""
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_bus_route_coordinates():
    """測試公車路線站點經緯度"""
    from bus_tdx_service import get_bus_service

    service = get_bus_service()
    route_name = "藍23"

    print("=" * 60)
    print(f"測試路線：{route_name}")
    print("=" * 60)

    # 1. 先搜尋路線找到所屬縣市
    all_routes = await service.get_all_taipei_routes()
    route_info = None
    city = "Taipei"

    for r in all_routes:
        route_name_zh = r.get("RouteName", {}).get("Zh_tw", "")
        if route_name_zh == route_name:
            route_info = r
            city = r.get("City", "Taipei")
            break

    if not route_info:
        print(f"[ERR] 找不到路線 {route_name}")
        return

    print(f"[OK] 找到路線：{route_name}（{city}）")
    print(f"   起點：{route_info.get('DepartureStopName', 'N/A')}")
    print(f"   終點：{route_info.get('DestinationStopName', 'N/A')}")

    # 2. 取得路線站點資料
    route_stops_data = await service.get_route_stops(route_name, city, direction=0)
    print(f"[OK] 取得 {len(route_stops_data)} 筆站點順序資料")

    # 3. 收集所有站點 UID
    all_stop_uids = []
    for route_stop in route_stops_data:
        route_stop_direction = route_stop.get("Direction", 0)
        if route_stop_direction != 0:
            continue
        stops_list = route_stop.get("Stops", [])
        for stop in stops_list:
            stop_uid = stop.get("StopUID", "")
            if stop_uid:
                all_stop_uids.append(stop_uid)

    print(f"[OK] 收集到 {len(all_stop_uids)} 個站點 UID")

    # 4. 取得站點位置快取
    stop_positions = await service.get_stop_positions_batch(all_stop_uids)
    print(f"[OK] 取得 {len(stop_positions)} 個站點的經緯度資料")

    # 5. 顯示每個站點的經緯度
    print("\n" + "=" * 60)
    print("站點經緯度資料：")
    print("=" * 60)

    found_count = 0
    missing_count = 0

    for route_stop in route_stops_data:
        route_stop_direction = route_stop.get("Direction", 0)
        if route_stop_direction != 0:
            continue

        stops_list = route_stop.get("Stops", [])
        for stop in stops_list:
            stop_uid = stop.get("StopUID", "")
            stop_name = stop.get("StopName", {}).get("Zh_tw", "")
            stop_sequence = stop.get("StopSequence", 0)

            position = stop_positions.get(stop_uid, {})
            latitude = position.get("latitude")
            longitude = position.get("longitude")

            if latitude and longitude:
                print(f"  {stop_sequence:2d}. {stop_name:20s} | 經緯度: {latitude:.5f}, {longitude:.5f}")
                found_count += 1
            else:
                print(f"  {stop_sequence:2d}. {stop_name:20s} | [ERR] 無經緯度資料")
                missing_count += 1

    print("\n" + "=" * 60)
    print(f"統計：找到 {found_count} 個，缺少 {missing_count} 個")
    print("=" * 60)

    # 6. 顯示快取統計
    cache_stats = service.get_stop_position_cache_stats()
    print(f"\n快取統計：")
    print(f"  總站點數：{cache_stats['total_stops']}")
    print(f"  最後更新：{cache_stats['last_update']}")

if __name__ == "__main__":
    asyncio.run(test_bus_route_coordinates())
