"""
新北市公車 API 測試
使用 httpx 測試 API 端點
"""

import asyncio
import httpx
import sys
from pathlib import Path

# API 基底 URL
BASE_URL = "http://localhost:8000"


async def test_get_routes():
    """測試取得路線列表"""
    print("\n【測試 GET /api/bus/routes】")

    async with httpx.AsyncClient() as client:
        # 測試取得所有路線
        response = await client.get(f"{BASE_URL}/api/bus/routes")
        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"  Routes count: {len(data)}")

            if data:
                print("\n  First 3 routes:")
                for route in data[:3]:
                    print(f"    - {route['route_id']}: {route['route_name']}")
                    print(f"      {route['departure_stop']} → {route['arrival_stop']}")

            return True
        else:
            print(f"  Error: {response.text}")
            return False


async def test_search_routes():
    """測試搜尋路線"""
    print("\n【測試 GET /api/bus/routes/search】")

    async with httpx.AsyncClient() as client:
        keywords = ["F623", "板橋", "台北"]

        for keyword in keywords:
            response = await client.get(
                f"{BASE_URL}/api/bus/routes/search",
                params={"keyword": keyword}
            )
            print(f"\n  Search '{keyword}':")
            print(f"    Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"    Results: {len(data)}")

                for route in data[:2]:
                    print(f"      - {route['route_id']}: {route['departure']} → {route['destination']}")


async def test_get_route_detail():
    """測試取得路線詳細資料"""
    print("\n【測試 GET /api/bus/{route}】")

    async with httpx.AsyncClient() as client:
        # 先取得一個路線 ID
        routes_response = await client.get(f"{BASE_URL}/api/bus/routes")
        if routes_response.status_code != 200:
            print("  Failed to get routes list")
            return

        routes = routes_response.json()
        if not routes:
            print("  No routes available")
            return

        # 測試第一個路線
        route_id = routes[0]['route_id']
        print(f"\n  Testing route: {route_id}")

        response = await client.get(f"{BASE_URL}/api/bus/{route_id}")
        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"  Route: {data['route']}")
            print(f"  Stops count: {len(data['stops'])}")
            print(f"  Buses count: {len(data['buses'])}")

            if data['stops']:
                print("\n  First 5 stops:")
                for stop in data['stops'][:5]:
                    print(f"    - {stop['name']}: {stop['eta']}")
        else:
            print(f"  Error: {response.text}")


async def test_get_route_stops():
    """測試取得路線站牌"""
    print("\n【測試 GET /api/bus/{route}/stops】")

    async with httpx.AsyncClient() as client:
        # 取得路線列表
        routes_response = await client.get(f"{BASE_URL}/api/bus/routes")
        if routes_response.status_code != 200:
            print("  Failed to get routes list")
            return

        routes = routes_response.json()
        if not routes:
            print("  No routes available")
            return

        # 測試第一個路線
        route_id = routes[0]['route_id']

        for direction in [0, 1]:
            print(f"\n  Direction {direction}:")

            response = await client.get(
                f"{BASE_URL}/api/bus/{route_id}/stops",
                params={"direction": direction}
            )
            print(f"    Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"    Stops count: {len(data['stops'])}")

                if data['stops']:
                    for stop in data['stops'][:3]:
                        print(f"      {stop['sequence']}. {stop['name']} - {stop['eta']}")


async def test_get_route_info():
    """測試取得路線資訊"""
    print("\n【測試 GET /api/bus/{route}/info】")

    async with httpx.AsyncClient() as client:
        routes_response = await client.get(f"{BASE_URL}/api/bus/routes")
        if routes_response.status_code != 200:
            print("  Failed to get routes list")
            return

        routes = routes_response.json()
        if not routes:
            print("  No routes available")
            return

        route_id = routes[0]['route_id']

        response = await client.get(f"{BASE_URL}/api/bus/{route_id}/info")
        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"  Route: {data['route_id']} - {data['route_name']}")
            print(f"  Operator: {data['operator']}")
            print(f"  Departure: {data['departure']}")
            print(f"  Destination: {data['destination']}")

            if data.get('go_first_bus_time'):
                print(f"  First bus: {data['go_first_bus_time']}")
            if data.get('go_last_bus_time'):
                print(f"  Last bus: {data['go_last_bus_time']}")


async def main():
    """主程式"""
    print("=" * 60)
    print("新北市公車 API 測試")
    print(f"API URL: {BASE_URL}")
    print("=" * 60)

    try:
        await test_get_routes()
        await test_search_routes()
        await test_get_route_detail()
        await test_get_route_stops()
        await test_get_route_info()

        print("\n" + "=" * 60)
        print("API 測試完成")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAIL] 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
