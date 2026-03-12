"""
UBike TDX API 服務模組
提供腳踏車租借站點與即時車位資料的查詢功能

API 文件參考:
- 縣市租借站資料: https://tdx.transportdata.tw/api-service/swagger/basic/2998e851-81d0-40f5-b26d-77e2f5ac4118#/Bike/BikeApi_Station_2150
- 即時車位資料: https://tdx.transportdata.tw/api-service/swagger/basic/2998e851-81d0-40f5-b26d-77e2f5ac4118#/Bike/BikeApi_Availability_2151
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from math import radians, sin, cos, sqrt, atan2

import httpx
from tdx_auth import get_tdx_auth, TDXAuth

logger = logging.getLogger(__name__)

# TDX API 基礎網址
TDX_API_BASE_URL = "https://tdx.transportdata.tw/api/basic/v2"

# 支援的縣市代碼
SUPPORTED_CITIES = [
    "Taipei", "NewTaipei", "Taoyuan", "Taichung", "Tainan", "Kaohsiung",
    "Hsinchu", "HsinchuCounty", "MiaoliCounty", "ChanghuaCounty", "PingtungCounty"
]

# 快取設定（秒）
CACHE_TTL_STATIONS = 3600      # 站點資料快取 1 小時
CACHE_TTL_AVAILABILITY = 60    # 車位資訊快取 60 秒
CACHE_TTL_NEARBY_SEARCH = 60   # 附近搜尋結果快取 60 秒


class BikeTDXService:
    """
    UBike TDX API 服務類別

    提供腳踏車租借站相關資料的查詢功能，包括：
    - 站點資料查詢
    - 即時車位資訊查詢
    - 附近站點搜尋
    """

    # 類別層級的請求節流控制（所有實例共享）
    _last_request_time = 0.0
    _min_request_interval = 1.0  # 最小請求間隔（秒），增加到 1 秒
    _lock = asyncio.Lock()  # 用於同步請求節流

    def __init__(self, auth: Optional[TDXAuth] = None):
        """
        初始化 UBike 服務

        Args:
            auth: TDX 認證實例，如未提供則使用全域實例
        """
        self.auth = auth or get_tdx_auth()
        self.base_url = TDX_API_BASE_URL
        # 記憶體快取：{cache_key: (timestamp, data)}
        self._cache: Dict[str, Tuple[float, Any]] = {}

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
        max_retries: int = 5,  # 增加重試次數到 5 次
    ) -> Any:
        """
        發送 TDX API 請求（支援自動重試與速率限制控制）

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
            # 使用類別層級的鎖來同步請求節流（所有實例共享）
            async with self._lock:
                current_time = time.time()
                time_since_last = current_time - BikeTDXService._last_request_time
                if time_since_last < BikeTDXService._min_request_interval:
                    wait = BikeTDXService._min_request_interval - time_since_last
                    logger.debug(f"請求節流，等待 {wait:.2f} 秒")
                    await asyncio.sleep(wait)

            try:
                async with httpx.AsyncClient() as client:
                    # 更新最後請求時間（在鎖保護下）
                    async with self._lock:
                        BikeTDXService._last_request_time = time.time()
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
                    # 速率限制，使用指數退避等待後重試
                    wait_time = 2 ** attempt  # 1秒, 2秒, 4秒, 8秒, 16秒
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

    async def get_stations(self, city: str) -> List[Dict[str, Any]]:
        """
        取得指定縣市的腳踏車租借站資訊

        API: GET /basic/v2/Bike/Station/City/{City}

        Args:
            city: 縣市代碼 (Taipei, NewTaipei, Taichung 等)

        Returns:
            站點資料列表，每個站點包含:
            - StationUID: 站點唯一識別碼
            - StationID: 站點代碼
            - StationName: 站點名稱 (Zh_tw, En)
            - StationPosition: 站點位置
            - StationAddress: 站點地址
            - BikesCapacity: 總車位數
            - ServiceType: 服務類型
            - ServiceStatus: 服務狀態
            - UpdateTime: 資料更新時間
        """
        logger.info(f"取得 {city} 腳踏車租借站資料")

        # 檢查快取
        cache_key = f"bike_stations_{city}"
        cached_data = self._get_cached(cache_key, CACHE_TTL_STATIONS)
        if cached_data is not None:
            return cached_data

        try:
            data = await self._make_request(f"Bike/Station/City/{city}")
            # TDX API 直接回傳列表
            if isinstance(data, list):
                stations = data
            else:
                stations = data.get("Stations", [])
            logger.info(f"成功取得 {len(stations)} 個租借站")
            # 存入快取
            self._set_cached(cache_key, stations)
            return stations
        except Exception as e:
            logger.error(f"取得租借站資料失敗: {e}")
            raise

    async def get_availability(self, city: str) -> List[Dict[str, Any]]:
        """
        取得指定縣市的即時車位資訊

        API: GET /basic/v2/Bike/Availability/City/{City}

        Args:
            city: 縣市代碼

        Returns:
            車位資訊列表，每筆資料包含:
            - StationUID: 站點唯一識別碼
            - StationID: 站點代碼
            - AvailableRentBikes: 可租借車輛數
            - AvailableReturnBikes: 可歸還車位數
            - AvailableRentBikesDetail: 車輛詳細資訊
            - ServiceStatus: 服務狀態
            - UpdateTime: 資料更新時間
        """
        logger.info(f"取得 {city} 即時車位資訊")

        # 檢查快取
        cache_key = f"bike_availability_{city}"
        cached_data = self._get_cached(cache_key, CACHE_TTL_AVAILABILITY)
        if cached_data is not None:
            return cached_data

        try:
            data = await self._make_request(f"Bike/Availability/City/{city}")
            # TDX API 直接回傳列表
            if isinstance(data, list):
                availability = data
            else:
                availability = data.get("Availability", [])
            logger.info(f"成功取得 {len(availability)} 筆車位資訊")
            # 存入快取
            self._set_cached(cache_key, availability)
            return availability
        except Exception as e:
            logger.error(f"取得車位資訊失敗: {e}")
            raise

    async def get_stations_with_availability(self, city: str) -> List[Dict[str, Any]]:
        """
        取得站點與即時車位資訊的合併結果

        Args:
            city: 縣市代碼

        Returns:
            包含站點與車位資訊的合併列表
        """
        logger.info(f"取得 {city} 站點與車位合併資訊")

        # 序列化請求：先取得站點資訊，再取得車位資訊
        # 避免使用 asyncio.gather 同時發送多個請求，防止觸發速率限制
        stations = await self.get_stations(city)
        availability = await self.get_availability(city)

        # 建立車位資訊對照表
        availability_map = {
            item.get("StationUID"): item
            for item in availability
            if item.get("StationUID")
        }

        # 合併資料
        merged = []
        for station in stations:
            station_uid = station.get("StationUID")
            avail = availability_map.get(station_uid, {})

            merged.append({
                "station_uid": station_uid,
                "station_id": station.get("StationID"),
                "name": station.get("StationName", {}).get("Zh_tw", ""),
                "name_en": station.get("StationName", {}).get("En", ""),
                "address": station.get("StationAddress", {}).get("Zh_tw", ""),
                "address_en": station.get("StationAddress", {}).get("En", ""),
                "latitude": station.get("StationPosition", {}).get("PositionLat", 0.0),
                "longitude": station.get("StationPosition", {}).get("PositionLon", 0.0),
                "capacity": station.get("BikesCapacity", 0),
                "service_type": station.get("ServiceType", 0),
                "service_status": station.get("ServiceStatus", 0),
                "available_rent_bikes": avail.get("AvailableRentBikes", 0),
                "available_return_bikes": avail.get("AvailableReturnBikes", 0),
                "general_bikes": avail.get("AvailableRentBikesDetail", {}).get("GeneralBikes"),
                "electric_bikes": avail.get("AvailableRentBikesDetail", {}).get("ElectricBikes"),
                "station_update_time": station.get("UpdateTime"),
                "availability_update_time": avail.get("UpdateTime"),
            })

        logger.info(f"成功合併 {len(merged)} 筆站點與車位資訊")
        return merged

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        使用 Haversine Formula 計算兩點間距離（公尺）

        Args:
            lat1: 第一點緯度
            lon1: 第一點經度
            lat2: 第二點緯度
            lon2: 第二點經度

        Returns:
            兩點間的距離（公尺）
        """
        R = 6371000  # 地球半徑（公尺）
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    def calculate_nearby_from_list(
        self,
        stations: List[Dict[str, Any]],
        lat: float,
        lon: float,
        radius: int = 1000,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        從提供的站點列表計算附近站點（同步版本，適用於快取資料）

        Args:
            stations: 站點資料列表
            lat: 中心點緯度
            lon: 中心點經度
            radius: 搜尋半徑（公尺，預設 1000）
            limit: 回傳數量上限

        Returns:
            按距離排序的附近站點列表
        """
        nearby = []
        for station in stations:
            station_lat = station.get("latitude", 0.0)
            station_lon = station.get("longitude", 0.0)
            distance = self.calculate_distance(lat, lon, station_lat, station_lon)

            if distance <= radius:
                station_with_distance = station.copy()
                station_with_distance["distance"] = round(distance, 1)
                nearby.append(station_with_distance)

        # 按距離排序並限制數量
        nearby.sort(key=lambda x: x["distance"])
        nearby = nearby[:limit]

        return nearby

    async def get_nearby_stations(
        self,
        city: str,
        lat: float,
        lon: float,
        radius: int = 1000,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        取得附近的腳踏車租借站

        Args:
            city: 縣市代碼
            lat: 中心點緯度
            lon: 中心點經度
            radius: 搜尋半徑（公尺，預設 1000）
            limit: 回傳數量上限

        Returns:
            按距離排序的附近站點列表
        """
        logger.info(f"搜尋 {city} 附近 {radius} 公尺內的租借站，中心點 ({lat}, {lon})")

        # 檢查快取
        cache_key = f"bike_nearby_{city}_{lat}_{lon}_{radius}_{limit}"
        cached_data = self._get_cached(cache_key, CACHE_TTL_NEARBY_SEARCH)
        if cached_data is not None:
            return cached_data

        # 取得站點與車位資訊
        stations = await self.get_stations_with_availability(city)

        # 計算距離並篩選
        nearby = []
        for station in stations:
            station_lat = station.get("latitude", 0.0)
            station_lon = station.get("longitude", 0.0)
            distance = self.calculate_distance(lat, lon, station_lat, station_lon)

            if distance <= radius:
                station_with_distance = station.copy()
                station_with_distance["distance"] = round(distance, 1)
                nearby.append(station_with_distance)

        # 按距離排序並限制數量
        nearby.sort(key=lambda x: x["distance"])
        nearby = nearby[:limit]

        logger.info(f"找到 {len(nearby)} 個附近租借站")

        # 存入快取
        self._set_cached(cache_key, nearby)
        return nearby

    async def search_stations(
        self,
        keyword: str,
        city: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        搜尋腳踏車租借站

        Args:
            keyword: 搜尋關鍵字
            city: 指定縣市（未提供則搜尋所有支援的縣市）
            limit: 回傳數量上限

        Returns:
            符合條件的站點列表
        """
        logger.info(f"搜尋關鍵字 '{keyword}'，縣市: {city or '全部'}")

        keyword_lower = keyword.lower()
        results = []

        # 決定搜尋的縣市列表
        cities_to_search = [city] if city else SUPPORTED_CITIES[:2]  # 預設搜尋台北、新北

        for search_city in cities_to_search:
            try:
                stations = await self.get_stations_with_availability(search_city)
                for station in stations:
                    # 檢查關鍵字是否匹配
                    name = station.get("name", "").lower()
                    name_en = station.get("name_en", "").lower()
                    address = station.get("address", "").lower()

                    if (keyword_lower in name or
                        keyword_lower in name_en or
                        keyword_lower in address):
                        station["city"] = search_city
                        results.append(station)
            except Exception as e:
                logger.warning(f"搜尋 {search_city} 失敗: {e}")

        # 限制回傳數量
        results = results[:limit]
        logger.info(f"搜尋 '{keyword}' 找到 {len(results)} 個結果")
        return results

    async def get_station_detail(
        self,
        city: str,
        station_uid: str
    ) -> Optional[Dict[str, Any]]:
        """
        取得特定站點的詳細資訊（含即時車位）

        Args:
            city: 縣市代碼
            station_uid: 站點唯一識別碼

        Returns:
            站點詳細資訊，若找不到則回傳 None
        """
        logger.info(f"取得站點 {station_uid} 詳細資訊")

        stations = await self.get_stations_with_availability(city)

        for station in stations:
            if station.get("station_uid") == station_uid:
                return station

        return None


# 建立全域服務實例
_bike_service_instance: Optional[BikeTDXService] = None


def get_bike_service(auth: Optional[TDXAuth] = None) -> BikeTDXService:
    """
    取得 UBike 服務實例（單例模式）

    Args:
        auth: TDX 認證實例

    Returns:
        BikeTDXService 實例
    """
    global _bike_service_instance
    if _bike_service_instance is None:
        _bike_service_instance = BikeTDXService(auth)
    return _bike_service_instance


# 測試函數
async def test_bike_service():
    """測試 UBike 服務功能"""
    print("=" * 60)
    print("測試 UBike TDX API 服務")
    print("=" * 60)

    service = get_bike_service()

    try:
        # 測試取得台北市租借站
        print("\n1. 測試取得台北市租借站資料...")
        stations = await service.get_stations("Taipei")
        print(f"   [OK] 取得 {len(stations)} 個租借站")
        if stations:
            for station in stations[:3]:
                name = station.get("StationName", {}).get("Zh_tw", "")
                print(f"   - {name}")

        # 測試取得即時車位資訊
        print("\n2. 測試取得台北市即時車位資訊...")
        availability = await service.get_availability("Taipei")
        print(f"   [OK] 取得 {len(availability)} 筆車位資訊")

        # 測試取得站點與車位合併資訊
        print("\n3. 測試取得站點與車位合併資訊...")
        merged = await service.get_stations_with_availability("Taipei")
        print(f"   [OK] 合併 {len(merged)} 筆資訊")
        if merged:
            for s in merged[:3]:
                print(f"   - {s['name']}: 可借 {s['available_rent_bikes']}, 可還 {s['available_return_bikes']}")

        # 測試附近搜尋
        print("\n4. 測試附近搜尋 (台北市政府附近)...")
        nearby = await service.get_nearby_stations(
            "Taipei",
            lat=25.040857,
            lon=121.564812,
            radius=500,
            limit=5
        )
        print(f"   [OK] 找到 {len(nearby)} 個附近租借站")
        for s in nearby:
            print(f"   - {s['name']}: 距離 {s['distance']} 公尺")

        # 測試搜尋
        print("\n5. 測試搜尋功能 (市政府)...")
        search_results = await service.search_stations("市政府", city="Taipei", limit=5)
        print(f"   [OK] 搜尋到 {len(search_results)} 個結果")
        for s in search_results:
            print(f"   - {s['name']}")

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

    asyncio.run(test_bike_service())
