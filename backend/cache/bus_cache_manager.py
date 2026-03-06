"""
大台北公車快取管理器 - 懶加載模式 (Lazy Loading)
Taipei Bus Cache Manager - Lazy Loading Mode

這個模組負責：
1. 用戶請求時才從 ebus.gov.taipei 爬取公車資料（懶加載）
2. 資料過期（1分鐘）時自動重新爬取
3. 將資料快取在記憶體中
4. 提供 API 端點從快取取得資料

資料來源: https://ebus.gov.taipei/
快取過期時間: 60 秒 (1分鐘)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from scrapers.taipei_bus_scraper import TaipeiBusScraper

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 快取過期時間（秒）
CACHE_TTL = 60  # 1分鐘


@dataclass
class CachedRouteData:
    """快取的路線資料"""
    route_name: str
    route_id: str
    direction: int
    stops: List[Dict[str, Any]]
    buses: List[Dict[str, Any]]
    departure_stop: str
    arrival_stop: str
    direction_name_go: str
    direction_name_back: str
    timestamp: datetime = field(default_factory=datetime.now)

    def is_expired(self) -> bool:
        """檢查資料是否過期（超過1分鐘）"""
        return datetime.now() - self.timestamp > timedelta(seconds=CACHE_TTL)


@dataclass
class CachedRouteList:
    """快取的路線列表"""
    routes: List[Dict[str, str]]
    timestamp: datetime = field(default_factory=datetime.now)

    def is_expired(self) -> bool:
        """檢查資料是否過期（超過1分鐘）"""
        return datetime.now() - self.timestamp > timedelta(seconds=CACHE_TTL)


class TaipeiBusCacheManager:
    """
    大台北公車快取管理器 - 懶加載模式

    特性：
    1. 用戶請求時才撈取資料
    2. 資料過期（1分鐘）自動重新撈取
    3. 不需要背景定期更新任務
    """

    def __init__(self):
        """初始化快取管理器"""
        # 快取資料儲存
        self._route_cache: Dict[str, CachedRouteData] = {}  # key: "route_name:direction"
        self._route_list_cache: Optional[CachedRouteList] = None

        # 執行緒鎖
        self._lock = asyncio.Lock()

        # 統計資訊
        self._stats = {
            "total_requests": 0,  # 總請求次數
            "cache_hits": 0,      # 快取命中次數
            "cache_misses": 0,    # 快取未命中次數（需爬取）
            "expired_updates": 0, # 過期更新次數
            "failed_updates": 0,  # 更新失敗次數
            "last_error": None
        }

    async def start(self):
        """啟動快取管理器（懶加載模式不需要預先撈取）"""
        logger.info("啟動大台北公車快取管理器（懶加載模式）")
        logger.info("快取過期時間：60 秒")

    async def stop(self):
        """停止快取管理器"""
        logger.info("停止大台北公車快取管理器")
        # 清空快取
        async with self._lock:
            self._route_cache.clear()
            self._route_list_cache = None

    # ==================== 公開 API ====================

    async def get_all_routes(self) -> List[Any]:
        """
        取得所有公車路線列表

        邏輯：
        1. 如果快取中有資料且未過期，直接返回
        2. 如果快取中無資料或已過期，即時爬取並存入快取
        """
        self._stats["total_requests"] += 1

        async with self._lock:
            # 檢查快取是否有效
            if self._route_list_cache and not self._route_list_cache.is_expired():
                self._stats["cache_hits"] += 1
                logger.debug(f"路線列表快取命中，共 {len(self._route_list_cache.routes)} 條")
                # 轉換回原始格式
                from scrapers.taipei_bus_scraper import BusRoute
                return [BusRoute(
                    route_id=r["route_id"],
                    route_name=r["route_name"],
                    description=r["description"]
                ) for r in self._route_list_cache.routes]

        # 快取未命中或已過期，需要爬取
        self._stats["cache_misses"] += 1
        if self._route_list_cache and self._route_list_cache.is_expired():
            self._stats["expired_updates"] += 1
            logger.info("路線列表快取已過期，重新爬取...")
        else:
            logger.info("路線列表無快取，開始爬取...")

        try:
            async with TaipeiBusScraper(headless=True) as scraper:
                routes = await scraper.get_all_routes()

                # 存入快取
                route_list = [
                    {
                        "route_id": route.route_id,
                        "route_name": route.route_name,
                        "description": route.description
                    }
                    for route in routes
                ]

                async with self._lock:
                    self._route_list_cache = CachedRouteList(routes=route_list)

                logger.info(f"路線列表已更新，共 {len(routes)} 條路線")
                return routes

        except Exception as e:
            logger.error(f"爬取路線列表失敗: {e}")
            self._stats["failed_updates"] += 1
            self._stats["last_error"] = str(e)
            # 如果有舊快取，返回舊資料（即使過期）
            async with self._lock:
                if self._route_list_cache:
                    logger.warning("返回過期的路線列表快取")
                    from scrapers.taipei_bus_scraper import BusRoute
                    return [BusRoute(
                        route_id=r["route_id"],
                        route_name=r["route_name"],
                        description=r["description"]
                    ) for r in self._route_list_cache.routes]
            return []

    async def get_route_data(self, route_name: str, direction: int = 0) -> Optional[CachedRouteData]:
        """
        取得公車路線資料

        邏輯：
        1. 如果快取中有資料且未過期，直接返回
        2. 如果快取中無資料或已過期，即時爬取並存入快取

        Args:
            route_name: 路線名稱（如：藍15, 235）
            direction: 方向（0=去程, 1=返程）

        Returns:
            CachedRouteData: 路線資料
        """
        self._stats["total_requests"] += 1
        cache_key = f"{route_name}:{direction}"

        async with self._lock:
            cached = self._route_cache.get(cache_key)
            # 檢查快取是否有效
            if cached and not cached.is_expired():
                self._stats["cache_hits"] += 1
                logger.debug(f"路線 {route_name} 方向 {direction} 快取命中")
                return cached

        # 快取未命中或已過期，需要爬取
        self._stats["cache_misses"] += 1
        if cached and cached.is_expired():
            self._stats["expired_updates"] += 1
            logger.info(f"路線 {route_name} 方向 {direction} 快取已過期，重新爬取...")
        else:
            logger.info(f"路線 {route_name} 方向 {direction} 無快取，開始爬取...")

        try:
            return await self._fetch_and_cache_route(route_name, direction)
        except Exception as e:
            logger.error(f"爬取路線 {route_name} 失敗: {e}")
            self._stats["failed_updates"] += 1
            self._stats["last_error"] = str(e)
            # 如果有舊快取，返回舊資料（即使過期）
            async with self._lock:
                if cached:
                    logger.warning(f"返回過期的路線 {route_name} 快取")
                    return cached
            return None

    async def _fetch_and_cache_route(self, route_name: str, direction: int) -> Optional[CachedRouteData]:
        """
        爬取路線資料並存入快取

        Args:
            route_name: 路線名稱
            direction: 方向

        Returns:
            CachedRouteData: 更新後的快取資料
        """
        cache_key = f"{route_name}:{direction}"

        async with TaipeiBusScraper(headless=True) as scraper:
            route_info = await scraper.get_route_info(route_name, direction=direction)

            # 轉換站點資料
            stops = []
            for stop in route_info.stops:
                if stop.eta is None:
                    eta_str = "未發車"
                    status = "not_started"
                elif stop.eta == 0:
                    eta_str = "進站中"
                    status = "arriving"
                elif stop.eta == 1:
                    eta_str = "即將進站"
                    status = "near"
                else:
                    eta_str = f"{stop.eta} 分鐘"
                    status = "normal"

                buses_at_stop = []
                if stop.buses:
                    for bus in stop.buses:
                        buses_at_stop.append({
                            "plate_number": bus.get("plate_number", ""),
                            "bus_type": bus.get("bus_type", ""),
                            "remaining_seats": bus.get("remaining_seats")
                        })

                stops.append({
                    "sequence": stop.sequence,
                    "name": stop.name,
                    "eta": eta_str,
                    "status": status,
                    "buses": buses_at_stop
                })

            # 轉換車輛資料
            buses = []
            for stop in route_info.stops:
                if stop.buses:
                    for bus in stop.buses:
                        if stop.eta is None:
                            vehicle_status = "未發車"
                        elif stop.eta == 0:
                            vehicle_status = "進站中"
                        else:
                            vehicle_status = f"{stop.eta} 分鐘後到站"

                        buses.append({
                            "id": bus.get("plate_number", f"{route_name}-bus"),
                            "plate_number": bus.get("plate_number", ""),
                            "bus_type": bus.get("bus_type", ""),
                            "at_stop": stop.sequence,
                            "eta_next": vehicle_status,
                            "heading_to": stop.sequence + 1 if stop.sequence < len(route_info.stops) else stop.sequence,
                            "remaining_seats": bus.get("remaining_seats")
                        })

            # 建立快取資料
            cached_data = CachedRouteData(
                route_name=route_info.route_name or route_name,
                route_id=route_info.route_id or route_name,
                direction=direction,
                stops=stops,
                buses=buses,
                departure_stop=route_info.departure_stop or "",
                arrival_stop=route_info.arrival_stop or "",
                direction_name_go=route_info.direction_name_go or "往 終點站",
                direction_name_back=route_info.direction_name_back or "往 起點站"
            )

            # 存入快取
            async with self._lock:
                self._route_cache[cache_key] = cached_data

            logger.info(f"路線 {route_name} 方向 {direction} 已更新，共 {len(stops)} 站 {len(buses)} 車")
            return cached_data

    async def refresh_route(self, route_name: str, direction: int = 0) -> bool:
        """
        手動重新整理特定路線的快取

        Args:
            route_name: 路線名稱
            direction: 方向（0=去程, 1=返程）

        Returns:
            bool: 是否成功
        """
        try:
            await self._fetch_and_cache_route(route_name, direction)
            return True
        except Exception as e:
            logger.error(f"手動更新路線 {route_name} 失敗: {e}")
            return False

    async def clear_cache(self):
        """清空所有快取"""
        async with self._lock:
            self._route_cache.clear()
            self._route_list_cache = None
        logger.info("已清空所有快取")

    async def get_cache_status(self) -> Dict[str, Any]:
        """
        取得快取狀態資訊

        Returns:
            Dict: 快取狀態
        """
        async with self._lock:
            # 計算過期項目數量
            expired_routes = sum(1 for r in self._route_cache.values() if r.is_expired())
            expired_list = self._route_list_cache.is_expired() if self._route_list_cache else False

            return {
                "cached_routes_count": len(self._route_cache),
                "cached_route_list": self._route_list_cache is not None,
                "route_list_count": len(self._route_list_cache.routes) if self._route_list_cache else 0,
                "expired_routes_count": expired_routes,
                "route_list_expired": expired_list,
                "cache_ttl_seconds": CACHE_TTL,
                **self._stats
            }


# 全域快取管理器實例
_bus_cache_manager: Optional[TaipeiBusCacheManager] = None


def get_bus_cache_manager() -> TaipeiBusCacheManager:
    """
    取得全域快取管理器實例（單例模式）

    Returns:
        TaipeiBusCacheManager: 快取管理器實例
    """
    global _bus_cache_manager
    if _bus_cache_manager is None:
        _bus_cache_manager = TaipeiBusCacheManager()
    return _bus_cache_manager


async def start_cache_manager():
    """啟動快取管理器"""
    manager = get_bus_cache_manager()
    await manager.start()


async def stop_cache_manager():
    """停止快取管理器"""
    global _bus_cache_manager
    if _bus_cache_manager:
        await _bus_cache_manager.stop()
        _bus_cache_manager = None
