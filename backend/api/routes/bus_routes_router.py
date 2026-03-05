"""
台灣交通時刻表App - 公車API路由模組
Taipei Bus API Router Module

提供公車相關API端點，整合爬蟲功能以取得真實的公車資料。
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
import logging

from pydantic import BaseModel

# 導入爬蟲模組
from scrapers.taipei_bus_scraper import TaipeiBusScraper, BusRoute, BusRouteData, BusRouteSearch

# 設置logging
logger = logging.getLogger(__name__)

# 建立API路由器
router = APIRouter(prefix="/api/bus", tags=["公車"])

# 建立爬蟲實例（可以考慮使用依賴注入）
scraper = TaipeiBusScraper(headless=True)

# ==================== Pydantic模型 ====================

class BusRouteResponse(BaseModel):
    """公車路線API回應模型"""
    route_id: str
    route_name: str
    departure_stop: str
    arrival_stop: str
    operator: str = ""
    direction: int = 0
    stops: List[str] = []

class BusRouteDataResponse(BaseModel):
    """公車路線詳細資料API回應模型"""
    route: str
    stops: List[dict]
    buses: List[dict]
    updated: datetime
    operator: str = ""
    direction: int = 0
    total_stops: int

class BusRouteSearchResponse(BaseModel):
    """公車路線搜尋API回應模型"""
    route_id: str
    route_name: str
    departure_stop: str
    arrival_stop: str
    operator: str

class ErrorResponse(BaseModel):
    """錯誤回應模型"""
    detail: str
    error_code: str = ""
    timestamp: datetime


# ==================== API端點 ====================

@router.get("/routes", response_model=List[BusRouteResponse])
async def get_bus_routes(
    route_name: Optional[str] = None,
    limit: int = 50,
    background_tasks: BackgroundTasks = Depends()
):
    """
    取得公車路線列表

    - 支援搜尋特定路線名稱
    - 支援限制回傳數量
    - 使用快取機制提升效能
    """
    try:
        logger.info(f"API: Getting bus routes, route_name={route_name}, limit={limit}")

        # 呼叫爬蟲
        routes = await scraper.get_bus_routes(route_name, limit)

        # 轉換為API回應模型
        response_data = [
            BusRouteResponse(
                route_id=route.route_id,
                route_name=route.route_name,
                departure_stop=route.departure_stop,
                arrival_stop=route.arrival_stop,
                operator=route.operator,
                direction=route.direction,
                stops=route.stops
            )
            for route in routes
        ]

        logger.info(f"API: Successfully fetched {len(response_data)} bus routes")
        return response_data

    except Exception as e:
        logger.error(f"API Error: Failed to get bus routes - {e}")
        raise HTTPException(
            status_code=503,
            detail=f"無法取得公車路線資料: {str(e)}"
        )


@router.get("/{route_id}", response_model=BusRouteDataResponse)
async def get_bus_route_data(
    route_id: str,
    background_tasks: BackgroundTasks = Depends()
):
    """
    取得特定公車路線詳細資料

    - 包含車輛位置和到站時間
    - 包含站牌列表
    - 包含業者資訊
    """
    try:
        logger.info(f"API: Getting bus route data for route {route_id}")

        # 呼叫爬蟲
        route_data = await scraper.get_bus_route_data(route_id)

        # 轉換為API回應模型
        response_data = BusRouteDataResponse(
            route=route_data.route,
            stops=[{
                "name": stop.name,
                "sequence": stop.sequence,
                "latitude": stop.latitude,
                "longitude": stop.longitude
            } for stop in route_data.stops],
            buses=[{
                "id": vehicle.id,
                "plate_number": vehicle.plate_number,
                "at_stop": vehicle.at_stop,
                "eta_next": vehicle.eta_next,
                "heading_to": vehicle.heading_to,
                "latitude": vehicle.latitude,
                "longitude": vehicle.longitude,
                "speed": vehicle.speed,
                "direction": vehicle.direction
            } for vehicle in route_data.buses],
            updated=route_data.updated,
            operator=route_data.operator,
            direction=route_data.direction,
            total_stops=route_data.total_stops
        )

        logger.info(f"API: Successfully fetched data for route {route_id}")
        return response_data

    except Exception as e:
        logger.error(f"API Error: Failed to get bus route data for {route_id} - {e}")
        raise HTTPException(
            status_code=503,
            detail=f"無法取得路線 {route_id} 的詳細資料: {str(e)}"
        )


@router.get("/search", response_model=List[BusRouteSearchResponse])
async def search_bus_routes(query: str):
    """
    搜尋公車路線

    - 支援關鍵字搜尋
    - 回傳相關的路線列表
    """
    try:
        logger.info(f"API: Searching bus routes for query: {query}")

        # 呼叫爬蟲
        results = await scraper.search_routes(query)

        # 轉換為API回應模型
        response_data = [
            BusRouteSearchResponse(
                route_id=result.route_id,
                route_name=result.route_name,
                departure_stop=result.departure_stop,
                arrival_stop=result.arrival_stop,
                operator=result.operator
            )
            for result in results
        ]

        logger.info(f"API: Found {len(response_data)} search results for '{query}'")
        return response_data

    except Exception as e:
        logger.error(f"API Error: Failed to search bus routes - {e}")
        raise HTTPException(
            status_code=503,
            detail=f"無法搜尋公車路線: {str(e)}"
        )


@router.get("/operators", response_model=List[str])
async def get_bus_operators():
    """
    取得公車業者列表

    - 回傳所有已知的公車業者
    - 支援業者篩選
    """
    try:
        logger.info("API: Getting bus operators")

        # 這裡可以實作業者列表的邏輯
        # 暫時回傳一個示例列表
        operators = [
            "首都客運",
            "三重客運",
            "台北客運",
            "指南客運",
            "桃園客運",
            "新竹客運",
            "台中客運",
            "高雄客運",
            "屏東客運",
            "台鐵局",
            "高鐵局"
        ]

        return operators

    except Exception as e:
        logger.error(f"API Error: Failed to get bus operators - {e}")
        raise HTTPException(
            status_code=503,
            detail=f"無法取得公車業者列表: {str(e)}"
        )


# ==================== 錯誤處理中介層 ====================

@router.exception_handler(Exception)
async def api_exception_handler(request, exc):
    """全域API錯誤處理"""
    logger.error(f"Unhandled exception in API: {exc}")

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail="系統發生錯誤，請稍後重試",
            error_code="INTERNAL_SERVER_ERROR",
            timestamp=datetime.now()
        ).dict()
    )


# ==================== 健康檢查端點 ====================

@router.get("/health", response_model=dict)
async def health_check():
    """健康檢查端點"""
    try:
        # 檢查爬蟲是否可用
        is_healthy = await scraper.get_bus_routes(limit=1)

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "features": {
                "bus_routes": True,
                "bus_route_data": True,
                "search": True
            }
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }