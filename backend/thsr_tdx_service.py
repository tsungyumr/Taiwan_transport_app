"""
高鐵 TDX API 服務模組
提供高鐵時刻表、站點等資料的查詢功能

API 文件參考:
- 站點: https://tdx.transportdata.tw/api-service/swagger/basic/2998e851-81d0-40f5-b26d-77e2f5ac4118#/THSR/THSRApi_Station_2120
- 時刻表: https://tdx.transportdata.tw/api-service/swagger/basic/2998e851-81d0-40f5-b26d-77e2f5ac4118#/THSR/THSRApi_GeneralTimetable_2122
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple

import httpx
from tdx_auth import get_tdx_auth, TDXAuth

logger = logging.getLogger(__name__)

# TDX API 基礎網址
TDX_API_BASE_URL = "https://tdx.transportdata.tw/api/basic/v2"

# 快取設定（秒）
CACHE_TTL_STATIONS = 3600       # 站點資料快取 1 小時
CACHE_TTL_TIMETABLE = 300       # 時刻表快取 5 分鐘


class THSRTDXService:
    """
    高鐵 TDX API 服務類別

    提供高鐵相關資料的查詢功能，包括：
    - 站點資料查詢
    - 時刻表查詢
    """

    def __init__(self, auth: Optional[TDXAuth] = None):
        """
        初始化高鐵服務

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

    async def get_stations(self) -> List[Dict[str, Any]]:
        """
        取得高鐵所有站點資料

        API: GET /basic/v2/Rail/THSR/Station

        Returns:
            站點資料列表，每個站點包含:
            - StationUID: 站點唯一識別碼
            - StationID: 站點代碼 (如: 0990, 1000)
            - StationName: 站點名稱 (Zh_tw, En)
            - StationPosition: 站點位置
            - StationAddress: 站點地址
            - OperatorID: 營運業者代碼
            - UpdateTime: 資料更新時間
        """
        logger.info("取得高鐵站點資料")

        # 檢查快取
        cache_key = "thsr_stations"
        cached_data = self._get_cached(cache_key, CACHE_TTL_STATIONS)
        if cached_data is not None:
            return cached_data

        try:
            data = await self._make_request("Rail/THSR/Station")
            # TDX API 直接回傳列表
            if isinstance(data, list):
                stations = data
            else:
                stations = data.get("Stations", [])
            logger.info(f"成功取得 {len(stations)} 個高鐵站點")
            # 存入快取
            self._set_cached(cache_key, stations)
            return stations
        except Exception as e:
            logger.error(f"取得高鐵站點資料失敗: {e}")
            raise

    async def get_general_timetable(
        self,
        train_no: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        取得高鐵定期時刻表資料

        API: GET /basic/v2/Rail/THSR/GeneralTimetable

        Args:
            train_no: 車次代碼（選填，如提供則只回傳該車次）

        Returns:
            時刻表資料列表，每筆資料包含:
            - GeneralTimetable: 時刻表資訊
                - GeneralTrainInfo: 列車資訊
                    - TrainNo: 車次代碼
                    - Direction: 行駛方向 (0: 南下, 1: 北上)
                    - StartingStationID: 起始站代碼
                    - StartingStationName: 起始站名稱
                    - EndingStationID: 終點站代碼
                    - EndingStationName: 終點站名稱
                - StopTimes: 停靠時間列表
                    - StopSequence: 停靠順序
                    - StationID: 站點代碼
                    - StationName: 站點名稱
                    - ArrivalTime: 到站時間
                    - DepartureTime: 離站時間
        """
        logger.info(f"取得高鐵定期時刻表資料，車次: {train_no or '全部'}")

        # 檢查快取
        cache_key = f"thsr_timetable_{train_no or 'all'}"
        cached_data = self._get_cached(cache_key, CACHE_TTL_TIMETABLE)
        if cached_data is not None:
            return cached_data

        try:
            params = {}
            if train_no:
                params["$filter"] = f"TrainNo eq '{train_no}'"

            data = await self._make_request("Rail/THSR/GeneralTimetable", params)
            # TDX API 直接回傳列表
            if isinstance(data, list):
                timetables = data
            else:
                timetables = data.get("Timetables", [])
            logger.info(f"成功取得 {len(timetables)} 筆高鐵時刻表資料")
            # 存入快取
            self._set_cached(cache_key, timetables)
            return timetables
        except Exception as e:
            logger.error(f"取得高鐵時刻表資料失敗: {e}")
            raise

    async def search_timetable(
        self,
        from_station: str,
        to_station: str,
        date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        搜尋指定起訖站的列車時刻表

        Args:
            from_station: 出發站名稱（中文，如 "台北"）
            to_station: 抵達站名稱（中文，如 "台中"）
            date: 日期（格式: YYYY-MM-DD，選填）

        Returns:
            符合條件的列車列表，每筆包含:
            - train_no: 車次代碼
            - train_type: 車種（高鐵統一為「高鐵」）
            - departure_time: 出發時間
            - arrival_time: 抵達時間
            - from_station: 起站名稱
            - to_station: 訖站名稱
            - duration: 行車時間（分鐘）
        """
        logger.info(f"搜尋高鐵時刻表: {from_station} -> {to_station}")

        # 取得所有時刻表
        timetables = await self.get_general_timetable()

        results = []

        for tt in timetables:
            # TDX API 回傳的結構
            general_timetable = tt.get("GeneralTimetable", {})
            train_info = general_timetable.get("GeneralTrainInfo", {})
            stop_times = general_timetable.get("StopTimes", [])

            # 尋找起訖站在停靠站列表中的位置
            from_idx = None
            to_idx = None

            for idx, stop in enumerate(stop_times):
                station_name = stop.get("StationName", {}).get("Zh_tw", "")
                if station_name == from_station:
                    from_idx = idx
                elif station_name == to_station:
                    to_idx = idx

            # 如果找到起訖站，且起站在訖站之前
            if from_idx is not None and to_idx is not None and from_idx < to_idx:
                from_stop = stop_times[from_idx]
                to_stop = stop_times[to_idx]

                # 計算行車時間
                dep_time_str = from_stop.get("DepartureTime", "")
                arr_time_str = to_stop.get("ArrivalTime", "")
                duration = self._calculate_duration(dep_time_str, arr_time_str)

                results.append({
                    "train_no": train_info.get("TrainNo", ""),
                    "train_type": "高鐵",
                    "departure_time": dep_time_str,
                    "arrival_time": arr_time_str,
                    "from_station": from_station,
                    "to_station": to_station,
                    "duration": duration,
                    "direction": train_info.get("Direction", 0),
                })

        # 依照出發時間排序
        results.sort(key=lambda x: x["departure_time"])

        logger.info(f"找到 {len(results)} 班高鐵列車")
        return results

    def _calculate_duration(self, dep_time: str, arr_time: str) -> Optional[int]:
        """
        計算兩個時間點之間的分鐘數

        Args:
            dep_time: 出發時間 (HH:MM)
            arr_time: 抵達時間 (HH:MM)

        Returns:
            分鐘數，如果計算失敗則回傳 None
        """
        try:
            dep_parts = dep_time.split(":")
            arr_parts = arr_time.split(":")

            dep_minutes = int(dep_parts[0]) * 60 + int(dep_parts[1])
            arr_minutes = int(arr_parts[0]) * 60 + int(arr_parts[1])

            # 處理跨日情況
            if arr_minutes < dep_minutes:
                arr_minutes += 24 * 60

            return arr_minutes - dep_minutes
        except (ValueError, IndexError):
            return None

    async def get_station_by_id(self, station_id: str) -> Optional[Dict[str, Any]]:
        """
        根據站點代碼取得站點詳細資料

        Args:
            station_id: 站點代碼（如 "1000"）

        Returns:
            站點資料，如果找不到則回傳 None
        """
        stations = await self.get_stations()
        for station in stations:
            if station.get("StationID") == station_id:
                return station
        return None

    async def get_station_by_name(self, station_name: str) -> Optional[Dict[str, Any]]:
        """
        根據站名取得站點詳細資料

        Args:
            station_name: 站點名稱（中文）

        Returns:
            站點資料，如果找不到則回傳 None
        """
        stations = await self.get_stations()
        for station in stations:
            name = station.get("StationName", {}).get("Zh_tw", "")
            if name == station_name:
                return station
        return None


# 建立全域服務實例
_thsr_service_instance: Optional[THSRTDXService] = None


def get_thsr_service(auth: Optional[TDXAuth] = None) -> THSRTDXService:
    """
    取得高鐵服務實例（單例模式）

    Args:
        auth: TDX 認證實例

    Returns:
        THSRTDXService 實例
    """
    global _thsr_service_instance
    if _thsr_service_instance is None:
        _thsr_service_instance = THSRTDXService(auth)
    return _thsr_service_instance


# 測試函數
async def test_thsr_service():
    """測試高鐵服務功能"""
    print("=" * 60)
    print("測試高鐵 TDX API 服務")
    print("=" * 60)

    service = get_thsr_service()

    try:
        # 測試取得站點
        print("\n1. 測試取得站點資料...")
        stations = await service.get_stations()
        print(f"   [OK] 取得 {len(stations)} 個站點")
        for station in stations[:5]:
            print(f"   - {station.get('StationName', {}).get('Zh_tw')} (ID: {station.get('StationID')})")

        # 測試搜尋時刻表
        print("\n2. 測試搜尋時刻表 (台北 -> 台中)...")
        trains = await service.search_timetable("台北", "台中")
        print(f"   [OK] 找到 {len(trains)} 班列車")
        for train in trains[:5]:
            duration = train.get('duration')
            duration_str = f"{duration//60}:{duration%60:02d}" if duration else "N/A"
            print(f"   - {train['train_no']}: {train['departure_time']} -> {train['arrival_time']} ({duration_str})")

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

    asyncio.run(test_thsr_service())
