"""
測試公車路線 API 回傳結果是否包含經緯度
"""
import asyncio
import json
from bus_tdx_service import get_bus_service

async def test_api_response():
    """測試 API 回傳結果"""

    try:
        bus_service = get_bus_service()
        route = "藍15"
        direction = 0

        # 搜尋路線
        all_routes = await bus_service.get_all_taipei_routes()
        route_info = None
        city = "Taipei"
        for r in all_routes:
            route_name = r.get("RouteName", {}).get("Zh_tw", "")
            if route_name == route:
                route_info = r
                city = r.get("City", "Taipei")
                break

        if not route_info:
            print(f"找不到路線 {route}")
            return

        print(f"找到路線: {route} ({city})")

        # 取得路線站點
        route_stops_data = await bus_service.get_route_stops(route, city, direction)
        print(f"取得 {len(route_stops_data)} 筆站點順序資料")

        # 收集所有站點 UID
        all_stop_uids = []
        for route_stop in route_stops_data:
            route_stop_direction = route_stop.get("Direction", 0)
            if route_stop_direction != direction:
                continue
            stops_list = route_stop.get("Stops", [])
            for stop in stops_list:
                stop_uid = stop.get("StopUID", "")
                if stop_uid:
                    all_stop_uids.append(stop_uid)

        print(f"收集到 {len(all_stop_uids)} 個站點 UID")

        # 取得站點位置
        stop_positions = await bus_service.get_stop_positions_batch(all_stop_uids)
        print(f"取得 {len(stop_positions)} 個站點的經緯度")

        # 模擬建立 BusStop 列表
        stops = []
        seen_stop_uids = set()
        seen_sequences = set()

        for route_stop in route_stops_data:
            route_stop_direction = route_stop.get("Direction", 0)
            if route_stop_direction != direction:
                continue

            stops_list = route_stop.get("Stops", [])
            for stop in stops_list:
                stop_uid = stop.get("StopUID", "")
                stop_name = stop.get("StopName", {}).get("Zh_tw", "")
                stop_sequence = stop.get("StopSequence", 0)

                if stop_uid and stop_uid in seen_stop_uids:
                    continue
                if stop_sequence in seen_sequences:
                    continue

                if stop_uid:
                    seen_stop_uids.add(stop_uid)
                seen_sequences.add(stop_sequence)

                # 取得站點經緯度
                position = stop_positions.get(stop_uid, {})
                latitude = position.get("latitude")
                longitude = position.get("longitude")

                stops.append({
                    "sequence": stop_sequence,
                    "name": stop_name,
                    "eta": "未發車",
                    "status": "normal",
                    "buses": [],
                    "latitude": latitude,
                    "longitude": longitude
                })

        stops.sort(key=lambda x: x["sequence"])

        print(f"\n建立 {len(stops)} 個站點")
        print("\n前5個站點:")
        for stop in stops[:5]:
            print(f"  {stop['sequence']}. {stop['name']}")
            print(f"     經緯度: lat={stop['latitude']}, lon={stop['longitude']}")

        # 轉換為 JSON 檢查
        print("\n第一個站點的 JSON 格式:")
        print(json.dumps(stops[0], ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_response())
