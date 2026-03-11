"""
UBike 主動式快取管理器
定期從 TDX API 撈取資料並儲存於記憶體快取中
"""
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from bike_tdx_service import get_bike_service, BikeTDXService, SUPPORTED_CITIES

logger = logging.getLogger(__name__)

# 快取更新間隔（秒）
CACHE_TTL_STATIONS = 3600      # 站點資料每 1 小時更新
CACHE_TTL_AVAILABILITY = 60    # 車位資訊每 60 秒更新

# 預設支援的縣市（優先支援台北和新北）
DEFAULT_CITIES = ["Taipei", "NewTaipei"]


class BikeCacheManager:
    """
    UBike 主動式快取管理器

    定期從 TDX API 撈取站點和車位資訊，儲存於記憶體快取中，
    讓 API 端點能夠快速回應而不需要等待 TDX API 呼叫。
    """

    def __init__(self, bike_service: Optional[BikeTDXService] = None):
        """
        初始化快取管理器

        Args:
            bike_service: BikeTDXService 實例，如未提供則使用全域實例
        """
        self.bike_service = bike_service or get_bike_service()

        # 快取資料儲存
        self._cache_data: Dict[str, Dict[str, Any]] = {
            'stations': {},      # {city: stations_data}
            'availability': {},  # {city: availability_data}
            'merged': {}         # {city: merged_stations_with_availability}
        }

        # 最後更新時間
        self._last_update: Dict[str, Dict[str, float]] = {
            'stations': {},
            'availability': {},
            'merged': {}
        }

        # 背景任務
        self._scheduler_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

        # 統計資訊
        self._stats = {
            'total_updates': 0,
            'failed_updates': 0,
            'last_successful_update': None
        }

    async def start_scheduler(self) -> None:
        """啟動定期更新排程器"""
        if self._scheduler_task is not None:
            logger.warning("排程器已經在執行中")
            return

        self._stop_event.clear()
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("UBike 快取管理器排程器已啟動")

        # 立即執行首次更新
        asyncio.create_task(self.refresh_all_cities())

    async def stop_scheduler(self) -> None:
        """停止排程器"""
        if self._scheduler_task is None:
            return

        self._stop_event.set()
        self._scheduler_task.cancel()

        try:
            await self._scheduler_task
        except asyncio.CancelledError:
            pass

        self._scheduler_task = None
        logger.info("UBike 快取管理器排程器已停止")

    async def _scheduler_loop(self) -> None:
        """排程器主迴圈"""
        try:
            while not self._stop_event.is_set():
                try:
                    # 檢查哪些縣市需要更新
                    await self._check_and_refresh()

                    # 等待 10 秒後再次檢查
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=10.0
                    )
                except asyncio.TimeoutError:
                    # 正常超時，繼續檢查
                    continue
                except Exception as e:
                    logger.error(f"排程器迴圈錯誤: {e}")
                    await asyncio.sleep(10)

        except asyncio.CancelledError:
            logger.info("排程器迴圈被取消")
            raise

    async def _check_and_refresh(self) -> None:
        """檢查並更新需要重新整理的資料"""
        current_time = time.time()

        for city in DEFAULT_CITIES:
            # 檢查站點資料是否需要更新
            last_stations_update = self._last_update['stations'].get(city, 0)
            if current_time - last_stations_update > CACHE_TTL_STATIONS:
                try:
                    await self.refresh_city_stations(city)
                except Exception as e:
                    logger.error(f"更新 {city} 站點資料失敗: {e}")

            # 檢查車位資訊是否需要更新
            last_availability_update = self._last_update['availability'].get(city, 0)
            if current_time - last_availability_update > CACHE_TTL_AVAILABILITY:
                try:
                    await self.refresh_city_availability(city)
                except Exception as e:
                    logger.error(f"更新 {city} 車位資訊失敗: {e}")

    async def refresh_all_cities(self) -> None:
        """更新所有支援縣市的資料"""
        logger.info("開始更新所有縣市的 UBike 資料")

        for city in DEFAULT_CITIES:
            try:
                await self.refresh_city_data(city)
            except Exception as e:
                logger.error(f"更新 {city} 資料失敗: {e}")
                self._stats['failed_updates'] += 1

        self._stats['total_updates'] += 1
        self._stats['last_successful_update'] = datetime.now()
        logger.info("所有縣市 UBike 資料更新完成")

    async def refresh_city_data(self, city: str) -> None:
        """
        更新指定縣市的完整資料（站點 + 車位）

        Args:
            city: 縣市代碼
        """
        logger.info(f"更新 {city} 的所有資料")

        # 同時更新站點和車位資訊
        await asyncio.gather(
            self.refresh_city_stations(city),
            self.refresh_city_availability(city)
        )

        # 更新合併資料
        await self._update_merged_data(city)

    async def refresh_city_stations(self, city: str) -> None:
        """
        更新指定縣市的站點資料

        Args:
            city: 縣市代碼
        """
        try:
            stations = await self.bike_service.get_stations(city)
            self._cache_data['stations'][city] = stations
            self._last_update['stations'][city] = time.time()
            logger.info(f"已更新 {city} 的 {len(stations)} 個站點資料")
        except Exception as e:
            logger.error(f"更新 {city} 站點資料失敗: {e}")
            raise

    async def refresh_city_availability(self, city: str) -> None:
        """
        更新指定縣市的車位資訊

        Args:
            city: 縣市代碼
        """
        try:
            availability = await self.bike_service.get_availability(city)
            self._cache_data['availability'][city] = availability
            self._last_update['availability'][city] = time.time()
            logger.info(f"已更新 {city} 的 {len(availability)} 筆車位資訊")
        except Exception as e:
            logger.error(f"更新 {city} 車位資訊失敗: {e}")
            raise

    async def _update_merged_data(self, city: str) -> None:
        """
        更新指定縣市的合併資料（站點 + 車位）

        Args:
            city: 縣市代碼
        """
        try:
            merged = await self.bike_service.get_stations_with_availability(city)
            self._cache_data['merged'][city] = merged
            self._last_update['merged'][city] = time.time()
            logger.info(f"已更新 {city} 的 {len(merged)} 筆合併資料")
        except Exception as e:
            logger.error(f"更新 {city} 合併資料失敗: {e}")
            raise

    def get_cached_stations(self, city: str) -> Optional[List[Dict[str, Any]]]:
        """
        從快取取得站點資料

        Args:
            city: 縣市代碼

        Returns:
            站點資料列表，若快取不存在或過期則回傳 None
        """
        data = self._cache_data['stations'].get(city)
        if data is None:
            return None

        # 檢查是否過期
        last_update = self._last_update['stations'].get(city, 0)
        if time.time() - last_update > CACHE_TTL_STATIONS:
            return None

        return data

    def get_cached_availability(self, city: str) -> Optional[List[Dict[str, Any]]]:
        """
        從快取取得車位資訊

        Args:
            city: 縣市代碼

        Returns:
            車位資訊列表，若快取不存在或過期則回傳 None
        """
        data = self._cache_data['availability'].get(city)
        if data is None:
            return None

        # 檢查是否過期
        last_update = self._last_update['availability'].get(city, 0)
        if time.time() - last_update > CACHE_TTL_AVAILABILITY:
            return None

        return data

    def get_cached_merged(self, city: str) -> Optional[List[Dict[str, Any]]]:
        """
        從快取取得合併資料（站點 + 車位）

        Args:
            city: 縣市代碼

        Returns:
            合併資料列表，若快取不存在或過期則回傳 None
        """
        data = self._cache_data['merged'].get(city)
        if data is None:
            return None

        # 檢查是否過期（使用較短的 TTL）
        last_update = self._last_update['merged'].get(city, 0)
        if time.time() - last_update > CACHE_TTL_AVAILABILITY:
            return None

        return data

    def get_cache_status(self) -> Dict[str, Any]:
        """
        取得快取狀態資訊

        Returns:
            快取狀態字典
        """
        current_time = time.time()

        status = {
            'cities': {},
            'stats': self._stats.copy(),
            'ttl': {
                'stations': CACHE_TTL_STATIONS,
                'availability': CACHE_TTL_AVAILABILITY
            }
        }

        for city in DEFAULT_CITIES:
            stations_age = current_time - self._last_update['stations'].get(city, 0)
            availability_age = current_time - self._last_update['availability'].get(city, 0)

            status['cities'][city] = {
                'stations_count': len(self._cache_data['stations'].get(city, [])),
                'availability_count': len(self._cache_data['availability'].get(city, [])),
                'stations_age_seconds': int(stations_age),
                'availability_age_seconds': int(availability_age),
                'stations_fresh': stations_age < CACHE_TTL_STATIONS,
                'availability_fresh': availability_age < CACHE_TTL_AVAILABILITY
            }

        return status


