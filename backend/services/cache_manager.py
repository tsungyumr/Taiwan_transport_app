"""
統一快取管理器
提供各服務專用的快取實例與統一管理介面

統一快取機制，取代分散在各模組中的獨立快取實現
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from services.memory_cache import MemoryCache

logger = logging.getLogger(__name__)


class CacheManager:
    """
    統一快取管理器 - 提供各服務專用的快取實例

    集中管理所有服務的快取設定，提供統一的介面與統計資訊
    """

    # TTL 設定 (集中管理，單位：秒)
    TTL_BUS_TIMETABLE = 60      # 公車時刻表 60 秒
    TTL_BUS_ROUTES = 3600       # 公車路線 1 小時
    TTL_BUS_STOPS = 3600        # 公車站點 1 小時
    TTL_BUS_ROUTE_STOPS = 1800  # 路線站點順序 30 分鐘
    TTL_BUS_ETA = 30            # 公車 ETA 30 秒
    TTL_BUS_STOP_POSITIONS = 7200  # 站點位置 2 小時

    TTL_TRA_STATIONS = 3600     # 台鐵站點 1 小時
    TTL_TRA_TIMETABLE = 300     # 台鐵時刻表 5 分鐘

    TTL_THSR_STATIONS = 3600    # 高鐵站點 1 小時
    TTL_THSR_TIMETABLE = 300    # 高鐵時刻表 5 分鐘

    TTL_BIKE_STATIONS = 3600    # UBike 站點 1 小時
    TTL_BIKE_AVAILABILITY = 60  # UBike 車位 60 秒

    def __init__(self):
        """初始化統一快取管理器"""
        self._initialized = False

        # 各服務專用快取實例
        self._bus_timetable_cache: Optional[MemoryCache] = None
        self._bus_routes_cache: Optional[MemoryCache] = None
        self._bus_stops_cache: Optional[MemoryCache] = None
        self._bus_route_stops_cache: Optional[MemoryCache] = None
        self._bus_eta_cache: Optional[MemoryCache] = None
        self._bus_stop_positions_cache: Optional[MemoryCache] = None

        self._tra_stations_cache: Optional[MemoryCache] = None
        self._tra_timetable_cache: Optional[MemoryCache] = None

        self._thsr_stations_cache: Optional[MemoryCache] = None
        self._thsr_timetable_cache: Optional[MemoryCache] = None

        self._bike_stations_cache: Optional[MemoryCache] = None
        self._bike_availability_cache: Optional[MemoryCache] = None

        # 統計資訊
        self._cache_names = {
            'bus_timetable': '公車時刻表快取',
            'bus_routes': '公車路線快取',
            'bus_stops': '公車站點快取',
            'bus_route_stops': '路線站點順序快取',
            'bus_eta': '公車 ETA 快取',
            'bus_stop_positions': '公車站點位置快取',
            'tra_stations': '台鐵站點快取',
            'tra_timetable': '台鐵時刻表快取',
            'thsr_stations': '高鐵站點快取',
            'thsr_timetable': '高鐵時刻表快取',
            'bike_stations': 'UBike 站點快取',
            'bike_availability': 'UBike 車位快取',
        }

    async def initialize(self):
        """初始化所有快取實例"""
        if self._initialized:
            return

        logger.info("初始化統一快取管理器...")

        # 公車相關快取
        self._bus_timetable_cache = MemoryCache(
            max_size=1000,
            default_ttl=self.TTL_BUS_TIMETABLE,
            cleanup_interval=60
        )
        await self._bus_timetable_cache.start()

        self._bus_routes_cache = MemoryCache(
            max_size=500,
            default_ttl=self.TTL_BUS_ROUTES,
            cleanup_interval=300
        )
        await self._bus_routes_cache.start()

        self._bus_stops_cache = MemoryCache(
            max_size=2000,
            default_ttl=self.TTL_BUS_STOPS,
            cleanup_interval=300
        )
        await self._bus_stops_cache.start()

        self._bus_route_stops_cache = MemoryCache(
            max_size=1000,
            default_ttl=self.TTL_BUS_ROUTE_STOPS,
            cleanup_interval=300
        )
        await self._bus_route_stops_cache.start()

        self._bus_eta_cache = MemoryCache(
            max_size=2000,
            default_ttl=self.TTL_BUS_ETA,
            cleanup_interval=30
        )
        await self._bus_eta_cache.start()

        self._bus_stop_positions_cache = MemoryCache(
            max_size=5000,
            default_ttl=self.TTL_BUS_STOP_POSITIONS,
            cleanup_interval=600
        )
        await self._bus_stop_positions_cache.start()

        # 台鐵相關快取
        self._tra_stations_cache = MemoryCache(
            max_size=300,
            default_ttl=self.TTL_TRA_STATIONS,
            cleanup_interval=300
        )
        await self._tra_stations_cache.start()

        self._tra_timetable_cache = MemoryCache(
            max_size=500,
            default_ttl=self.TTL_TRA_TIMETABLE,
            cleanup_interval=60
        )
        await self._tra_timetable_cache.start()

        # 高鐵相關快取
        self._thsr_stations_cache = MemoryCache(
            max_size=20,
            default_ttl=self.TTL_THSR_STATIONS,
            cleanup_interval=300
        )
        await self._thsr_stations_cache.start()

        self._thsr_timetable_cache = MemoryCache(
            max_size=500,
            default_ttl=self.TTL_THSR_TIMETABLE,
            cleanup_interval=60
        )
        await self._thsr_timetable_cache.start()

        # UBike 相關快取
        self._bike_stations_cache = MemoryCache(
            max_size=2000,
            default_ttl=self.TTL_BIKE_STATIONS,
            cleanup_interval=300
        )
        await self._bike_stations_cache.start()

        self._bike_availability_cache = MemoryCache(
            max_size=2000,
            default_ttl=self.TTL_BIKE_AVAILABILITY,
            cleanup_interval=60
        )
        await self._bike_availability_cache.start()

        self._initialized = True
        logger.info("統一快取管理器初始化完成")

    async def shutdown(self):
        """關閉所有快取實例"""
        logger.info("關閉統一快取管理器...")

        caches = [
            self._bus_timetable_cache,
            self._bus_routes_cache,
            self._bus_stops_cache,
            self._bus_route_stops_cache,
            self._bus_eta_cache,
            self._bus_stop_positions_cache,
            self._tra_stations_cache,
            self._tra_timetable_cache,
            self._thsr_stations_cache,
            self._thsr_timetable_cache,
            self._bike_stations_cache,
            self._bike_availability_cache,
        ]

        for cache in caches:
            if cache:
                try:
                    await cache.stop()
                except Exception as e:
                    logger.error(f"關閉快取時發生錯誤: {e}")

        self._initialized = False
        logger.info("統一快取管理器已關閉")

    # ==================== 公車快取屬性 ====================

    @property
    def bus_timetable_cache(self) -> MemoryCache:
        """公車時刻表快取 (TTL: 60秒)"""
        if not self._initialized:
            raise RuntimeError("快取管理器尚未初始化，請先呼叫 initialize()")
        return self._bus_timetable_cache

    @property
    def bus_routes_cache(self) -> MemoryCache:
        """公車路線快取 (TTL: 1小時)"""
        if not self._initialized:
            raise RuntimeError("快取管理器尚未初始化，請先呼叫 initialize()")
        return self._bus_routes_cache

    @property
    def bus_stops_cache(self) -> MemoryCache:
        """公車站點快取 (TTL: 1小時)"""
        if not self._initialized:
            raise RuntimeError("快取管理器尚未初始化，請先呼叫 initialize()")
        return self._bus_stops_cache

    @property
    def bus_route_stops_cache(self) -> MemoryCache:
        """路線站點順序快取 (TTL: 30分鐘)"""
        if not self._initialized:
            raise RuntimeError("快取管理器尚未初始化，請先呼叫 initialize()")
        return self._bus_route_stops_cache

    @property
    def bus_eta_cache(self) -> MemoryCache:
        """公車 ETA 快取 (TTL: 30秒)"""
        if not self._initialized:
            raise RuntimeError("快取管理器尚未初始化，請先呼叫 initialize()")
        return self._bus_eta_cache

    @property
    def bus_stop_positions_cache(self) -> MemoryCache:
        """公車站點位置快取 (TTL: 2小時)"""
        if not self._initialized:
            raise RuntimeError("快取管理器尚未初始化，請先呼叫 initialize()")
        return self._bus_stop_positions_cache

    # ==================== 台鐵快取屬性 ====================

    @property
    def tra_cache(self) -> MemoryCache:
        """台鐵時刻表快取 (TTL: 5分鐘)"""
        if not self._initialized:
            raise RuntimeError("快取管理器尚未初始化，請先呼叫 initialize()")
        return self._tra_timetable_cache

    @property
    def tra_stations_cache(self) -> MemoryCache:
        """台鐵站點快取 (TTL: 1小時)"""
        if not self._initialized:
            raise RuntimeError("快取管理器尚未初始化，請先呼叫 initialize()")
        return self._tra_stations_cache

    # ==================== 高鐵快取屬性 ====================

    @property
    def thsr_cache(self) -> MemoryCache:
        """高鐵時刻表快取 (TTL: 5分鐘)"""
        if not self._initialized:
            raise RuntimeError("快取管理器尚未初始化，請先呼叫 initialize()")
        return self._thsr_timetable_cache

    @property
    def thsr_stations_cache(self) -> MemoryCache:
        """高鐵站點快取 (TTL: 1小時)"""
        if not self._initialized:
            raise RuntimeError("快取管理器尚未初始化，請先呼叫 initialize()")
        return self._thsr_stations_cache

    # ==================== UBike 快取屬性 ====================

    @property
    def bike_cache(self) -> MemoryCache:
        """UBike 車位快取 (TTL: 60秒)"""
        if not self._initialized:
            raise RuntimeError("快取管理器尚未初始化，請先呼叫 initialize()")
        return self._bike_availability_cache

    @property
    def bike_stations_cache(self) -> MemoryCache:
        """UBike 站點快取 (TTL: 1小時)"""
        if not self._initialized:
            raise RuntimeError("快取管理器尚未初始化，請先呼叫 initialize()")
        return self._bike_stations_cache

    # ==================== 統計資訊 ====================

    def get_all_stats(self) -> Dict[str, Any]:
        """
        取得所有快取的統計資訊

        Returns:
            包含所有快取統計資訊的字典
        """
        stats = {}

        cache_map = {
            'bus_timetable': self._bus_timetable_cache,
            'bus_routes': self._bus_routes_cache,
            'bus_stops': self._bus_stops_cache,
            'bus_route_stops': self._bus_route_stops_cache,
            'bus_eta': self._bus_eta_cache,
            'bus_stop_positions': self._bus_stop_positions_cache,
            'tra_stations': self._tra_stations_cache,
            'tra_timetable': self._tra_timetable_cache,
            'thsr_stations': self._thsr_stations_cache,
            'thsr_timetable': self._thsr_timetable_cache,
            'bike_stations': self._bike_stations_cache,
            'bike_availability': self._bike_availability_cache,
        }

        for key, cache in cache_map.items():
            if cache:
                cache_stats = cache.get_stats()
                stats[key] = {
                    'name': self._cache_names.get(key, key),
                    **cache_stats
                }
            else:
                stats[key] = {
                    'name': self._cache_names.get(key, key),
                    'status': 'not_initialized'
                }

        # 計算總計
        total_hits = sum(s.get('hits', 0) for s in stats.values() if isinstance(s.get('hits'), int))
        total_misses = sum(s.get('misses', 0) for s in stats.values() if isinstance(s.get('misses'), int))
        total_size = sum(s.get('size', 0) for s in stats.values() if isinstance(s.get('size'), int))

        total_requests = total_hits + total_misses
        overall_hit_rate = total_hits / total_requests if total_requests > 0 else 0

        return {
            'caches': stats,
            'summary': {
                'total_hits': total_hits,
                'total_misses': total_misses,
                'total_requests': total_requests,
                'overall_hit_rate': f"{overall_hit_rate:.2%}",
                'total_items': total_size,
                'initialized': self._initialized
            }
        }

    async def clear_all(self):
        """清除所有快取"""
        caches = [
            self._bus_timetable_cache,
            self._bus_routes_cache,
            self._bus_stops_cache,
            self._bus_route_stops_cache,
            self._bus_eta_cache,
            self._bus_stop_positions_cache,
            self._tra_stations_cache,
            self._tra_timetable_cache,
            self._thsr_stations_cache,
            self._thsr_timetable_cache,
            self._bike_stations_cache,
            self._bike_availability_cache,
        ]

        for cache in caches:
            if cache:
                try:
                    await cache.clear()
                except Exception as e:
                    logger.error(f"清除快取時發生錯誤: {e}")

        logger.info("已清除所有快取")

    async def clear_service_cache(self, service_name: str):
        """
        清除指定服務的快取

        Args:
            service_name: 服務名稱 (bus, tra, thsr, bike)
        """
        service_cache_map = {
            'bus': [
                self._bus_timetable_cache,
                self._bus_routes_cache,
                self._bus_stops_cache,
                self._bus_route_stops_cache,
                self._bus_eta_cache,
                self._bus_stop_positions_cache,
            ],
            'tra': [
                self._tra_stations_cache,
                self._tra_timetable_cache,
            ],
            'thsr': [
                self._thsr_stations_cache,
                self._thsr_timetable_cache,
            ],
            'bike': [
                self._bike_stations_cache,
                self._bike_availability_cache,
            ],
        }

        caches = service_cache_map.get(service_name, [])
        for cache in caches:
            if cache:
                try:
                    await cache.clear()
                except Exception as e:
                    logger.error(f"清除 {service_name} 快取時發生錯誤: {e}")

        logger.info(f"已清除 {service_name} 服務的快取")


# 全域快取管理器實例
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """
    取得全域快取管理器實例（單例模式）

    Returns:
        CacheManager: 快取管理器實例
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


async def initialize_cache_manager():
    """初始化全域快取管理器"""
    manager = get_cache_manager()
    await manager.initialize()
    return manager


async def shutdown_cache_manager():
    """關閉全域快取管理器"""
    global _cache_manager
    if _cache_manager:
        await _cache_manager.shutdown()
        _cache_manager = None
