"""Complete API simulation test"""
import sys
sys.path.insert(0, 'D:/source/Taiwan_transport_app/backend')

import asyncio
import traceback
from datetime import datetime
from services.ntpc_bus_service import NTPCBusService
from pydantic import BaseModel, Field
from typing import List, Optional

# Copy models from main.py
class BusStop(BaseModel):
    sequence: int
    name: str
    eta: str
    status: str
    buses: List[dict]

class BusVehicle(BaseModel):
    id: str
    plate_number: str
    bus_type: str
    at_stop: int
    eta_next: str
    heading_to: int
    remaining_seats: Optional[int] = None

class DirectionDetail(BaseModel):
    direction: int
    direction_name: str
    departure: str
    arrival: str

class DirectionInfo(BaseModel):
    direction: int
    direction_name: str
    departure: str
    arrival: str
    go: DirectionDetail
    back: DirectionDetail

class BusRouteData(BaseModel):
    route: str
    route_name: str
    direction: DirectionInfo
    stops: List[BusStop]
    buses: List[BusVehicle]
    updated: str

async def test_full_api():
    ntpc_service = NTPCBusService('data/ntpc_bus')
    await ntpc_service.initialize()

    route = "935"
    direction = 0

    print(f"Testing full API flow: route={route}, direction={direction}")
    print("=" * 60)

    try:
        # Step 1: Find route
        route_info = ntpc_service.get_route(route)
        if not route_info:
            matching_routes = ntpc_service.search_routes(route)
            for r in matching_routes:
                if r.name_zh == route:
                    route_info = r
                    break
            if not route_info and matching_routes:
                route_info = matching_routes[0]

        if not route_info:
            print("ERROR: Route not found")
            return

        print(f"1. Found route: {route_info.route_id} ({route_info.name_zh})")

        # Step 2: Get stops with ETA
        stops_with_eta = ntpc_service.get_route_stops_with_eta(route_info.route_id, direction)
        print(f"2. Got {len(stops_with_eta)} stops with ETA")

        if not stops_with_eta:
            print("   No stops, trying opposite direction...")
            opposite_direction = 1 if direction == 0 else 0
            stops_with_eta = ntpc_service.get_route_stops_with_eta(route_info.route_id, opposite_direction)
            print(f"   Got {len(stops_with_eta)} stops from opposite direction")

        if not stops_with_eta:
            print("ERROR: No stops found")
            return

        # Step 3: Convert stops
        print("3. Converting stops...")
        stops = []
        for i, stop in enumerate(stops_with_eta):
            try:
                bus_stop = BusStop(
                    sequence=stop.sequence,
                    name=stop.name_zh,
                    eta=stop.estimate_text,
                    status=stop.status,
                    buses=[]
                )
                stops.append(bus_stop)
            except Exception as e:
                print(f"   ERROR converting stop {i}: {e}")
                print(f"   stop data: seq={stop.sequence}, name={stop.name_zh}, eta={stop.estimate_text}, status={stop.status}")
                raise

        print(f"   Converted {len(stops)} stops")

        # Step 4: Create direction info
        print("4. Creating direction info...")
        opposite_direction = 1 if direction == 0 else 0
        direction_info = DirectionInfo(
            direction=direction,
            direction_name="去程" if direction == 0 else "返程",
            departure=route_info.departure_zh if direction == 0 else route_info.destination_zh,
            arrival=route_info.destination_zh if direction == 0 else route_info.departure_zh,
            go=DirectionDetail(
                direction=0,
                direction_name=f"往 {route_info.destination_zh}",
                departure=route_info.departure_zh,
                arrival=route_info.destination_zh
            ),
            back=DirectionDetail(
                direction=1,
                direction_name=f"往 {route_info.departure_zh}",
                departure=route_info.destination_zh,
                arrival=route_info.departure_zh
            )
        )
        print("   Direction info created")

        # Step 5: Create buses
        print("5. Creating buses...")
        buses = []
        for stop in stops_with_eta:
            if stop.status in ['arriving', 'near']:
                try:
                    bus = BusVehicle(
                        id=f"bus-{stop.sequence}",
                        plate_number="",
                        bus_type="一般公車",
                        at_stop=stop.sequence,
                        eta_next=stop.estimate_text,
                        heading_to=min(stop.sequence + 1, len(stops_with_eta) - 1)
                    )
                    buses.append(bus)
                except Exception as e:
                    print(f"   ERROR creating bus for stop {stop.sequence}: {e}")
                    raise

        if not buses:
            for j in range(1, 4):
                position = min(j * (len(stops) // 3), len(stops) - 1)
                bus = BusVehicle(
                    id=f"{route}-bus-{j}",
                    plate_number="",
                    bus_type="一般公車",
                    at_stop=position,
                    eta_next=f"{j * 5}分後到達",
                    heading_to=min(position + 1, len(stops) - 1)
                )
                buses.append(bus)

        print(f"   Created {len(buses)} buses")

        # Step 6: Create result
        print("6. Creating result...")
        result = BusRouteData(
            route=route,
            route_name=route_info.name_zh,
            direction=direction_info,
            stops=stops,
            buses=buses,
            updated=datetime.now().isoformat()
        )
        print("   Result created successfully!")
        print(f"\n7. SUCCESS! Route {route} has {len(stops)} stops and {len(buses)} buses")

    except Exception as e:
        print(f"\nEXCEPTION: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_api())
