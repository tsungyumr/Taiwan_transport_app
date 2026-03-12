"""
新北市公車資料服務
提供路線、站牌、到站時間的整合查詢功能
"""

from typing import List, Optional, Dict
from pathlib import Path
import csv

from models.ntpc_bus_models import (
    BusStopInfo,
    BusRouteInfo,
    BusEstimation,
    BusStopWithETA,
    BusRouteSummary
)
from .ntpc_csv_service import CSVDownloader


class NTPCBusService:
    """
    新北市公車資料服務

    提供以下功能：
    1. 載入路線、站牌、預估資料
    2. 路線搜尋
    3. 站牌查詢
    4. 到站時間查詢
    """

    def __init__(self, data_dir: str = "data/ntpc_bus"):
        """
        初始化服務

        Args:
            data_dir: 資料檔案目錄
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._routes: Dict[str, BusRouteInfo] = {}
        self._stops: Dict[str, List[BusStopInfo]] = {}
        self._estimations: Dict[str, BusEstimation] = {}

        self.downloader = CSVDownloader(data_dir)

    async def initialize(self):
        """
        初始化資料
        下載並載入所有必要資料
        """
        # 下載資料
        await self.downloader.download_all()

        # 載入資料
        self.load_data()

    def load_data(self):
        """
        從快取檔案載入資料
        """
        self._load_routes()
        self._load_stops()
        self._load_estimations()

    def _load_routes(self):
        """載入路線資料"""
        routes_file = self.downloader.cache.get_file_path('routes')
        if not routes_file.exists():
            return

        self._routes.clear()
        with open(routes_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                route = BusRouteInfo.from_csv_row(row)
                self._routes[route.route_id] = route

    def _load_stops(self):
        """載入站牌資料"""
        stops_file = self.downloader.cache.get_file_path('stops')
        if not stops_file.exists():
            return

        self._stops.clear()
        with open(stops_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                stop = BusStopInfo.from_csv_row(row)
                key = f"{stop.route_id}_{stop.direction}"
                if key not in self._stops:
                    self._stops[key] = []
                self._stops[key].append(stop)

        # 排序站牌
        for key in self._stops:
            self._stops[key].sort(key=lambda x: x.sequence)

    def _load_estimations(self):
        """載入預估到站資料"""
        estimations_file = self.downloader.cache.get_file_path('estimations')
        if not estimations_file.exists():
            return

        self._estimations.clear()
        with open(estimations_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                est = BusEstimation.from_csv_row(row)
                key = f"{est.route_id}_{est.stop_id}_{est.direction}"
                self._estimations[key] = est

    def get_all_routes(self) -> List[BusRouteInfo]:
        """
        取得所有路線

        Returns:
            路線資訊列表
        """
        return list(self._routes.values())

    def get_route(self, route_id: str) -> Optional[BusRouteInfo]:
        """
        取得特定路線資訊

        Args:
            route_id: 路線代碼

        Returns:
            路線資訊，找不到則回傳 None
        """
        return self._routes.get(route_id)

    def search_routes(self, keyword: str) -> List[BusRouteInfo]:
        """
        搜尋路線

        Args:
            keyword: 搜尋關鍵字

        Returns:
            符合的路線列表
        """
        keyword = keyword.lower()
        results = []

        for route in self._routes.values():
            if (keyword in route.route_id.lower() or
                keyword in route.name_zh.lower() or
                keyword in route.departure_zh.lower() or
                keyword in route.destination_zh.lower()):
                results.append(route)

        return results

    def get_route_stops(self, route_id: str, direction: int = 0) -> List[BusStopInfo]:
        """
        取得路線站牌列表

        Args:
            route_id: 路線代碼
            direction: 方向 (0=去程, 1=返程)

        Returns:
            站牌列表（依站序排序）
        """
        key = f"{route_id}_{direction}"
        return self._stops.get(key, [])

    def get_stop_estimation(self, route_id: str, stop_id: str, direction: int = 0) -> Optional[BusEstimation]:
        """
        取得站牌預估到站時間

        Args:
            route_id: 路線代碼
            stop_id: 站牌代碼
            direction: 方向

        Returns:
            預估到站資訊，找不到則回傳 None
        """
        key = f"{route_id}_{stop_id}_{direction}"
        return self._estimations.get(key)

    def get_route_stops_with_eta(self, route_id: str, direction: int = 0) -> List[BusStopWithETA]:
        """
        取得路線站牌列表（包含到站時間）

        Args:
            route_id: 路線代碼
            direction: 方向

        Returns:
            帶有到站時間的站牌列表
        """
        stops = self.get_route_stops(route_id, direction)
        result = []

        for stop in stops:
            estimation = self.get_stop_estimation(route_id, stop.stop_id, direction)
            stop_with_eta = BusStopWithETA.from_stop_and_estimation(stop, estimation)
            result.append(stop_with_eta)

        return result

    def get_route_summaries(self) -> List[BusRouteSummary]:
        """
        取得所有路線摘要

        Returns:
            路線摘要列表
        """
        return [BusRouteSummary.from_route_info(route) for route in self._routes.values()]

    async def refresh_estimations(self):
        """
        重新整理到站時間資料
        用於即時更新
        """
        await self.downloader.download_estimations(force=True)
        self._load_estimations()

    async def close(self):
        """清理資源"""
        await self.downloader.close()

    def get_nearby_stops(
        self,
        lat: float,
        lon: float,
        radius: float = 1000.0,
        limit: int = 10
    ) -> List[Dict]:
        """
        取得指定座標附近的公車站點

        使用 Haversine 公式計算距離，返回附近站點及其所屬路線資訊

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
        from math import radians, cos, sin, asin, sqrt

        def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            """計算兩點間距離（公尺）"""
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371000  # 地球半徑（公尺）
            return c * r

        nearby_stops = []

        # 遍歷所有路線的所有站點
        for key, stops in self._stops.items():
            for stop in stops:
                # 跳過沒有座標的站點
                if stop.latitude is None or stop.longitude is None:
                    continue

                # 計算距離
                distance = haversine(lat, lon, stop.latitude, stop.longitude)

                if distance <= radius:
                    # 取得路線資訊
                    route = self._routes.get(stop.route_id)
                    if route:
                        nearby_stops.append({
                            "stop_id": stop.stop_id,
                            "name": stop.name_zh,
                            "route_id": stop.route_id,
                            "route_name": route.name_zh,
                            "direction": stop.direction,
                            "sequence": stop.sequence,
                            "latitude": stop.latitude,
                            "longitude": stop.longitude,
                            "distance": round(distance, 1),
                            "departure": route.departure_zh,
                            "destination": route.destination_zh
                        })

        # 按距離排序
        nearby_stops.sort(key=lambda x: x["distance"])

        # 限制數量
        return nearby_stops[:limit]
