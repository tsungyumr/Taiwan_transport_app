#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試公車路線方向切換 API
"""
import asyncio
import httpx


async def test_bus_route_directions():
    """測試取得不同方向的路線資料"""
    base_url = "http://localhost:8001"
    route = "藍15"

    print("=" * 60)
    print("測試公車路線方向切換 API")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=60.0) as client:
        # 測試去程 (direction=0)
        print(f"\n1. 測試去程 (direction=0)...")
        try:
            response = await client.get(f"{base_url}/api/bus/{route}?direction=0")
            if response.status_code == 200:
                data = response.json()
                print(f"   [OK] 成功取得去程資料")
                print(f"   - 路線: {data.get('route_name')}")
                print(f"   - 方向: {data.get('direction', {}).get('direction_name')}")
                print(f"   - 起站: {data.get('direction', {}).get('departure')}")
                print(f"   - 終站: {data.get('direction', {}).get('arrival')}")
                print(f"   - 站數: {len(data.get('stops', []))}")

                # 顯示雙向資訊
                go_info = data.get('direction', {}).get('go', {})
                back_info = data.get('direction', {}).get('back', {})
                print(f"\n   雙向資訊:")
                print(f"   - 去程往: {go_info.get('direction_name')}")
                print(f"   - 返程往: {back_info.get('direction_name')}")
            else:
                print(f"   [FAIL] 失敗: {response.status_code}")
                print(f"   {response.text[:200]}")
        except Exception as e:
            print(f"   [ERROR] 錯誤: {e}")

        # 測試返程 (direction=1)
        print(f"\n2. 測試返程 (direction=1)...")
        try:
            response = await client.get(f"{base_url}/api/bus/{route}?direction=1")
            if response.status_code == 200:
                data = response.json()
                print(f"   [OK] 成功取得返程資料")
                print(f"   - 路線: {data.get('route_name')}")
                print(f"   - 方向: {data.get('direction', {}).get('direction_name')}")
                print(f"   - 起站: {data.get('direction', {}).get('departure')}")
                print(f"   - 終站: {data.get('direction', {}).get('arrival')}")
                print(f"   - 站數: {len(data.get('stops', []))}")

                # 顯示前3個站點
                stops = data.get('stops', [])
                print(f"\n   前3個站點:")
                for i, stop in enumerate(stops[:3]):
                    print(f"   - {stop.get('sequence')}. {stop.get('name')}")
            else:
                print(f"   [FAIL] 失敗: {response.status_code}")
                print(f"   {response.text[:200]}")
        except Exception as e:
            print(f"   [ERROR] 錯誤: {e}")

    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_bus_route_directions())
