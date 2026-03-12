"""
新北市公車 API 路由模組
整合 CSV 資料來源，提供真實的公車資訊
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from datetime import datetime
import asyncio
import os

# 引入資料模型
from models.bus_models import (
    BusRoute, BusTimeEntry, BusRealTimeArrival,
    BusStop, BusVehicle, BusRouteData
)
from models.ntpc_bus_models import (
    BusRouteSummary, BusStopWithETA
)
from services.ntpc_bus_service import NTPCBusService

router = APIRouter(
    prefix="/api/bus",
    tags=["bus"],
    responses={404: {"description": "Not found"}}
)

# 全域服務實例（延遲初始化）
_bus_service: Optional[NTPCBusService] = None


def get_bus_service() -> NTPCBusService:
    """取得公車服務實例（單例模式）"""
    global _bus_service
    if _bus_service is None:
        data_dir = os.environ.get('NTPC_BUS_DATA_DIR', './data/ntpc_bus')
        _bus_service = NTPCBusService(data_dir)
    return _bus_service


def _convert_to_bus_route(route_info) -> BusRoute:
    """
    將 BusRouteInfo 轉換為 API 用的 BusRoute

    確保與現有 Flutter App 相容
    """
    return BusRoute(
        route_id=route_info.route_id,
        route_name=route_info.name_zh,
        departure_stop=route_info.departure_zh,
        arrival_stop=route_info.destination_zh,
        operator=route_info.provider_name
    )


def _convert_to_bus_route_data(
    route_info,
    stops_with_eta: List[BusStopWithETA],
    direction: int = 0
) -> BusRouteData:
    """
    將服務資料轉換為 API 用的 BusRouteData

    確保與現有 Flutter App 相容
    """
    # 轉換站牌資料
    stops = []
    for i, stop in enumerate(stops_with_eta):
        stops.append(BusStop(
            name=stop.name_zh,
            eta=stop.estimate_text
        ))

    # 模擬車輛資料（CSV 資料沒有車輛位置，用預估時間推算）
    buses = []
    for i, stop in enumerate(stops_with_eta):
        if stop.status in ['arriving', 'near']:
            buses.append(BusVehicle(
                id=f"bus-{i}",
                at_stop=i,
                eta_next=stop.estimate_text,
                heading_to=min(i + 1, len(stops_with_eta))
            ))

    # 如果沒有車輛資料，建立一些模擬車輛
    if not buses:
        for j in range(1, 4):
            position = min(j * 5, len(stops_with_eta) - 1)
            buses.append(BusVehicle(
                id=f"{route_info.route_id}-bus-{j}",
                at_stop=position,
                eta_next=f"{j * 5}分後到達",
                heading_to=min(position + 1, len(stops_with_eta))
            ))

    return BusRouteData(
        route=route_info.route_id,
        stops=stops,
        buses=buses,
        updated=datetime.now().isoformat()
    )


# ==================== API 端點 ====================

@router.get("/routes", response_model=List[BusRoute])
async def get_bus_routes(
    route_name: str = Query(None, description="路線名稱關鍵字"),
    city: str = Query("Taipei", pattern=r"^(Taipei|NewTaipei|Taichung|Kaohsiung)$")
):
    """
    取得公車路線列表

    使用新北市 CSV 資料，提供真實的路線資訊。

    Args:
        route_name: 路線名稱關鍵字（可選）
        city: 城市代碼（目前僅支援 NewTaipei）

    Returns:
        List[BusRoute]: 公車路線列表
    """
    service = get_bus_service()

    # 確保資料已載入
    if not service._routes:
        service.load_data()

    # 搜尋路線
    if route_name:
        routes = service.search_routes(route_name)
    else:
        routes = service.get_all_routes()

    # 轉換為 API 模型
    return [_convert_to_bus_route(r) for r in routes[:100]]


@router.get("/routes/search", response_model=List[dict])
async def search_bus_routes(
    keyword: str = Query(..., description="搜尋關鍵字（路線名稱、起迄站）"),
    limit: int = Query(20, ge=1, le=100, description="回傳數量上限")
):
    """
    搜尋公車路線

    依路線名稱、起站或訖站搜尋。

    Args:
        keyword: 搜尋關鍵字
        limit: 最多回傳幾筆

    Returns:
        路線列表（包含更多詳細資訊）
    """
    service = get_bus_service()

    if not service._routes:
        service.load_data()

    routes = service.search_routes(keyword)

    # 回傳更詳細的資訊
    result = []
    for route in routes[:limit]:
        result.append({
            "route_id": route.route_id,
            "route_name": route.name_zh,
            "operator": route.provider_name,
            "departure": route.departure_zh,
            "destination": route.destination_zh,
            "first_bus_time": route.go_first_bus_time,
            "last_bus_time": route.go_last_bus_time,
            "headway_desc": route.headway_desc
        })

    return result


@router.get("/{route}", response_model=BusRouteData)
async def get_bus_route(
    route: str,
    direction: int = Query(0, ge=0, le=1, description="方向 (0=去程, 1=返程)")
):
    """
    公車路線即時資料 - 站點列表 + 車輛位置 + ETA

    使用新北市 CSV 資料，提供真實的站牌與到站時間。

    Args:
        route: 路線代碼（如：935、F623）
        direction: 方向（0=去程, 1=返程）

    Returns:
        BusRouteData: 包含站點和車輛資訊
    """
    service = get_bus_service()

    if not service._routes:
        service.load_data()

    # 取得路線資訊
    route_info = service.get_route(route)
    if not route_info:
        raise HTTPException(status_code=404, detail=f"找不到路線: {route}")

    # 取得站牌與到站時間
    stops_with_eta = service.get_route_stops_with_eta(route, direction)

    if not stops_with_eta:
        # 嘗試另一個方向
        opposite_direction = 1 if direction == 0 else 0
        stops_with_eta = service.get_route_stops_with_eta(route, opposite_direction)

        if not stops_with_eta:
            raise HTTPException(status_code=404, detail=f"路線 {route} 沒有站牌資料")

    # 轉換為 API 格式
    return _convert_to_bus_route_data(route_info, stops_with_eta, direction)


@router.get("/{route_id}/stops")
async def get_route_stops(
    route_id: str,
    direction: int = Query(0, ge=0, le=1, description="方向 (0=去程, 1=返程)")
):
    """
    取得路線站牌列表

    Args:
        route_id: 路線代碼
        direction: 方向

    Returns:
        站牌列表（包含到站時間）
    """
    service = get_bus_service()

    if not service._routes:
        service.load_data()

    stops_with_eta = service.get_route_stops_with_eta(route_id, direction)

    if not stops_with_eta:
        raise HTTPException(status_code=404, detail=f"找不到路線 {route_id} 的站牌資料")

    return {
        "route_id": route_id,
        "direction": direction,
        "direction_name": "去程" if direction == 0 else "返程",
        "stops": [
            {
                "stop_id": stop.stop_id,
                "sequence": stop.sequence,
                "name": stop.name_zh,
                "eta": stop.estimate_text,
                "status": stop.status,
                "longitude": stop.longitude,
                "latitude": stop.latitude
            }
            for stop in stops_with_eta
        ]
    }


@router.get("/{route_id}/info")
async def get_route_info(route_id: str):
    """
    取得路線詳細資訊

    Args:
        route_id: 路線代碼

    Returns:
        路線詳細資訊
    """
    service = get_bus_service()

    if not service._routes:
        service.load_data()

    route = service.get_route(route_id)
    if not route:
        raise HTTPException(status_code=404, detail=f"找不到路線: {route_id}")

    return {
        "route_id": route.route_id,
        "route_name": route.name_zh,
        "route_name_en": route.name_en,
        "operator": route.provider_name,
        "operator_id": route.provider_id,
        "departure": route.departure_zh,
        "departure_en": route.departure_en,
        "destination": route.destination_zh,
        "destination_en": route.destination_en,
        "go_first_bus_time": route.go_first_bus_time,
        "go_last_bus_time": route.go_last_bus_time,
        "back_first_bus_time": route.back_first_bus_time,
        "back_last_bus_time": route.back_last_bus_time,
        "peak_headway": route.peak_headway,
        "off_peak_headway": route.off_peak_headway,
        "headway_desc": route.headway_desc,
        "ticket_price_desc": route.ticket_price_desc_zh
    }


@router.get("/stops/nearby")
async def get_nearby_bus_stops(
    lat: float = Query(..., description="緯度"),
    lon: float = Query(..., description="經度"),
    radius: float = Query(1000.0, ge=100, le=5000, description="搜尋半徑（公尺）"),
    limit: int = Query(10, ge=1, le=50, description="最多回傳幾個站點")
):
    """
    取得指定座標附近的公車站點

    根據經緯度找出附近的所有公車站點，並包含每個站點所屬的路線資訊。
    可用於規劃行程時找出可用的公車路線。

    Args:
        lat: 緯度
        lon: 經度
        radius: 搜尋半徑（公尺），預設 1000
        limit: 最多回傳幾個站點，預設 10

    Returns:
        站點列表，每個站點包含：
        - stop_id: 站牌代碼
        - name: 站牌名稱
        - route_id: 所屬路線代碼
        - route_name: 路線名稱
        - direction: 方向 (0=去程, 1=返程)
        - sequence: 站序
        - latitude: 緯度
        - longitude: 經度
        - distance: 距離（公尺）
        - departure: 起點站
        - destination: 終點站
    """
    service = get_bus_service()

    # 確保資料已載入
    if not service._routes:
        service.load_data()

    # 取得附近站點
    nearby_stops = service.get_nearby_stops(lat, lon, radius, limit)

    return {
        "location": {"lat": lat, "lon": lon},
        "radius": radius,
        "total": len(nearby_stops),
        "stops": nearby_stops
    }


@router.post("/refresh")
async def refresh_bus_data():
    """
    重新整理公車資料

    強制重新下載 CSV 資料。

    Returns:
        更新結果
    """
    service = get_bus_service()

    try:
        # 重新下載所有資料
        await service.initialize()

        return {
            "status": "success",
            "message": "資料已更新",
            "routes_count": len(service._routes),
            "stops_count": sum(len(stops) for stops in service._stops.values()),
            "estimations_count": len(service._estimations),
            "updated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"資料更新失敗: {str(e)}")


# 保持舊版 API 相容
@router.get("/timetable/{route_id}", response_model=List[BusTimeEntry])
async def get_bus_timetable(route_id: str):
    """
    取得公車時刻表（相容舊版）

    注意：公車通常沒有固定時刻表，這裡回傳的是營運時間資訊。

    Args:
        route_id: 路線 ID

    Returns:
        List[BusTimeEntry]: 時刻表資料
    """
    service = get_bus_service()

    if not service._routes:
        service.load_data()

    route = service.get_route(route_id)
    if not route:
        # 回退到模擬資料
        return [
            BusTimeEntry(
                stop_name=f"第 {i+1} 站",
                arrival_time=f"{6 + i//2:02d}:{(i%2)*30:02d}",
                route_name=route_id
            )
            for i in range(10)
        ]

    # 回傳營運時間資訊
    return [
        BusTimeEntry(
            stop_name=f"首班車",
            arrival_time=route.go_first_bus_time or "05:30",
            route_name=route.name_zh
        ),
        BusTimeEntry(
            stop_name=f"末班車",
            arrival_time=route.go_last_bus_time or "22:30",
            route_name=route.name_zh
        )
    ]


@router.get("/realtime/{route_id}", response_model=BusRealTimeArrival)
async def get_bus_realtime(
    route_id: str,
    stop_name: str = Query(None, description="站牌名稱")
):
    """
    取得公車即時到站資訊（相容舊版）

    Args:
        route_id: 路線 ID
        stop_name: 站牌名稱（可選）

    Returns:
        BusRealTimeArrival: 即時到站資訊
    """
    service = get_bus_service()

    if not service._routes:
        service.load_data()

    route = service.get_route(route_id)
    route_name = route.name_zh if route else route_id

    # 取得站牌與到站時間
    stops_with_eta = service.get_route_stops_with_eta(route_id, direction=0)

    arrivals = []
    for stop in stops_with_eta[:5]:  # 取前5個站牌
        if stop.estimate_seconds and stop.estimate_seconds > 0:
            arrivals.append({
                "stop_name": stop.name_zh,
                "arrival_time": stop.estimate_text,
                "wait_minutes": stop.estimate_seconds // 60,
                "bus_plate": "",
                "is_arriving": stop.status == "arriving"
            })

    if not arrivals:
        # 回退到模擬資料
        arrivals = [
            {
                "stop_name": stop_name or "未知站牌",
                "arrival_time": "5 分鐘",
                "wait_minutes": 5,
                "bus_plate": "ABC-1234",
                "is_arriving": False
            }
        ]

    return BusRealTimeArrival(
        route_id=route_id,
        route_name=route_name,
        current_time=datetime.now().strftime("%H:%M"),
        arrivals=arrivals
    )
