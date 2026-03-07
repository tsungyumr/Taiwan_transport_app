"""Debug API endpoint directly"""
import sys
sys.path.insert(0, 'D:/source/Taiwan_transport_app/backend')

import asyncio
import traceback
from services.ntpc_bus_service import NTPCBusService

async def test_api_logic():
    # Initialize services
    ntpc_service = NTPCBusService('data/ntpc_bus')
    await ntpc_service.initialize()

    route = "935"
    direction = 0

    print(f"Testing route={route}, direction={direction}")
    print("=" * 60)

    try:
        # Step 1: Try to get route by route_id
        route_info = ntpc_service.get_route(route)
        print(f"1. get_route('{route}'): {route_info}")

        if not route_info:
            # Step 2: Search by name
            print(f"2. Route not found by ID, searching by name...")
            matching_routes = ntpc_service.search_routes(route)
            print(f"   search_routes('{route}'): found {len(matching_routes)} routes")

            for r in matching_routes:
                print(f"   - route_id: {r.route_id}, name_zh: {r.name_zh}")
                if r.name_zh == route:
                    route_info = r
                    print(f"   -> Found match: {r.route_id}")
                    break

        if route_info:
            print(f"\n3. Using route_id: {route_info.route_id}")

            # Step 3: Get stops with ETA
            print(f"4. Calling get_route_stops_with_eta('{route_info.route_id}', {direction})...")
            stops_with_eta = ntpc_service.get_route_stops_with_eta(route_info.route_id, direction)
            print(f"5. Result: {len(stops_with_eta)} stops")

            if stops_with_eta:
                print("\n6. First few stops:")
                for stop in stops_with_eta[:3]:
                    print(f"   - {stop.name_zh}: {stop.estimate_text}")
                print("\n7. Returning stops data...")
            else:
                print("\n6. No stops found!")
        else:
            print("ERROR: route_info is None")
    except Exception as e:
        print(f"EXCEPTION: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_logic())
