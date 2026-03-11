"""
公車 TDX API 服務模組
提供大台北地區公車路線、站點、即時動態等資料的查詢功能

API 文件參考:
- 縣市站牌資料: https://tdx.transportdata.tw/api-service/swagger/basic/2998e851-81d0-40f5-b26d-77e2f5ac4118#/CityBus/CityBusApi_Stop_2036
- 縣市公車路線資料: https://tdx.transportdata.tw/api-service/swagger/basic/2998e851-81d0-40f5-b26d-77e2f5ac4118#/CityBus/CityBusApi_Route_2035_1
- 指定縣市路線公車動態資料: https://tdx.transportdata.tw/api-service/swagger/basic/2998e851-81d0-40f5-b26d-77e2f5ac4118#/CityBus/CityBusApi_RealTimeByFrequency_UDP_2046_1
"""
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple

import httpx
from tdx_auth import get_tdx_auth, TDXAuth

logger = logging.getLogger(__name__)

# TDX API 基礎網址
TDX_API_BASE_URL = "https://tdx.transportdata.tw/api/basic/v2"

# 大台北地區縣市代碼
TAIPEI_CITIES = ["Taipei", "NewTaipei"]

# 快取設定（秒）
CACHE_TTL_ROUTES = 3600  # 路線資料快取 1 小時
CACHE_TTL_STOPS = 3600   # 站點資料快取 1 小時
CACHE_TTL_STOP_POSITIONS = 7200  # 站點位置快取 2 小時
CACHE_TTL_ROUTE_STOPS = 1800  # 路線站點順序快取 30 分鐘
CACHE_TTL_ETA = 30       # ETA 資料快取 30 秒


class BusStopPositionCache:
    """
    公車站點位置快取管理器
    定期撈取並快取所有縣市的站點經緯度座標
    """

    def __init__(self, bus_service: 'BusTDXService'):
        self.bus_service = bus_service
        self._stop_positions: Dict[str, Dict[str, float]] = {}  # {stop_uid: {lat, lon}}
        self._last_update: Optional[datetime] = None
        self._update_interval = 3600  # 1 小時更新一次
        self._lock = asyncio.Lock()

    async def get_stop_position(self, stop_uid: str) -> Optional[Dict[str, float]]:
        """取得指定站點的經緯度座標"""
        # 檢查是否需要更新
        if self._needs_update():
            await self._refresh_cache()

        return self._stop_positions.get(stop_uid)

    async def get_multiple_positions(self, stop_uids: List[str]) -> Dict[str, Dict[str, float]]:
        """批量取得多個站點的經緯度座標"""
        if self._needs_update():
            await self._refresh_cache()

        return {
            uid: self._stop_positions[uid]
            for uid in stop_uids
            if uid in self._stop_positions
        }

    def _needs_update(self) -> bool:
        """檢查是否需要更新快取"""
        if not self._last_update:
            return True
        elapsed = (datetime.now() - self._last_update).total_seconds()
        return elapsed > self._update_interval

    async def _refresh_cache(self):
        """重新整理快取資料"""
        async with self._lock:
            # 雙重檢查，避免多個協程同時更新
            if not self._needs_update():
                return

            logger.info("【BusStopPositionCache】開始更新站點位置快取...")
            total_updated = 0

            for city in TAIPEI_CITIES:
                try:
                    stops = await self.bus_service.get_stops(city)
                    for stop in stops:
                        stop_uid = stop.get("StopUID", "")
                        position = stop.get("StopPosition", {})
                        if stop_uid and position:
                            self._stop_positions[stop_uid] = {
                                "latitude": position.get("PositionLat"),
                                "longitude": position.get("PositionLon")
                            }
                            total_updated += 1
                    logger.info(f"【BusStopPositionCache】{city}: 已更新 {len(stops)} 個站點")
                except Exception as e:
                    logger.error(f"【BusStopPositionCache】取得 {city} 站點位置失敗: {e}")

            self._last_update = datetime.now()
            logger.info(f"【BusStopPositionCache】快取更新完成，共 {total_updated} 個站點")

    def get_cache_stats(self) -> Dict[str, Any]:
        """取得快取統計資訊"""
        return {
            "total_stops": len(self._stop_positions),
            "last_update": self._last_update.isoformat() if self._last_update else None,
            "next_update": (self._last_update + timedelta(seconds=self._update_interval)).isoformat()
            if self._last_update else None
        }


