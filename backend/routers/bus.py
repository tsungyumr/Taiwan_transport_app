"""
公車 API 路由模組
處理所有與公車相關的 API 端點
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from datetime import datetime
import httpx
import random

# 引入資料模型
from models.bus_models import (
    BusRoute, BusTimeEntry, BusRealTimeArrival,
    BusStop, BusVehicle, BusRouteData
)

router = APIRouter(
    prefix="/api/bus",
    tags=["bus"],
    responses={404: {"description": "Not found"}}
)


# ==================== 預設資料 ====================

DEFAULT_ROUTES = [
    {"route_id": "235", "route_name": "235", "departure": "長春路", "arrival": "福港街", "operator": "首都客運"},
    {"route_id": "307", "route_name": "307", "departure": "板橋", "arrival": "撫遠街", "operator": "三重客運"},
    {"route_id": "604", "route_name": "604", "departure": "板橋站", "arrival": "捷運明德站", "operator": "台北客運"},
    {"route_id": "265", "route_name": "265", "departure": "板橋府中", "arrival": "士林", "operator": "三重客運"},
    {"route_id": "651", "route_name": "651", "departure": "板橋法院", "arrival": "台北車站", "operator": "台北客運"},
    {"route_id": "667", "route_name": "667", "departure": "板橋站", "arrival": "捷運忠孝敦化", "operator": "三重客運"},
    {"route_id": "99", "route_name": "99", "departure": "板橋", "arrival": "新莊", "operator": "台北客運"},
    {"route_id": "234", "route_name": "234", "departure": "板橋", "arrival": "西門", "operator": "三重客運"},
    {"route_id": "705", "route_name": "705", "departure": "板橋", "arrival": "三重", "operator": "三重客運"},
    {"route_id": "812", "route_name": "812", "departure": "板橋", "arrival": "中和", "operator": "台北客運"},
    {"route_id": "920", "route_name": "920", "departure": "板橋", "arrival": "信義區", "operator": "台北客運"},
    {"route_id": "930", "route_name": "930", "departure": "板橋", "arrival": "新店", "operator": "台北客運"},
    {"route_id": "965", "route_name": "965", "departure": "板橋", "arrival": "金瓜石", "operator": "基隆客運"},
]

BUS_STOPS = {
    "235": ["長春路", "民生社區", "富民生態", "新東街", "吉祥路", "成福路", "福港街"],
    "307": ["板橋", "致理科技大學", "新埔", "江子翠", "龍山寺", "西門", "博愛路", "撫遠街"],
    "604": ["板橋站", "捷運板橋站", "音樂公園", "光復中學", "民生社區", "捷運明德站"],
}


# ==================== 輔助函數 ====================

def get_default_routes(route_name: str = None, limit: int = 50) -> List[BusRoute]:
    """取得預設公車路線"""
    routes = [
        BusRoute(
            route_id=r["route_id"],
            route_name=r["route_name"],
            departure_stop=r["departure"],
            arrival_stop=r["arrival"],
            operator=r["operator"]
        )
        for r in DEFAULT_ROUTES
    ]

    if route_name:
        routes = [r for r in routes if route_name.lower() in r.route_name.lower()]

    return routes[:limit]


def get_default_timetable(route_id: str) -> List[BusTimeEntry]:
    """取得預設時刻表"""
    entries = []
    route_info = next((r for r in DEFAULT_ROUTES if r["route_id"] == route_id), None)
    route_name = route_info["route_name"] if route_info else route_id

    stops = BUS_STOPS.get(route_id, [f"第 {i+1} 站" for i in range(15)])

    base_hour = 6
    for bus_num in range(25):
        hour = base_hour + bus_num // 2
        minute = (bus_num % 2) * 15 + 10

        if hour > 23:
            break

        for i, stop in enumerate(stops):
            stop_time_hour = hour + i // 4
            stop_time_min = minute + (i % 4) * 8

            if stop_time_min >= 60:
                stop_time_hour += 1
                stop_time_min -= 60

            if stop_time_hour > 23:
                continue

            entries.append(BusTimeEntry(
                stop_name=stop,
                arrival_time=f"{stop_time_hour:02d}:{stop_time_min:02d}",
                route_name=route_name
            ))

    return entries[:50]


def get_mock_real_time_arrival(route_id: str, stop_name: str = None) -> Dict:
    """取得模擬即時到站資訊"""
    now = datetime.now()
    current_minute = now.hour * 60 + now.minute

    route_info = next((r for r in DEFAULT_ROUTES if r["route_id"] == route_id), None)
    route_name = route_info["route_name"] if route_info else route_id

    stops = BUS_STOPS.get(route_id, ["站牌1", "站牌2", "站牌3"])

    arrivals = []
    for i in range(3):
        wait_minutes = random.randint(3, 25) * (i + 1)
        arrival_minute = current_minute + wait_minutes
        arrival_hour = arrival_minute // 60
        arrival_m = arrival_minute % 60

        arrivals.append({
            "stop_name": stops[i % len(stops)] if not stop_name else stop_name,
            "arrival_time": f"{arrival_hour:02d}:{arrival_m:02d}",
            "wait_minutes": wait_minutes,
            "bus_plate": f"{random.choice(['基', '北', '新', '三重', '台北'])}{random.randint(1000, 9999)}",
            "is_arriving": wait_minutes <= 3
        })

    return {
        "route_id": route_id,
        "route_name": route_name,
        "current_time": now.strftime("%H:%M"),
        "arrivals": arrivals
    }


# ==================== API 端點 ====================

@router.get("/routes", response_model=List[BusRoute])
async def get_bus_routes(
    route_name: str = Query(None, description="路線名稱關鍵字"),
    city: str = Query("Taipei", pattern=r"^(Taipei|NewTaipei|Taichung|Kaohsiung)$")
):
    """
    取得公車路線列表

    Args:
        route_name: 路線名稱關鍵字（可選）
        city: 城市代碼（Taipei/NewTaipei/Taichung/Kaohsiung）

    Returns:
        List[BusRoute]: 公車路線列表
    """
    return get_default_routes(route_name)


@router.get("/timetable/{route_id}", response_model=List[BusTimeEntry])
async def get_bus_timetable(route_id: str):
    """
    取得公車時刻表

    Args:
        route_id: 路線 ID

    Returns:
        List[BusTimeEntry]: 時刻表資料
    """
    return get_default_timetable(route_id)


@router.get("/realtime/{route_id}", response_model=BusRealTimeArrival)
async def get_bus_realtime(
    route_id: str,
    stop_name: str = Query(None, description="站牌名稱")
):
    """
    取得公車即時到站資訊

    Args:
        route_id: 路線 ID
        stop_name: 站牌名稱（可選）

    Returns:
        BusRealTimeArrival: 即時到站資訊
    """
    result = get_mock_real_time_arrival(route_id, stop_name)
    return BusRealTimeArrival(**result)


@router.get("/{route}", response_model=BusRouteData)
async def get_bus_route(route: str):
    """
    公車路線即時資料 - 站點列表 + 多輛公車位置 + ETA

    Args:
        route: 路線代碼（如：藍15、綠1、紅10）

    Returns:
        BusRouteData: 包含站點和車輛資訊
    """
    client = httpx.AsyncClient(
        verify=False,
        timeout=httpx.Timeout(30.0),
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
    )

    try:
        # 從 5284 API 取得站點資訊
        stop_url = f"https://www.5284.gov.taipei/ibus/api/bus/StopOfRoute?routeName={route}&routeAll=1"
        stop_resp = await client.get(stop_url)
        stops = []

        if stop_resp.status_code == 200:
            data = stop_resp.json().get("data", [])
            for s in data:
                name = s.get("StopName", {}).get("Zh_tw", f"{route} 未知站")
                stops.append(BusStop(name=name, eta="公車已離開"))
        else:
            stops = [BusStop(name=f"{route} 第{i+1}站", eta="API載入失敗") for i in range(25)]

        # 從 5284 API 取得即時公車資訊
        realtime_url = f"https://www.5284.gov.taipei/ibus/api/bus/RealTimeByRoute?routeName={route}&routeAll=1"
        rt_resp = await client.get(realtime_url)
        buses = []

        if rt_resp.status_code == 200:
            data = rt_resp.json().get("data", [])
            now_ms = int(datetime.now().timestamp() * 1000)

            for b in data:
                busid = b.get("PlateNumb", "未知公車")
                position_str = b.get("BusPositionMark", "0")

                try:
                    at_stop = int(position_str.split("/")[0]) if "/" in position_str else int(position_str)
                except:
                    at_stop = 1

                eta_ms = b.get("EstimateTime_Arrive")
                if eta_ms:
                    eta_min = max(1, int((int(eta_ms) - now_ms) / 60000))
                    eta_next = f"{eta_min}min後到達"
                else:
                    eta_next = "N/A"

                heading_to = min(at_stop + 1, len(stops) + 1)
                buses.append(BusVehicle(
                    id=busid,
                    at_stop=at_stop,
                    eta_next=eta_next,
                    heading_to=heading_to
                ))

        await client.aclose()

        return BusRouteData(
            route=route,
            stops=stops,
            buses=buses,
            updated=datetime.now().isoformat()
        )

    except Exception as e:
        await client.aclose()
        print(f"Bus route API error for {route}: {e}")

        # 回退到模擬資料
        stops = [
            BusStop(
                name=f"{route} 第{i+1}站",
                eta=random.choice(["公車已離開", "即將進站", f"{random.randint(1,30)}分後到達"])
            )
            for i in range(25)
        ]

        buses = [
            BusVehicle(
                id=f"{route}-bus-{j}",
                at_stop=random.randint(1, 25),
                eta_next=f"{random.randint(1,15)}分後到達",
                heading_to=random.randint(1, 26)
            )
            for j in range(1, 4)
        ]

        return BusRouteData(
            route=route,
            stops=stops,
            buses=buses,
            updated=datetime.now().isoformat()
        )
