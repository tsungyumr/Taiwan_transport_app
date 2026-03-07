"""Debug script to check why stops are not found"""
import sys
sys.path.insert(0, 'D:/source/Taiwan_transport_app/backend')

from services.ntpc_bus_service import NTPCBusService
import asyncio

async def main():
    service = NTPCBusService('data/ntpc_bus')
    await service.initialize()

    print(f"Total routes: {len(service._routes)}")
    print(f"Total stops keys: {len(service._stops)}")

    # Check route 935
    route_info = service.get_route('16562')
    if route_info:
        print(f"\nRoute 16562 found: {route_info.name_zh}")
    else:
        print("\nRoute 16562 not found")

    # Search by name
    routes = service.search_routes('935')
    print(f"\nSearch '935': found {len(routes)} routes")
    for r in routes:
        if r.name_zh == '935':
            print(f"  - route_id: {r.route_id}, name: {r.name_zh}")

    # Check stops for route 16562
    key_0 = "16562_0"
    key_1 = "16562_1"
    print(f"\nLooking for stops with key: {key_0}")
    print(f"  Found: {key_0 in service._stops}")
    if key_0 in service._stops:
        print(f"  Count: {len(service._stops[key_0])}")

    print(f"\nLooking for stops with key: {key_1}")
    print(f"  Found: {key_1 in service._stops}")
    if key_1 in service._stops:
        print(f"  Count: {len(service._stops[key_1])}")

    # List all keys containing 16562
    print("\nAll stop keys containing 16562:")
    for key in service._stops.keys():
        if '16562' in key:
            print(f"  - {key}: {len(service._stops[key])} stops")

    # Check get_route_stops
    stops_0 = service.get_route_stops('16562', 0)
    stops_1 = service.get_route_stops('16562', 1)
    print(f"\nget_route_stops('16562', 0): {len(stops_0)} stops")
    print(f"get_route_stops('16562', 1): {len(stops_1)} stops")

if __name__ == "__main__":
    asyncio.run(main())