class BusTDXService:
    """
    公車 TDX API 服務類別

    提供大台北地區公車相關資料的查詢功能，包括：
    - 路線資料查詢
    - 站點資料查詢
    - 即時車輛動態查詢
    """

    def __init__(self, auth: Optional[TDXAuth] = None):
        """
        初始化公車服務

        Args:
            auth: TDX 認證實例，如未提供則使用全域實例
        """
        self.auth = auth or get_tdx_auth()
        self.base_url = TDX_API_BASE_URL
        # 記憶體快取：{cache_key: (timestamp, data)}
        self._cache: Dict[str, Tuple[float, Any]] = {}
        # 站點位置快取
        self._stop_position_cache = BusStopPositionCache(self)

    def _get_cached(self, key: str, ttl: int) -> Optional[Any]:
        """取得快取資料，若過期則回傳 None"""
        if key not in self._cache:
            return None
        timestamp, data = self._cache[key]
        if time.time() - timestamp > ttl:
            # 過期，刪除快取
            del self._cache[key]
            return None
        logger.debug(f"快取命中: {key}")
        return data

    def _set_cached(self, key: str, data: Any) -> None:
        """設定快取資料"""
        self._cache[key] = (time.time(), data)

    def _clear_cache(self) -> None:
        """清除所有快取"""
        self._cache.clear()
        logger.info("已清除所有快取")

    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> Any:
        """
        發送 TDX API 請求（支援自動重試）

        Args:
            endpoint: API 端點路徑
            params: 查詢參數
            max_retries: 最大重試次數

        Returns:
            API 回應的 JSON 資料

        Raises:
            Exception: 當請求失敗時拋出例外
        """
        headers = await self.auth.get_auth_headers()
        url = f"{self.base_url}/{endpoint}"

        # 預設加入 $format=JSON
        if params is None:
            params = {}
        params["$format"] = "JSON"

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        url,
                        headers=headers,
                        params=params,
                        timeout=30.0,
                    )
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # 速率限制，等待後重試
                    wait_time = 0.5 * (attempt + 1)  # 漸進式等待
                    logger.warning(f"TDX API 速率限制，等待 {wait_time} 秒後重試 ({attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                logger.error(f"TDX API HTTP 錯誤: {e.response.status_code} - {e.response.text}")
                raise Exception(f"TDX API 請求失敗: HTTP {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error(f"TDX API 請求錯誤: {e}")
                raise Exception(f"TDX API 請求失敗: {e}")
            except Exception as e:
                logger.error(f"TDX API 未知錯誤: {e}")
                raise Exception(f"TDX API 請求失敗: {e}")

        # 重試次數用完
        raise Exception(f"TDX API 請求失敗: 超過最大重試次數 ({max_retries})")

    async def get_routes(self, city: str = "Taipei") -> List[Dict[str, Any]]:
        """
        取得指定縣市的公車路線資料

        API: GET /basic/v2/Bus/Route/City/{City}

        Args:
            city: 縣市代碼 (Taipei 或 NewTaipei)

        Returns:
            路線資料列表，每個路線包含:
            - RouteUID: 路線唯一識別碼
            - RouteID: 路線代碼
            - RouteName: 路線名稱 (Zh_tw, En)
            - DepartureStopName: 起點站名
            - DestinationStopName: 終點站名
            - OperatorIDs: 營運業者代碼列表
            - UpdateTime: 資料更新時間
        """
        logger.info(f"取得 {city} 公車路線資料")

        # 檢查快取
        cache_key = f"routes_{city}"
        cached_data = self._get_cached(cache_key, CACHE_TTL_ROUTES)
        if cached_data is not None:
            return cached_data

        try:
            data = await self._make_request(f"Bus/Route/City/{city}")
            # TDX API 直接回傳列表
            if isinstance(data, list):
                routes = data
            else:
                routes = data.get("Routes", [])
            logger.info(f"成功取得 {len(routes)} 條路線")
            # 存入快取
            self._set_cached(cache_key, routes)
            return routes
        except Exception as e:
            logger.error(f"取得公車路線資料失敗: {e}")
            raise

    async def get_all_taipei_routes(self) -> List[Dict[str, Any]]:
        """
        取得大台北地區所有公車路線資料

        Returns:
            台北市和新北市的路線資料列表
        """
        all_routes = []
        for city in TAIPEI_CITIES:
            try:
                routes = await self.get_routes(city)
                # 加入縣市資訊
                for route in routes:
                    route["City"] = city
                all_routes.extend(routes)
            except Exception as e:
                logger.warning(f"取得 {city} 路線資料失敗: {e}")

        logger.info(f"大台北地區共取得 {len(all_routes)} 條路線")
        return all_routes

    async def get_stops(self, city: str = "Taipei") -> List[Dict[str, Any]]:
        """
        取得指定縣市的公車站點資料

        API: GET /basic/v2/Bus/Stop/City/{City}

        Args:
            city: 縣市代碼 (Taipei 或 NewTaipei)

        Returns:
            站點資料列表，每個站點包含:
            - StopUID: 站點唯一識別碼
            - StopID: 站點代碼
            - StopName: 站點名稱 (Zh_tw, En)
            - StopPosition: 站點位置
            - StationID: 車站代碼
            - UpdateTime: 資料更新時間
        """
        logger.info(f"取得 {city} 公車站點資料")

        # 檢查快取
        cache_key = f"stops_{city}"
        cached_data = self._get_cached(cache_key, CACHE_TTL_STOPS)
        if cached_data is not None:
            return cached_data

        try:
            data = await self._make_request(f"Bus/Stop/City/{city}")
            # TDX API 直接回傳列表
            if isinstance(data, list):
                stops = data
            else:
                stops = data.get("Stops", [])
            logger.info(f"成功取得 {len(stops)} 個站點")
            # 存入快取
            self._set_cached(cache_key, stops)
            return stops
        except Exception as e:
            logger.error(f"取得公車站點資料失敗: {e}")
            raise

    async def get_route_stops(
        self,
        route_id: str,
        city: str = "Taipei",
        direction: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        取得指定路線的站點順序資料

        API: GET /basic/v2/Bus/StopOfRoute/City/{City}/{RouteName}

        Args:
            route_id: 路線代碼或名稱
            city: 縣市代碼
            direction: 方向（0=去程, 1=返程），如未指定則回傳所有方向

        Returns:
            站點順序資料列表，每筆資料包含:
            - Direction: 行駛方向
            - Stops: 站點列表，包含 StopUID, StopID, StopName, StopSequence
        """
        logger.info(f"取得 {city} 路線 {route_id} 的站點順序資料")

        # 檢查快取
        cache_key = f"route_stops_{city}_{route_id}_{direction}"
        cached_data = self._get_cached(cache_key, CACHE_TTL_ROUTE_STOPS)
        if cached_data is not None:
            return cached_data

        try:
            params = {}
            if direction is not None:
                params["$filter"] = f"Direction eq {direction}"

            data = await self._make_request(
                f"Bus/StopOfRoute/City/{city}/{route_id}",
                params
            )
            # TDX API 直接回傳列表
            if isinstance(data, list):
                route_stops = data
            else:
                route_stops = data.get("Routes", [])
            logger.info(f"成功取得 {len(route_stops)} 筆站點順序資料")
            # 存入快取
            self._set_cached(cache_key, route_stops)
            return route_stops
        except Exception as e:
            logger.error(f"取得站點順序資料失敗: {e}")
            raise

    async def get_estimated_time_of_arrival(
        self,
        route_id: str,
        city: str = "Taipei",
        direction: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        取得指定路線的公車預估到站時間資料

        API: GET /basic/v2/Bus/EstimatedTimeOfArrival/City/{City}/{RouteName}

        Args:
            route_id: 路線代碼或名稱
            city: 縣市代碼
            direction: 方向（0=去程, 1=返程），如未指定則回傳所有方向

        Returns:
            預估到站時間資料列表，每筆資料包含:
            - StopUID: 站點唯一識別碼
            - StopID: 站點代碼
            - StopName: 站點名稱
            - Direction: 行駛方向
            - EstimateTime: 預估到站時間（秒）
            - StopStatus: 站點狀態（0: 正常, 1: 未發車, 2: 已抵達, 3: 已過站）
            - UpdateTime: 資料更新時間
        """
        logger.info(f"取得 {city} 路線 {route_id} 的預估到站時間")

        # 檢查快取（ETA 快取時間較短）
        cache_key = f"eta_{city}_{route_id}_{direction}"
        cached_data = self._get_cached(cache_key, CACHE_TTL_ETA)
        if cached_data is not None:
            return cached_data

        try:
            params = {}
            if direction is not None:
                params["$filter"] = f"Direction eq {direction}"

            data = await self._make_request(
                f"Bus/EstimatedTimeOfArrival/City/{city}/{route_id}",
                params
            )
            # TDX API 直接回傳列表
            if isinstance(data, list):
                eta_data = data
            else:
                eta_data = data.get("Routes", [])
            logger.info(f"成功取得 {len(eta_data)} 筆預估到站時間資料")
            # 存入快取
            self._set_cached(cache_key, eta_data)
            return eta_data
        except Exception as e:
            logger.error(f"取得預估到站時間失敗: {e}")
            raise

    async def get_realtime_by_route(
        self,
        route_id: str,
        city: str = "Taipei",
    ) -> List[Dict[str, Any]]:
        """
        取得指定路線的公車即時動態資料

        API: GET /basic/v2/Bus/RealTimeByFrequency/City/{City}/{RouteName}

        Args:
            route_id: 路線代碼或名稱
            city: 縣市代碼

        Returns:
            即時動態資料列表，每筆資料包含:
            - PlateNumb: 車牌號碼
            - OperatorID: 營運業者代碼
            - RouteName: 路線名稱
            - Direction: 行駛方向 (0: 去程, 1: 返程)
            - BusPosition: 車輛位置
            - Speed: 速度
            - Azimuth: 方位角
            - UpdateTime: 資料更新時間
        """
        logger.info(f"取得 {city} 路線 {route_id} 的即時動態資料")
        try:
            data = await self._make_request(
                f"Bus/RealTimeByFrequency/City/{city}/{route_id}"
            )
            # TDX API 直接回傳列表
            if isinstance(data, list):
                realtime_data = data
            else:
                realtime_data = data.get("Buses", [])
            logger.info(f"成功取得 {len(realtime_data)} 筆即時動態資料")
            return realtime_data
        except Exception as e:
            logger.error(f"取得即時動態資料失敗: {e}")
            raise

    async def search_routes(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜尋路線

        Args:
            keyword: 搜尋關鍵字

        Returns:
            符合條件的路線列表
        """
        all_routes = await self.get_all_taipei_routes()
        keyword_lower = keyword.lower()

        results = []
        for route in all_routes:
            route_name = route.get("RouteName", {}).get("Zh_tw", "")
            departure = route.get("DepartureStopName", "")
            destination = route.get("DestinationStopName", "")

            if (keyword_lower in route_name.lower() or
                keyword_lower in departure.lower() or
                keyword_lower in destination.lower()):
                results.append(route)

        logger.info(f"搜尋 '{keyword}' 找到 {len(results)} 條路線")
        return results

    def get_route_display_name(self, route: Dict[str, Any]) -> str:
        """
        取得路線顯示名稱

        Args:
            route: 路線資料

        Returns:
            格式化的路線名稱
        """
        route_name = route.get("RouteName", {}).get("Zh_tw", "")
        departure = route.get("DepartureStopName", "")
        destination = route.get("DestinationStopName", "")

        if departure and destination:
            return f"{route_name} ({departure} - {destination})"
        return route_name

    async def get_stop_position(self, stop_uid: str) -> Optional[Dict[str, float]]:
        """
        取得指定站點的經緯度座標

        Args:
            stop_uid: 站點唯一識別碼

        Returns:
            包含 latitude 和 longitude 的字典，若找不到則回傳 None
        """
        return await self._stop_position_cache.get_stop_position(stop_uid)

    async def get_stop_positions_batch(self, stop_uids: List[str]) -> Dict[str, Dict[str, float]]:
        """
        批量取得多個站點的經緯度座標

        Args:
            stop_uids: 站點唯一識別碼列表

        Returns:
            站點UID到座標的對照表
        """
        return await self._stop_position_cache.get_multiple_positions(stop_uids)

    async def refresh_stop_positions(self):
        """強制重新整理站點位置快取"""
        await self._stop_position_cache._refresh_cache()

    def get_stop_position_cache_stats(self) -> Dict[str, Any]:
        """取得站點位置快取統計資訊"""
        return self._stop_position_cache.get_cache_stats()


# 建立全域服務實例
_bus_service_instance: Optional[BusTDXService] = None


def get_bus_service(auth: Optional[TDXAuth] = None) -> BusTDXService:
    """
    取得公車服務實例（單例模式）

    Args:
        auth: TDX 認證實例

    Returns:
        BusTDXService 實例
    """
    global _bus_service_instance
    if _bus_service_instance is None:
        _bus_service_instance = BusTDXService(auth)
    return _bus_service_instance


# 測試函數
async def test_bus_service():
    """測試公車服務功能"""
    print("=" * 60)
    print("測試公車 TDX API 服務")
    print("=" * 60)

    service = get_bus_service()

    try:
        # 測試取得台北市路線
        print("\n1. 測試取得台北市路線資料...")
        routes = await service.get_routes("Taipei")
        print(f"   [OK] 取得 {len(routes)} 條路線")
        if routes:
            for route in routes[:3]:
                display_name = service.get_route_display_name(route)
                print(f"   - {display_name}")

        # 測試搜尋路線
        print("\n2. 測試搜尋路線 (232)...")
        search_results = await service.search_routes("232")
        print(f"   [OK] 找到 {len(search_results)} 條路線")
        for route in search_results[:3]:
            display_name = service.get_route_display_name(route)
            city = route.get("City", "")
            print(f"   - [{city}] {display_name}")

        # 測試取得站點
        print("\n3. 測試取得台北市站點資料...")
        stops = await service.get_stops("Taipei")
        print(f"   [OK] 取得 {len(stops)} 個站點")
        for stop in stops[:3]:
            stop_name = stop.get("StopName", {}).get("Zh_tw", "")
            print(f"   - {stop_name}")

        print("\n" + "=" * 60)
        print("所有測試通過！")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n[FAIL] 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    asyncio.run(test_bus_service())