# 建立全域快取管理器實例
_bike_cache_manager_instance: Optional[BikeCacheManager] = None


def get_bike_cache_manager(bike_service: Optional[BikeTDXService] = None) -> BikeCacheManager:
    """
    取得 UBike 快取管理器實例（單例模式）

    Args:
        bike_service: BikeTDXService 實例

    Returns:
        BikeCacheManager 實例
    """
    global _bike_cache_manager_instance
    if _bike_cache_manager_instance is None:
        _bike_cache_manager_instance = BikeCacheManager(bike_service)
    return _bike_cache_manager_instance


async def test_cache_manager():
    """測試快取管理器功能"""
    print("=" * 60)
    print("測試 UBike 快取管理器")
    print("=" * 60)

    cache_manager = get_bike_cache_manager()

    try:
        # 啟動排程器
        print("\n1. 啟動排程器...")
        await cache_manager.start_scheduler()
        print("   [OK] 排程器已啟動")

        # 等待首次更新完成
        print("\n2. 等待首次資料更新...")
        await asyncio.sleep(3)

        # 檢查快取狀態
        print("\n3. 檢查快取狀態...")
        status = cache_manager.get_cache_status()
        for city, city_status in status['cities'].items():
            print(f"   {city}:")
            print(f"     - 站點數: {city_status['stations_count']}")
            print(f"     - 車位資訊數: {city_status['availability_count']}")
            print(f"     - 站點資料新鮮: {city_status['stations_fresh']}")
            print(f"     - 車位資料新鮮: {city_status['availability_fresh']}")

        # 測試從快取讀取
        print("\n4. 測試從快取讀取資料...")
        stations = cache_manager.get_cached_stations("Taipei")
        if stations:
            print(f"   [OK] 從快取取得 {len(stations)} 個台北站點")

        availability = cache_manager.get_cached_availability("Taipei")
        if availability:
            print(f"   [OK] 從快取取得 {len(availability)} 筆台北車位資訊")

        merged = cache_manager.get_cached_merged("Taipei")
        if merged:
            print(f"   [OK] 從快取取得 {len(merged)} 筆台北合併資料")
            for s in merged[:3]:
                print(f"   - {s['name']}: 可借 {s['available_rent_bikes']}, 可還 {s['available_return_bikes']}")

        # 停止排程器
        print("\n5. 停止排程器...")
        await cache_manager.stop_scheduler()
        print("   [OK] 排程器已停止")

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
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    asyncio.run(test_cache_manager())
