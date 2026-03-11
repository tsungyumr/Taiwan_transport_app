"""
台灣交通時刻表 API - TDX 版本
Taiwan Transport Timetable API with TDX

Target Sources:
1. 高鐵時刻表: TDX API (OAuth 2.0)
2. 台鐵時刻表: TDX API (OAuth 2.0)
3. 公車: TDX API (大台北地區)
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import httpx
from datetime import datetime, date
from playwright.async_api import async_playwright, Browser, Page
from THSR_scraper import scrape_thsr_stations
from scrapers.taipei_bus_scraper import TaipeiBusScraper
from tra_tdx_service import get_tra_service
from thsr_tdx_service import get_thsr_service
from bus_tdx_service import get_bus_service
from bike_tdx_service import get_bike_service, SUPPORTED_CITIES
from bike_cache_manager import get_bike_cache_manager
from services.cache_manager import get_cache_manager, initialize_cache_manager, shutdown_cache_manager
# 快取管理器會在 lifespan 中初始化
import os
import random
import logging
from functools import wraps
import asyncio
from collections import deque
from time import time

# 設置 logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== 高鐵站點資料模型 ====================
class THSRStation(BaseModel):
    """高鐵站點資料模型"""
    name: str = Field(description="站點名稱")
    code: str = Field(description="站點代碼")
    info: str = Field(description="站點詳細資訊")
    timestamp: str = Field(description="資料抓取時間")


# ==================== 快取相關 ====================
class THSRStationsCache:
    """高鐵站點列表快取管理器"""
    def __init__(self, ttl=3600):
        self.ttl = ttl  # 1小時 TTL
        self.cache = {}
        self.lock = asyncio.Lock()

    async def get(self) -> Optional[List[dict]]:
        """取得快取的站點資料"""
        async with self.lock:
            entry = self.cache.get("stations")
            if entry and time() - entry["timestamp"] < self.ttl:
                logging.info("使用高鐵站點列表快取")
                return entry["data"]
        return None

    async def set(self, data: List[dict]):
        """設定站點列表快取"""
        async with self.lock:
            self.cache["stations"] = {
                "data": data,
                "timestamp": time()
            }

# ==================== 快取相關 ====================
class RailwayTimetableCache:
    """台鐵時刻表快取管理器"""
    def __init__(self, ttl=300):
        self.ttl = ttl  # 5分鐘 TTL
        self.cache = {}
        self.lock = asyncio.Lock()

    async def get(self, from_station: str, to_station: str, date: str) -> Optional[List[dict]]:
        """取得快取資料"""
        key = f"{from_station}|{to_station}|{date}"
        async with self.lock:
            entry = self.cache.get(key)
            if entry and time() - entry["timestamp"] < self.ttl:
                logging.info(f"使用快取: {from_station} -> {to_station} ({date})")
                return entry["data"]
        return None

    async def set(self, from_station: str, to_station: str, date: str, data: List[dict]):
        """設定快取資料"""
        key = f"{from_station}|{to_station}|{date}"
        async with self.lock:
            self.cache[key] = {
                "data": data,
                "timestamp": time()
            }
            logging.info(f"更新快取: {from_station} -> {to_station} ({date})")

# 建立快取實例
railway_cache = RailwayTimetableCache(ttl=300)
thsr_stations_cache = THSRStationsCache(ttl=3600)

# ==================== 錯誤處理相關 ====================
class RailwayTimetableError(Exception):
    """台鐵時刻表專用錯誤類型"""
    pass

def retry_on_error(max_retries=3, delay=2):
    """錯誤重試裝飾器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except RailwayTimetableError as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logging.warning(f"嘗試 {attempt + 1}/{max_retries} 失敗: {str(e)}")
                        await asyncio.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


# ==================== 全域變數 ====================

# Playwright browser instance
_pw = None
_browser: Browser = None

# 公車快取管理器實例
bus_cache_manager = None

# UBike 快取管理器實例
bike_cache_manager = None

# 新北市 CSV 資料服務實例
_ntpc_bus_service = None

# 記憶體快取實例
_route_cache = None
_estimation_cache = None

# 背景排程器
_background_scheduler = None

def get_ntpc_bus_service():
    """取得新北市公車資料服務（單例）"""
    global _ntpc_bus_service
    if _ntpc_bus_service is None:
        from services.ntpc_bus_service import NTPCBusService
        _ntpc_bus_service = NTPCBusService("./data/ntpc_bus")
    return _ntpc_bus_service


def get_route_cache():
    """取得路線快取（單例）"""
    global _route_cache
    if _route_cache is None:
        from services.memory_cache import MemoryCache
        _route_cache = MemoryCache(max_size=500, default_ttl=600)  # 10 分鐘 TTL
    return _route_cache


def get_estimation_cache():
    """取得到站時間快取（單例）"""
    global _estimation_cache
    if _estimation_cache is None:
        from services.memory_cache import MemoryCache
        _estimation_cache = MemoryCache(max_size=1000, default_ttl=60)  # 1 分鐘 TTL
    return _estimation_cache


def get_background_scheduler():
    """取得背景排程器（單例）"""
    global _background_scheduler
    if _background_scheduler is None:
        from services.background_scheduler import get_scheduler
        _background_scheduler = get_scheduler()
    return _background_scheduler


async def _refresh_estimations():
    """背景任務：重新整理到站時間"""
    global _ntpc_bus_service
    if _ntpc_bus_service:
        try:
            logger.info("背景任務：重新整理到站時間...")
            await _ntpc_bus_service.refresh_estimations()
            # 清除到站時間快取
            cache = get_estimation_cache()
            await cache.clear()
            logger.info("背景任務：到站時間已更新")
        except Exception as e:
            logger.error(f"背景任務：更新到站時間失敗: {e}")


async def _cleanup_cache():
    """背景任務：清理過期快取"""
    try:
        route_cache = get_route_cache()
        estimation_cache = get_estimation_cache()
        # 快取會自動清理，這裡只記錄統計
        logger.debug(f"快取統計 - 路線: {route_cache.get_stats()}")
        logger.debug(f"快取統計 - 到站時間: {estimation_cache.get_stats()}")
    except Exception as e:
        logger.error(f"背景任務：清理快取失敗: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global _pw, _browser, bus_cache_manager, _ntpc_bus_service, _route_cache, _estimation_cache
    global bike_cache_manager

    # Startup: init Playwright
    _pw = await async_playwright().start()
    _browser = await _pw.chromium.launch(
        headless=True,
        args=['--disable-blink-features=AutomationControlled']
    )
    print("Playwright browser started")

    # Startup: 初始化公車快取管理器（懶加載模式，不預先撈取）
    from cache.bus_cache_manager import TaipeiBusCacheManager
    bus_cache_manager = TaipeiBusCacheManager()  # 懶加載模式，不設定更新間隔
    await bus_cache_manager.start()
    print("公車快取管理器已啟動（懶加載模式，快取過期時間：60秒）")

    # Startup: 初始化 UBike 快取管理器（主動式快取）
    try:
        bike_cache_manager = get_bike_cache_manager()
        await bike_cache_manager.start_scheduler()
        print("UBike 快取管理器已啟動（主動式快取，站點每小時更新，車位每60秒更新）")
    except Exception as e:
        print(f"UBike 快取管理器初始化失敗：{e}")
        bike_cache_manager = None

    # Startup: 初始化新北市 CSV 資料服務
    try:
        from services.ntpc_bus_service import NTPCBusService
        _ntpc_bus_service = NTPCBusService("./data/ntpc_bus")
        # 載入現有資料（不重新下載）
        _ntpc_bus_service.load_data()
        routes_count = len(_ntpc_bus_service._routes)
        print(f"新北市公車 CSV 資料服務已初始化，載入 {routes_count} 條路線")
    except Exception as e:
        print(f"新北市公車 CSV 資料服務初始化失敗：{e}")
        _ntpc_bus_service = None

    # Startup: 初始化記憶體快取
    try:
        _route_cache = get_route_cache()
        _estimation_cache = get_estimation_cache()
        await _route_cache.start()
        await _estimation_cache.start()
        print("記憶體快取服務已啟動")
    except Exception as e:
        print(f"記憶體快取服務初始化失敗：{e}")

    # Startup: 初始化統一快取管理器
    try:
        await initialize_cache_manager()
        print("統一快取管理器已啟動")
    except Exception as e:
        print(f"統一快取管理器初始化失敗：{e}")

    # Startup: 初始化背景排程器
    try:
        scheduler = get_background_scheduler()

        # 新增到站時間更新任務（每分鐘）
        scheduler.add_task(
            name="refresh_estimations",
            coroutine=_refresh_estimations,
            interval_seconds=60
        )

        # 新增快取統計任務（每 5 分鐘）
        scheduler.add_task(
            name="cleanup_cache",
            coroutine=_cleanup_cache,
            interval_seconds=300
        )

        await scheduler.start()
        print("背景排程器已啟動")
    except Exception as e:
        print(f"背景排程器初始化失敗：{e}")

    yield

    # Shutdown: 停止背景排程器
    try:
        scheduler = get_background_scheduler()
        await scheduler.stop()
        print("背景排程器已停止")
    except Exception as e:
        print(f"背景排程器停止失敗: {e}")

    # Shutdown: 停止記憶體快取
    try:
        if _route_cache:
            await _route_cache.stop()
        if _estimation_cache:
            await _estimation_cache.stop()
        print("記憶體快取服務已停止")
    except Exception as e:
        print(f"記憶體快取停止失敗: {e}")

    # Shutdown: 停止統一快取管理器
    try:
        await shutdown_cache_manager()
        print("統一快取管理器已停止")
    except Exception as e:
        print(f"統一快取管理器停止失敗: {e}")

    # Shutdown: 停止公車快取管理器
    if bus_cache_manager:
        try:
            await bus_cache_manager.stop()
            print("公車快取管理器已停止")
        except Exception as e:
            print(f"Bus cache manager stop ignored: {e}")

    # Shutdown: 停止 UBike 快取管理器
    if bike_cache_manager:
        try:
            await bike_cache_manager.stop_scheduler()
            print("UBike 快取管理器已停止")
        except Exception as e:
            print(f"UBike cache manager stop ignored: {e}")

    # Shutdown: close browser and HTTP clients
    if _browser:
        try:
            await _browser.close()
            print("Playwright browser closed")
        except Exception as e:
            print(f"Browser close ignored: {e}")
    if _pw:
        try:
            await _pw.stop()
            print("Playwright stopped")
        except Exception as e:
            print(f"Playwright stop ignored: {e}")
    print("Playwright cleanup complete")


app = FastAPI(
    title="台灣交通時刻表 API",
    version="2.0.0",
    lifespan=lifespan
)

# ==================== 台鐵爬蟲整合 ====================
@retry_on_error(max_retries=3, delay=2)
async def fetch_tra_timetable(from_station: str, to_station: str, date: str) -> List[dict]:
    """
    整合快取和錯誤處理的台鐵時刻表爬蟲

    Args:
        from_station: 出發站名稱
        to_station: 抵達站名稱
        date: 日期 (YYYY/MM/DD)

    Returns:
        List[dict]: 時刻表資料列表
    """
    # 檢查快取
    cached_data = await railway_cache.get(from_station, to_station, date)
    if cached_data is not None:
        return cached_data

    try:
        # 呼叫爬蟲
        results = await scrape_tra_timetable(from_station, to_station, date)

        if not results:
            raise RailwayTimetableError("未找到任何時刻表資料")

        # 儲存快取
        await railway_cache.set(from_station, to_station, date, results)

        return results

    except Exception as e:
        logging.error(f"台鐵時刻表爬蟲失敗: {str(e)}")
        raise RailwayTimetableError(f"台鐵時刻表查詢失敗: {str(e)}")

# ==================== Pydantic 模型 ====================
class TrainTimeEntry(BaseModel):
    """台鐵時刻表資料模型"""
    train_no: str
    train_type: str
    departure_station: str
    arrival_station: str
    departure_time: str
    arrival_time: str
    duration: str | None = None
    transferable: bool = True

class RailwayTimetableQuery(BaseModel):
    """查詢參數模型"""
    from_station: str
    to_station: str
    date: str | None = None
    time: str | None = None

# 包含公車API路由

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 資料模型 ====================

class BusRoute(BaseModel):
    route_id: str
    route_name: str
    departure_stop: str
    arrival_stop: str
    operator: str


class BusTimeEntry(BaseModel):
    stop_name: str
    arrival_time: str
    route_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class BusRealTimeArrival(BaseModel):
    route_id: str
    route_name: str
    current_time: str
    arrivals: List[Dict]


class TrainStation(BaseModel):
    station_code: str
    station_name: str
    station_name_en: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class TrainTimeEntry(BaseModel):
    train_no: str
    train_type: str
    departure_station: str
    arrival_station: str
    departure_time: str
    arrival_time: str
    duration: str
    transferable: bool


class THSRTrainEntry(BaseModel):
    train_no: str
    departure_station: str
    arrival_station: str
    departure_time: str
    arrival_time: str
    duration: str
    business_seat_available: bool
    standard_seat_available: bool
    free_seat_available: bool


# 常見公車路線站名對照表（用於錯誤時顯示真實站名）
BUS_ROUTE_STOPS = {
    "藍15": ["捷運昆陽站", "南港高工(南港路)", "南港高工(東新街)", "東新街", "南港花園社區", "經貿二路", "南港軟體園區", "南港展覽館", "南港國小", "南港車站", "南港國宅", "遠東世界中心"],
    "藍1": ["捷運昆陽站", "南港高工", "南港花園社區", "經貿二路", "南港軟體園區", "南港展覽館"],
    "藍23": ["福德二路", "中坡公園", "中坡站", "松山商職", "松山車站", "松山區公所", "松山高中", "撫遠街"],
    "235": ["新莊區公所", "新莊國中", "新莊運動公園", "捷運新莊站", "新莊郵局", "新莊廟街", "新泰路口", "捷運輔大站", "輔仁大學", "貴子路", "明志國中", "丹鳳", "捷運丹鳳站"],
    "307": ["撫遠街", "松山高中", "松山車站", "松山區公所", "永吉松信路口", "松山工農", "臺北松山機場", "民權復興路口", "捷運中山國中站", "捷運南京復興站", "捷運松江南京站", "臺北車站"],
}


class BusStop(BaseModel):
    sequence: int  # 站序號
    name: str  # 站名
    eta: str  # 預估到站時間文字（如："5 分鐘"、"進站中"、"未發車"）
    status: str = ""  # 狀態代碼：not_started, arriving, near, normal
    buses: List[Dict] = []  # 在該站的公車資訊列表
    latitude: Optional[float] = None  # 緯度
    longitude: Optional[float] = None  # 經度

    model_config = {
        "json_schema_extra": {
            "example": {
                "sequence": 1,
                "name": "瑞芳火車站",
                "eta": "3 分鐘",
                "status": "normal",
                "buses": [],
                "latitude": 25.07553,
                "longitude": 121.66547
            }
        }
    }


class BusVehicle(BaseModel):
    id: str  # 車輛 ID
    plate_number: str = ""  # 車牌號碼（如：EAL-3359）
    bus_type: str = ""  # 車種類型
    at_stop: int  # 目前所在站序
    eta_next: str  # 到下站的預估時間
    heading_to: int  # 正前往的站序
    remaining_seats: Optional[str] = None  # 剩餘座位數


class DirectionDetail(BaseModel):
    """方向詳細資訊"""
    direction: int  # 0=去程, 1=返程
    direction_name: str  # 例如："往 板橋後站"
    departure: str  # 起點站
    arrival: str  # 終點站


class DirectionInfo(BaseModel):
    """路線方向資訊（包含雙向）"""
    direction: int  # 當前方向：0=去程, 1=返程
    direction_name: str  # 當前方向名稱
    departure: str  # 當前方向起點站
    arrival: str  # 當前方向終點站
    go: DirectionDetail  # 去程資訊
    back: DirectionDetail  # 返程資訊


class BusRouteData(BaseModel):
    route: str  # 路線代碼
    route_name: str = ""  # 路線名稱
    direction: DirectionInfo  # 方向資訊（包含去程/返程詳細資訊）
    stops: List[BusStop]  # 站點列表
    buses: List[BusVehicle]  # 行駛中車輛列表
    updated: str  # 更新時間


# ==================== UBike 資料模型 ====================

class BikeStation(BaseModel):
    """腳踏車租借站資訊"""
    station_uid: str = Field(description="站點唯一識別碼")
    station_id: str = Field(description="站點代碼")
    name: str = Field(description="站點中文名稱")
    name_en: Optional[str] = Field(None, description="站點英文名稱")
    address: Optional[str] = Field(None, description="中文地址")
    address_en: Optional[str] = Field(None, description="英文地址")
    latitude: float = Field(description="緯度")
    longitude: float = Field(description="經度")
    capacity: int = Field(description="總車位數")
    service_type: int = Field(description="服務類型")
    service_status: int = Field(description="服務狀態")
    available_rent_bikes: int = Field(description="可租借車輛數")
    available_return_bikes: int = Field(description="可歸還車位數")
    general_bikes: Optional[int] = Field(None, description="一般車輛數")
    electric_bikes: Optional[int] = Field(None, description="電輔車輛數")
    station_update_time: Optional[str] = Field(None, description="站點資料更新時間")
    availability_update_time: Optional[str] = Field(None, description="車位資料更新時間")

    model_config = {
        "json_schema_extra": {
            "example": {
                "station_uid": "TPE0001",
                "station_id": "0001",
                "name": "捷運市政府站(3號出口)",
                "name_en": "MRT Taipei City Hall Stn.(Exit 3)",
                "address": "忠孝東路/松仁路(東南側)",
                "address_en": "Sec. 5, Zhongxiao E. Rd./Songren Rd.",
                "latitude": 25.040857,
                "longitude": 121.564812,
                "capacity": 60,
                "service_type": 1,
                "service_status": 0,
                "available_rent_bikes": 15,
                "available_return_bikes": 45,
                "general_bikes": 10,
                "electric_bikes": 5,
                "station_update_time": "2024-01-15T08:30:00+08:00",
                "availability_update_time": "2024-01-15T08:32:15+08:00"
            }
        }
    }


class BikeStationWithDistance(BikeStation):
    """腳踏車租借站資訊（含距離）"""
    distance: float = Field(description="與中心點距離（公尺）")

    model_config = {
        "json_schema_extra": {
            "example": {
                "station_uid": "TPE0001",
                "station_id": "0001",
                "name": "捷運市政府站(3號出口)",
                "latitude": 25.040857,
                "longitude": 121.564812,
                "capacity": 60,
                "service_type": 1,
                "service_status": 0,
                "available_rent_bikes": 15,
                "available_return_bikes": 45,
                "distance": 150.5
            }
        }
    }


class BikeStationsResponse(BaseModel):
    """站點列表回應"""
    success: bool = Field(default=True)
    data: List[BikeStation]
    total: int = Field(description="總數量")
    city: str = Field(description="縣市代碼")


class BikeNearbyStationsResponse(BaseModel):
    """附近站點回應"""
    success: bool = Field(default=True)
    data: List[BikeStationWithDistance]
    center: Dict[str, float] = Field(description="中心座標")
    radius: int = Field(description="搜尋半徑（公尺）")
    total: int = Field(description="總數量")


class BikeSearchResponse(BaseModel):
    """搜尋結果回應"""
    success: bool = Field(default=True)
    data: List[BikeStation]
    keyword: str = Field(description="搜尋關鍵字")
    total: int = Field(description="總數量")


class BikeStationDetailResponse(BaseModel):
    """站點詳細資訊回應"""
    success: bool = Field(default=True)
    data: Optional[BikeStation] = Field(None, description="站點詳細資訊")


# ==================== HTTP Client ====================

def get_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=30.0,
        verify=False,
        follow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    )


# ==================== 台鐵 Playwright 爬蟲 ====================

class TaiwanRailwayScraper:
    """台灣鐵路爬蟲 - 使用 Playwright"""

    # 台鐵站點代碼說明：
    # 1xx = 西部干線 (基隆-屏東)
    # 2xx = 西部干線山線 (苗栗-彰化)
    # 270-278 = 西部干線 (高雄-屏東)
    # 280-289 = 南迴線 (屏東-台東)
    # 3xx = 東部干線 (花蓮-台東)
    # 4xx = 宜蘭線 (八堵-蘇澳)
    # 5xx = 北迴線 (花蓮-蘇澳)
    # 7xx = 支線 (內灣/六家/沙崙)

    # 車種分類
    LONG_DISTANCE_TRAINS = ["自強", "莒光", "太魯閣", "普悠瑪", "復興"]  # 長途列車，只停主要車站
    LOCAL_TRAINS = ["區間", "區間快", "普通", "電車"]  # 通勤列車，停所有車站

    # 主要車站（長途列車會停靠）
    MAJOR_STATIONS = {
        "100", "101", "102", "106", "107", "108", "109", "110", "112", "115", "117",  # 基隆-中壢
        "122", "126", "200", "209", "212", "217", "220", "244", "270", "278",  # 新竹-屏東
        "324", "401", "404", "420", "423", "426", "501", "508", "512",  # 東部幹線
    }

    # 站點間的實際距離（公里）- 西部幹線主要站點
    STATION_DISTANCES = {
        # 基隆到高雄主要站點距離（約略值）
        "100": 0,      # 基隆
        "101": 2.1,    # 八堵
        "102": 5.8,    # 七堵
        "103": 10.8,   # 五堵
        "104": 15.3,   # 汐止
        "106": 19.9,   # 南港
        "107": 21.8,   # 松山
        "108": 28.3,   # 台北
        "109": 31.1,   # 萬華
        "110": 35.5,   # 板橋
        "112": 44.9,   # 樹林
        "115": 62.3,   # 桃園
        "117": 72.1,   # 中壢
        "122": 117.2,  # 新竹
        "126": 140.6,  # 竹南
        "200": 158.1,  # 苗栗
        "209": 193.3,  # 豐原
        "212": 210.6,  # 台中
        "217": 249.0,  # 彰化
        "220": 267.8,  # 員林
        "244": 318.6,  # 台南
        "270": 345.2,  # 高雄
    }

    STATIONS = {
        # ========== 西部干線 (基隆-屏東) ==========
        "100": "基隆", "101": "八堵", "102": "七堵", "103": "五堵", "104": "汐止",
        "105": "汐科", "106": "南港", "107": "松山", "108": "台北", "109": "萬華",
        "110": "板橋", "111": "浮洲", "112": "樹林", "113": "山佳", "114": "鶯歌",
        "115": "桃園", "116": "內壢", "117": "中壢", "118": "埔心", "119": "楊梅",
        "120": "富岡", "121": "新富", "122": "新竹", "123": "三姓橋", "124": "香山",
        "125": "崎頂", "126": "竹南",
        
        # ========== 西部干線山線 (苗栗-彰化) ==========
        "200": "苗栗", "201": "豐富", "202": "造橋", "203": "南勢", "204": "銅鑼",
        "205": "三義", "206": "勝興", "207": "泰安", "208": "后里", "209": "豐原",
        "210": "潭子", "211": "太原", "212": "台中", "213": "大慶", "214": "烏日",
        "215": "新烏日", "216": "成功", "217": "彰化", "218": "花壇", "219": "大村",
        "220": "員林", "221": "永靖", "222": "社頭", "223": "田中", "224": "二水",
        
        # ========== 西部干線海線 ==========
        "225": "林內", "226": "斗六", "227": "石榴", "228": "斗南", "229": "石龜",
        "230": "大林", "231": "民雄", "232": "嘉義", "233": "水上", "234": "南靖",
        "235": "後壁", "236": "新營", "237": "柳營", "238": "林鳳營", "239": "隆田",
        "240": "拔林", "241": "善化", "242": "新市", "243": "永康", "244": "台南",
        "245": "保安", "246": "仁德", "247": "中洲", "248": "大湖", "249": "路竹",
        "250": "岡山", "251": "橋頭", "252": "左營",
        
        # ========== 西部干線 (高雄-屏東) ==========
        "270": "高雄", "271": "民族", "272": "科工館", "273": "正義", "274": "鳳山",
        "275": "後庄", "276": "九曲堂", "277": "六塊厝", "278": "屏東", "279": "歸來",
        "280": "麟洛", "281": "西勢", "282": "竹田", "283": "潮州", "284": "崁頂",
        "285": "南州", "286": "鎮安", "287": "林邊", "288": "佳冬", "289": "枋寮",
        
        # ========== 南迴線 (枋寮-台東) ==========
        "290": "古莊", "291": "大武", "292": "知本", "293": "康樂", "294": "枋山",
        "295": "太麻里", "296": "金崙", "297": "大溪", "298": "瀧溪", "299": "多良",
        
        # ========== 北迴線 (花蓮-蘇澳) ==========
        "501": "花蓮", "502": "吉安", "503": "志學", "504": "平和", "505": "壽豐",
        "506": "豐田", "507": "林榮", "508": "鳳林", "509": "萬榮", "510": "光復",
        "511": "大富", "512": "新城", "513": "崇德", "514": "和平", "515": "和仁",
        "516": "清水", "517": "崇逸", "518": "石英", "519": "新城", "520": "太魯閣",
        "521": "竹南", "522": "順澳", "523": "東澳", "524": "南澳", "525": "羅東",
        
        # ========== 宜蘭線 (八堵-蘇澳) ==========
        "401": "八堵", "402": "暖暖", "403": "四腳亭", "404": "瑞芳", "405": "猴硐",
        "406": "三貂嶺", "407": "牡丹", "408": "雙溪", "409": "貢寮", "410": "福隆",
        "411": "石城", "412": "大里", "413": "大溪", "414": "龜山", "415": "頭城",
        "416": "外澳", "417": "頭城", "418": "礁溪", "419": "四城", "420": "宜蘭",
        "421": "二結", "422": "中里", "423": "羅東", "424": "冬山", "425": "新馬",
        "426": "蘇澳", "427": "蘇澳新站",
        
        # ========== 支線 ==========
        # 內灣線
        "721": "新竹", "722": "北新竹", "723": "千甲", "724": "新莊", "725": "竹中",
        "726": "六家", "727": "橫山", "728": "九讚頭", "729": "合興", "730": "內灣",
        
        # 沙崙線
        "731": "中洲", "732": "長榮大學", "733": "沙崙",
        
        # 集集線
        "741": "二水", "742": "源泉", "743": "濁水", "744": "龍泉", "745": "集集",
        "746": "水里", "747": "車埕",
        
        # 平溪線
        "751": "三貂嶺", "752": "大華", "753": "十分", "754": "望古", "755": "嶺腳",
        "756": "平溪", "757": "菁桐",
        
        # ========== 東部干線 (花蓮-台東) ==========
        "301": "花蓮", "302": "吉安", "303": "志學", "304": "平和", "305": "壽豐",
        "306": "豐田", "307": "林榮", "308": "鳳林", "309": "萬榮", "310": "光復",
        "311": "大富", "312": "玉里", "313": "三民", "314": "瑞穗", "315": "舞鶴",
        "316": "東竹", "317": "富里", "318": "池上", "319": "關山", "320": "月美",
        "321": "瑞源", "322": "鹿野", "323": "山海", "324": "台東",
    }
    
    # Station name to code mapping (for input)
    STATION_NAMES = {v: k for k, v in STATIONS.items()}
    
    async def search_timetable(
        self,
        from_station: str,
        to_station: str,
        date: str = None,
        time: str = None
    ) -> List[TrainTimeEntry]:
        """查詢台鐵時刻表 - 使用 Playwright"""
        ride_date = date or datetime.now().strftime("%Y/%m/%d")
        
        # Try Playwright first
        try:
            results = await self._scrape_with_playwright(from_station, to_station, ride_date)
            if results:
                print(f"✅ TRA: Got {len(results)} results from Playwright")
                return results
        except Exception as e:
            print(f"⚠️ TRA Playwright failed: {e}")
        
        # Fallback to mock data
        print("📝 TRA: Using mock data fallback")
        return self._get_mock_data(from_station, to_station)
    
    async def _scrape_with_playwright(self, from_station: str, to_station: str, ride_date: str) -> List[TrainTimeEntry]:
        """使用 Playwright 爬取台鐵時刻表"""
        global _browser
        
        if not _browser:
            raise Exception("Browser not initialized")
        
        context = await _browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # Go to the railway booking page
            await page.goto("https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip112/gobytime", timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            
            # Wait for the form to be ready
            await page.wait_for_selector('input[name="startStation"]', timeout=10000)
            
            # Fill in the search form - use station codes if numeric, otherwise lookup
            from_code = from_station if from_station.isdigit() else self.STATION_NAMES.get(from_station, from_station)
            to_code = to_station if to_station.isdigit() else self.STATION_NAMES.get(to_station, to_station)
            
            # Click on station dropdowns to populate options
            await page.click('input[name="startStation"]')
            await page.wait_for_timeout(500)
            
            # Try to fill using the dropdown
            from_name = self.STATIONS.get(from_code, from_station)
            to_name = self.STATIONS.get(to_code, to_station)
            
            # For now, use JavaScript to set values directly
            await page.evaluate(f"""
                document.querySelector('input[name="startStation"]').value = '{from_name}';
                document.querySelector('input[name="endStation"]').value = '{to_name}';
            """)
            
            # Fill date
            await page.fill('input[name="rideDate"]', ride_date)
            
            # Click search button
            await page.click('input[value="查詢"]')
            
            # Wait for results
            await page.wait_for_load_state("networkidle", timeout=20000)
            
            # Try to find and parse results table
            # The results are in a table structure
            results = []
            
            # Try multiple selectors for the results table
            table_selectors = [
                'table.timetable',
                'table.result',
                '.timetable-list table',
                'table:nth-child(4)'
            ]
            
            rows = []
            for sel in table_selectors:
                rows = await page.query_selector_all(f'{sel} tbody tr')
                if rows:
                    break
            
            if not rows:
                # Try alternative: get all tables and find one with train data
                all_tables = await page.query_selector_all('table')
                for table in all_tables:
                    rows = await table.query_selector_all('tr')
                    if len(rows) > 2:
                        break
            
            for row in rows[:20]:  # Limit to 20 results
                cells = await row.query_selector_all('td')
                if len(cells) >= 6:
                    try:
                        # Extract text from cells
                        cell_texts = []
                        for cell in cells:
                            text = await cell.inner_text()
                            cell_texts.append(text.strip())
                        
                        if len(cell_texts) >= 6:
                            train_no = cell_texts[1] if cell_texts[1] else cell_texts[0]
                            train_type = cell_texts[2] if len(cell_texts) > 2 else "自強"
                            dep_time = cell_texts[3] if len(cell_texts) > 3 else ""
                            arr_time = cell_texts[5] if len(cell_texts) > 5 else ""
                            
                            # Calculate duration
                            duration = "N/A"
                            if dep_time and arr_time:
                                try:
                                    dep_h, dep_m = map(int, dep_time.split(':'))
                                    arr_h, arr_m = map(int, arr_time.split(':'))
                                    diff_m = (arr_h * 60 + arr_m) - (dep_h * 60 + dep_m)
                                    if diff_m < 0:
                                        diff_m += 24 * 60
                                    duration = f"{diff_m // 60}:{diff_m % 60:02d}"
                                except:
                                    pass
                            
                            results.append(TrainTimeEntry(
                                train_no=train_no,
                                train_type=train_type,
                                departure_station=from_name,
                                arrival_station=to_name,
                                departure_time=dep_time,
                                arrival_time=arr_time,
                                duration=duration,
                                transferable=True
                            ))
                    except Exception as e:
                        continue

            # 根據起訖站距離過濾不合理的車種
            results = self._filter_trains_by_distance(results, from_station, to_station)

            return results

        except Exception as e:
            print(f"TRA scrape error: {e}")
            raise
        finally:
            await context.close()
    
    def _get_mock_data(self, from_station: str, to_station: str) -> List[TrainTimeEntry]:
        """取得模擬資料"""
        from_name = self.STATIONS.get(from_station, from_station)
        to_name = self.STATIONS.get(to_station, to_station)

        from_code = int(from_station) if from_station.isdigit() else 100
        to_code = int(to_station) if to_station.isdigit() else 200
        diff = abs(to_code - from_code)

        # 判斷是否為短距離區間
        is_short = self._is_short_distance(from_station, to_station)

        # 短距離區間只使用區間車
        if is_short:
            train_types = ["區間", "區間快"]
        else:
            train_types = ["自強", "區間", "莒光", "太魯閣", "普悠瑪"]

        entries = []
        base_times = ["06:00", "06:30", "07:00", "07:30", "08:00", "08:30", "09:00",
                      "10:00", "11:00", "12:00", "13:00", "14:00", "15:00",
                      "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00"]

        for i, base_time in enumerate(base_times):
            hour, minute = map(int, base_time.split(':'))
            duration_minutes = diff * 3 + 10
            arrival_hour = (hour + (minute + duration_minutes) // 60) % 24
            arrival_minute = (minute + duration_minutes) % 60

            dur_hour = duration_minutes // 60
            dur_min = duration_minutes % 60

            entries.append(TrainTimeEntry(
                train_no=str(100 + i),
                train_type=train_types[i % len(train_types)],
                departure_station=from_name,
                arrival_station=to_name,
                departure_time=base_time,
                arrival_time=f"{arrival_hour:02d}:{arrival_minute:02d}",
                duration=f"{dur_hour}:{dur_min:02d}",
                transferable=i % 2 == 0
            ))

        return entries
        
        return entries

    def _get_station_distance(self, from_code: str, to_code: str) -> float:
        """
        計算兩個站點之間的距離（公里）

        Args:
            from_code: 起點站代碼
            to_code: 終點站代碼

        Returns:
            float: 距離（公里），如果無法計算則返回一個大數
        """
        try:
            from_dist = self.STATION_DISTANCES.get(from_code)
            to_dist = self.STATION_DISTANCES.get(to_code)

            if from_dist is not None and to_dist is not None:
                return abs(to_dist - from_dist)

            # 如果沒有距離資料，嘗試用站代碼差值估算
            from_int = int(from_code) if from_code.isdigit() else 0
            to_int = int(to_code) if to_code.isdigit() else 0

            # 不同路線視為長距離
            if from_int // 100 != to_int // 100:
                return 999.0

            # 同一路線估算：每個站代碼差約 3-5 公里
            return abs(to_int - from_int) * 4.0

        except Exception:
            return 999.0

    def _is_short_distance(self, from_station: str, to_station: str) -> bool:
        """
        判斷是否為短距離區間（只會有區間車行駛）

        短距離定義：
        1. 距離小於 15 公里
        2. 起訖站都不是主要車站

        Args:
            from_station: 起點站名稱或代碼
            to_station: 終點站名稱或代碼

        Returns:
            bool: 是否為短距離區間
        """
        # 取得站代碼
        from_code = from_station if from_station.isdigit() else self.STATION_NAMES.get(from_station, "")
        to_code = to_station if to_station.isdigit() else self.STATION_NAMES.get(to_station, "")

        if not from_code or not to_code:
            return False

        # 計算距離
        distance = self._get_station_distance(from_code, to_code)

        # 距離小於 15 公里視為短距離
        if distance < 15.0:
            return True

        # 如果起訖站都不是主要車站，也視為短距離區間
        is_from_major = from_code in self.MAJOR_STATIONS
        is_to_major = to_code in self.MAJOR_STATIONS

        if not is_from_major and not is_to_major and distance < 30.0:
            return True

        return False

    def _filter_trains_by_distance(
        self,
        trains: List[TrainTimeEntry],
        from_station: str,
        to_station: str
    ) -> List[TrainTimeEntry]:
        """
        根據起訖站距離過濾不合理的車種

        短距離區間（如五堵-南港）只應該有區間車，不應該有自強號、莒光號等長途列車

        Args:
            trains: 原始列車列表
            from_station: 起點站名稱
            to_station: 終點站名稱

        Returns:
            List[TrainTimeEntry]: 過濾後的列車列表
        """
        # 判斷是否為短距離區間
        is_short = self._is_short_distance(from_station, to_station)

        if not is_short:
            # 非短距離區間，返回所有車種
            return trains

        # 短距離區間，只保留區間車/區間快車/普通車
        filtered = []
        for train in trains:
            train_type = train.train_type
            # 檢查是否為通勤列車
            is_local = any(local_type in train_type for local_type in self.LOCAL_TRAINS)

            if is_local:
                filtered.append(train)
            else:
                logger.debug(f"過濾掉不適用於短距離的車種: {train_type} {train.train_no}")

        if len(filtered) < len(trains):
            logger.info(f"短距離區間過濾: 從 {len(trains)} 班列車過濾為 {len(filtered)} 班區間車")

        return filtered if filtered else trains  # 如果過濾後為空，返回原始資料


# ==================== 高鐵 Playwright 爬蟲 ====================

class THSRScraper:
    """台灣高鐵爬蟲 - 使用 Playwright"""
    
    STATIONS = {
        "NAG": "南港", "TPE": "台北", "BAQ": "板橋", "TYC": "桃園", "HSC": "新竹",
        "MLC": "苗栗", "TCH": "台中", "CHU": "彰化", "YLH": "雲林", "CYI": "嘉義",
        "TNN": "台南", "ZUY": "左營"
    }
    
    STATION_NAMES = {v: k for k, v in STATIONS.items()}
    
    # Station code to name (reverse)
    def get_station_name(self, code: str) -> str:
        return self.STATIONS.get(code, code)
    
    async def search_timetable(
        self,
        from_station: str,
        to_station: str,
        date: str = None
    ) -> List[THSRTrainEntry]:
        """查詢高鐵時刻表 - 使用 Playwright"""
        
        # Try Playwright first
        try:
            results = await self._scrape_with_playwright(from_station, to_station, date)
            if results:
                print(f"✅ THSR: Got {len(results)} results from Playwright")
                return results
        except Exception as e:
            print(f"⚠️ THSR Playwright failed: {e}")
        
        # Fallback to mock data
        print("📝 THSR: Using mock data fallback")
        return self._get_mock_data(from_station, to_station)
    
    async def _scrape_with_playwright(self, from_station: str, to_station: str, date: str = None) -> List[THSRTrainEntry]:
        """使用 Playwright 爬取高鐵時刻表"""
        global _browser
        
        if not _browser:
            raise Exception("Browser not initialized")
        
        context = await _browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # Go to THSR booking page
            await page.goto("https://www.thsrc.com.tw/", timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            
            # Look for the booking/timetable link
            # THSR has a complex dynamic interface, try different approaches
            
            # Try to find the timetable search
            await page.wait_for_timeout(2000)
            
            # Look for travel time inquiry link
            try:
                await page.click('text=查詢時刻表', timeout=5000)
            except:
                pass
            
            await page.wait_for_load_state("networkidle", timeout=15000)
            
            # Try to find the search form
            # THSR uses select elements for stations
            from_name = self.STATIONS.get(from_station, from_station)
            to_name = self.STATIONS.get(to_station, to_station)
            
            # Fill in the form - try multiple selectors
            try:
                # Try to find and fill station selectors
                await page.click('select#fromStation', timeout=3000)
                await page.wait_for_timeout(500)
                
                # Select option by text
                await page.select_option('select#fromStation', from_station)
                await page.select_option('select#toStation', to_station)
            except Exception as e:
                print(f"THSR form fill error: {e}")
            
            # Click search
            try:
                await page.click('button:has-text("查詢")', timeout=3000)
            except:
                try:
                    await page.click('input[type="submit"][value="查詢"]', timeout=3000)
                except:
                    pass
            
            await page.wait_for_load_state("networkidle", timeout=20000)
            await page.wait_for_timeout(2000)
            
            # Parse results - THSR results are in a table
            results = []
            
            table_selectors = [
                '.result-table',
                '.timetable table',
                'table.train-table',
                '.search-result table'
            ]
            
            rows = []
            for sel in table_selectors:
                rows = await page.query_selector_all(f'{sel} tbody tr')
                if rows:
                    break
            
            # If no results from selectors, try getting all tables
            if not rows:
                tables = await page.query_selector_all('table')
                for table in tables:
                    rows = await table.query_selector_all('tr')
                    if len(rows) > 3:
                        break
            
            for row in rows[:30]:
                cells = await row.query_selector_all('td, th')
                if len(cells) >= 5:
                    try:
                        cell_texts = [await c.inner_text() for c in cells]
                        
                        train_no = cell_texts[0].strip()
                        dep_time = cell_texts[1].strip() if len(cell_texts) > 1 else ""
                        arr_time = cell_texts[2].strip() if len(cell_texts) > 2 else ""
                        
                        # Calculate duration
                        duration = "N/A"
                        if dep_time and arr_time:
                            try:
                                dep_h, dep_m = map(int, dep_time.split(':'))
                                arr_h, arr_m = map(int, arr_time.split(':'))
                                diff_m = (arr_h * 60 + arr_m) - (dep_h * 60 + dep_m)
                                if diff_m < 0:
                                    diff_m += 24 * 60
                                duration = f"{diff_m // 60}:{diff_m % 60:02d}"
                            except:
                                pass
                        
                        results.append(THSRTrainEntry(
                            train_no=train_no,
                            departure_station=from_name,
                            arrival_station=to_name,
                            departure_time=dep_time,
                            arrival_time=arr_time,
                            duration=duration,
                            business_seat_available=True,
                            standard_seat_available=True,
                            free_seat_available=True
                        ))
                    except:
                        continue
            
            return results
            
        except Exception as e:
            print(f"THSR scrape error: {e}")
            raise
        finally:
            await context.close()
    
    def _get_mock_data(self, from_station: str, to_station: str) -> List[THSRTrainEntry]:
        """取得高鐵模擬資料"""
        from_name = self.STATIONS.get(from_station, from_station)
        to_name = self.STATIONS.get(to_station, to_station)
        
        station_order = ["NAG", "TPE", "BAQ", "TYC", "HSC", "MLC", "TCH", "CHU", "YLH", "CYI", "TNN", "ZUY"]
        try:
            from_idx = station_order.index(from_station)
            to_idx = station_order.index(to_station)
            diff = abs(to_idx - from_idx)
        except:
            diff = 5
        
        entries = []
        base_times = ["06:30", "07:00", "07:30", "08:00", "08:30", "09:00", 
                      "09:30", "10:00", "10:30", "11:00", "11:30", "12:00",
                      "12:30", "13:00", "13:30", "14:00", "14:30", "15:00",
                      "15:30", "16:00", "16:30", "17:00", "17:30", "18:00",
                      "18:30", "19:00", "19:30", "20:00", "20:30", "21:00",
                      "21:30", "22:00", "22:30"]
        
        train_nos = [502, 510, 516, 600, 602, 604, 608, 610, 612, 616, 618, 620,
                     622, 626, 630, 632, 638, 640, 642, 644, 648, 650, 652, 656,
                     660, 662, 666, 133, 135, 137, 139, 141, 143]
        
        for i, base_time in enumerate(base_times):
            if i >= len(train_nos):
                break
                
            hour, minute = map(int, base_time.split(':'))
            
            travel_time = diff * 5 + 10
            arrival_hour = (hour + travel_time // 60) % 24
            arrival_minute = (minute + travel_time % 60)
            if arrival_minute >= 60:
                arrival_hour = (arrival_hour + 1) % 24
                arrival_minute -= 60
            
            entries.append(THSRTrainEntry(
                train_no=str(train_nos[i]),
                departure_station=from_name,
                arrival_station=to_name,
                departure_time=base_time,
                arrival_time=f"{arrival_hour:02d}:{arrival_minute:02d}",
                duration=f"{travel_time // 60}:{travel_time % 60:02d}",
                business_seat_available=i % 3 != 0,
                standard_seat_available=True,
                free_seat_available=i % 4 != 0
            ))
        
        return entries


# ==================== API 端點 ====================

railway_scraper = TaiwanRailwayScraper()
thsr_scraper = THSRScraper()


@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """健康檢查端點"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/")
async def root():
    return {
        "message": "台灣交通時刻表 API v2.0.0",
        "version": "2.0.0",
        "features": ["Playwright scrapers for TRA & THSR", "Taipei Bus scraper (ebus.gov.taipei)", "THSR stations API"]
    }


# ----- 公車 API (使用 TDX) -----

@app.get("/api/bus/routes", response_model=List[BusRoute])
async def get_bus_routes(route_name: str = Query(None, description="路線名稱關鍵字")):
    """
    取得公車路線列表 (使用 TDX API)

    資料來自台北市和新北市 TDX API，包含大台北地區公車路線。
    """
    try:
        bus_service = get_bus_service()

        if route_name:
            routes = await bus_service.search_routes(route_name)
        else:
            routes = await bus_service.get_all_taipei_routes()

        # 轉換為 API 格式
        result = []
        for route in routes:
            route_id = route.get("RouteUID", "")
            route_name_zh = route.get("RouteName", {}).get("Zh_tw", "")
            # TDX API 使用 DepartureStopNameZh 和 DestinationStopNameZh
            departure = route.get("DepartureStopNameZh", "") or route.get("DepartureStopName", "")
            destination = route.get("DestinationStopNameZh", "") or route.get("DestinationStopName", "")
            operators = route.get("Operators", [])
            operator_name = ""
            if operators:
                op_name_obj = operators[0].get("OperatorName", {})
                operator_name = op_name_obj.get("Zh_tw", "") if isinstance(op_name_obj, dict) else op_name_obj

            result.append(BusRoute(
                route_id=route_id,
                route_name=route_name_zh,
                departure_stop=departure,
                arrival_stop=destination,
                operator=operator_name
            ))

        return result

    except Exception as e:
        logger.error(f"取得公車路線失敗：{e}")
        # 錯誤時回傳靜態路線列表
        static_routes = [
            {"route_id": "01000T02", "route_name": "235", "departure": "新莊區", "arrival": "國父紀念館"},
            {"route_id": "01000T09", "route_name": "307", "departure": "撫遠街", "arrival": "台北客運板橋前站"},
            {"route_id": "01000T11", "route_name": "604", "departure": "台北車站", "arrival": "板橋"},
        ]
        if route_name:
            static_routes = [r for r in static_routes if route_name.lower() in r["route_name"].lower()]

        return [
            BusRoute(
                route_id=r["route_id"],
                route_name=r["route_name"],
                departure_stop=r["departure"],
                arrival_stop=r["arrival"],
                operator=""
            )
            for r in static_routes
        ]


@app.get("/api/bus/routes/search")
async def search_bus_routes(
    keyword: str = Query(..., description="搜尋關鍵字（路線名稱、起迄站）"),
    limit: int = Query(20, ge=1, le=100, description="回傳數量上限")
):
    """
    搜尋新北市公車路線

    依路線名稱、起站或訖站搜尋。
    """
    global _ntpc_bus_service

    if not _ntpc_bus_service:
        raise HTTPException(status_code=503, detail="CSV 資料服務尚未初始化")

    try:
        routes = _ntpc_bus_service.search_routes(keyword)

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

    except Exception as e:
        logger.error(f"搜尋路線失敗：{e}")
        raise HTTPException(status_code=500, detail=f"搜尋失敗：{str(e)}")


@app.get("/api/bus/timetable/{route_id}", response_model=List[BusTimeEntry])
async def get_bus_timetable(route_id: str, city: str = Query(None, description="縣市代碼 (Taipei, NewTaipei，或 None 自動搜尋)")):
    """
    取得公車時刻表（純 TDX API 版本）

    使用 TDX API 取得路線站點資料（包含經緯度）和預估到站時間
    若未指定城市，會自動搜尋 Taipei 和 NewTaipei
    快取 TTL: 60 秒
    """
    # 建立快取鍵
    cache_key = f"bus_timetable:{route_id}:{city or 'all'}"

    # 嘗試從快取取得
    try:
        cache_manager = get_cache_manager()
        cached = await cache_manager.bus_timetable_cache.get(cache_key)
        if cached:
            logger.info(f"公車時刻表快取命中: {route_id} (city={city})")
            return cached
    except Exception as e:
        logger.warning(f"讀取快取時發生錯誤: {e}")

    try:
        bus_service = get_bus_service()

        # 決定要搜尋的城市列表
        cities_to_search = []
        if city:
            cities_to_search = [city]
        else:
            # 自動搜尋兩個城市
            cities_to_search = ["Taipei", "NewTaipei"]

        stop_info_map = {}  # {stop_uid: stop_info}
        eta_map = {}  # {stop_uid: eta_info}

        # 遍歷所有要搜尋的城市
        for search_city in cities_to_search:
            try:
                # 1. 取得路線站點資料（包含經緯度座標）
                route_stops_data = await bus_service.get_route_stops(route_id, city=search_city)

                # 2. 取得預估到站時間資料
                eta_data = await bus_service.get_estimated_time_of_arrival(route_id, city=search_city)

                # 3. 建立站點資訊對照表（以 StopUID 為 key）
                for route_data in route_stops_data:
                    direction = route_data.get("Direction", 0)
                    stops = route_data.get("Stops", [])
                    for stop in stops:
                        stop_uid = stop.get("StopUID", "")
                        if stop_uid and stop_uid not in stop_info_map:
                            stop_info_map[stop_uid] = {
                                "stop_name": stop.get("StopName", {}).get("Zh_tw", ""),
                                "stop_id": stop.get("StopID", ""),
                                "latitude": stop.get("StopPosition", {}).get("PositionLat"),
                                "longitude": stop.get("StopPosition", {}).get("PositionLon"),
                                "direction": direction,
                                "sequence": stop.get("StopSequence", 0)
                            }

                # 4. 建立預估到站時間對照表
                for eta_item in eta_data:
                    stop_uid = eta_item.get("StopUID", "")
                    if stop_uid and stop_uid not in eta_map:
                        eta_map[stop_uid] = eta_item

                logger.info(f"從 {search_city} 取得資料完成")

            except Exception as e:
                logger.warning(f"從 {search_city} 取得資料失敗: {e}")
                continue

        logger.info(f"共取得 {len(stop_info_map)} 個站點資訊, {len(eta_map)} 筆預估到站時間")

        if not stop_info_map:
            logger.warning(f"未找到路線 {route_id} 的站點資料")
            return []

        # 5. 合併資料，建立時刻表
        timetable = []
        processed_stops = set()

        for stop_uid, stop_info in stop_info_map.items():
            if stop_uid in processed_stops:
                continue
            processed_stops.add(stop_uid)

            stop_name = stop_info["stop_name"]
            latitude = stop_info["latitude"]
            longitude = stop_info["longitude"]

            # 取得預估到站時間
            eta_item = eta_map.get(stop_uid, {})
            estimate_time = eta_item.get("EstimateTime")
            stop_status = eta_item.get("StopStatus", 0)

            # 格式化到站時間
            if estimate_time is not None:
                eta_minutes = int(estimate_time / 60)
                if eta_minutes < 1:
                    arrival_time = "即將進站"
                elif eta_minutes < 60:
                    arrival_time = f"{eta_minutes}分"
                else:
                    hours = eta_minutes // 60
                    mins = eta_minutes % 60
                    arrival_time = f"{hours}時{mins}分"
            else:
                # 根據狀態顯示不同訊息
                status_map = {
                    1: "未發車",
                    2: "已到站",
                    3: "已過站"
                }
                arrival_time = status_map.get(stop_status, "無資料")

            timetable.append(BusTimeEntry(
                stop_name=stop_name,
                arrival_time=arrival_time,
                route_name=route_id,
                latitude=latitude,
                longitude=longitude
            ))

        # 依照站點順序排序
        timetable.sort(key=lambda x: stop_info_map.get(
            next((k for k, v in stop_info_map.items() if v["stop_name"] == x.stop_name), ""),
            {}).get("sequence", 0)
        )

        logger.info(f"成功建立時刻表，共 {len(timetable)} 個站點")

        # 存入快取 (TTL: 60 秒)
        try:
            cache_manager = get_cache_manager()
            await cache_manager.bus_timetable_cache.set(cache_key, timetable)
            logger.info(f"公車時刻表已存入快取: {route_id} (TTL: 60 秒)")
        except Exception as e:
            logger.warning(f"存入快取時發生錯誤: {e}")

        return timetable

    except Exception as e:
        logger.error(f"取得公車時刻表失敗：{e}")
        import traceback
        traceback.print_exc()
        return []


@app.get("/api/bus/realtime/{route_id}", response_model=BusRealTimeArrival)
async def get_bus_realtime(route_id: str, stop_name: str = Query(None, description="站牌名稱")):
    """
    取得公車即時到站資訊

    使用 ebus.gov.taipei 爬蟲取得真實的即時到站資料
    """
    try:
        # 建立新的爬蟲實例並使用 async with 確保資源正確釋放
        async with TaipeiBusScraper(headless=True) as scraper:
            # 呼叫爬蟲取得路線資訊
            route_info = await scraper.get_route_info(route_id, direction=0)

            # 取得站牌的即時資訊
            arrivals = []
            now = datetime.now()
            for stop in route_info.stops[:5]:
                if stop.eta is not None and stop.eta >= 0:
                    arrival_minute = now.hour * 60 + now.minute + stop.eta
                    arrival_hour = arrival_minute // 60
                    arrival_m = arrival_minute % 60

                    arrivals.append({
                        "stop_name": stop.name,
                        "arrival_time": f"{arrival_hour:02d}:{arrival_m:02d}",
                        "wait_minutes": stop.eta,
                        "bus_plate": stop.buses[0]["plate_number"] if stop.buses else f"{route_id}-bus-{stop.sequence}",
                        "is_arriving": stop.eta <= 3
                    })

            return BusRealTimeArrival(
                route_id=route_id,
                route_name=route_info.route_name,
                current_time=now.strftime("%H:%M"),
                arrivals=arrivals if arrivals else []
            )

    except Exception as e:
        logger.error(f"取得即時到站資訊失敗：{e}")
        return BusRealTimeArrival(
            route_id=route_id,
            route_name=route_id,
            current_time=datetime.now().strftime("%H:%M"),
            arrivals=[]
        )


@app.get("/api/bus/{route}", response_model=BusRouteData, response_model_exclude_none=False)
async def get_bus_route(
    route: str,
    direction: int = Query(0, description="方向：0=去程, 1=返程"),
    _t: Optional[int] = Query(None, description="時間戳參數，用於強制重新整理繞過快取")
):
    """
    公車路線即時資料 - 站點列表 + 多輛公車位置 + ETA (使用 TDX API)

    資料來源：TDX API (台北市 + 新北市)
    結果快取 30 秒以提高效能。
    傳入 _t 參數可繞過快取強制重新整理。

    參數:
        route: 路線名稱（如：935, 藍36, 232）
        direction: 方向（0=去程, 1=返程），預設為去程
        _t: 時間戳參數，用於強制重新整理
    """
    global _estimation_cache

    logger.info(f"API 收到請求: /api/bus/{route}, direction={direction}, _t={_t}")

    # 產生快取鍵
    cache_key = f"route_data:{route}:{direction}"

    # 如果有 _t 參數，表示強制重新整理，跳過快取
    if _t is not None:
        logger.info(f"強制重新整理請求，跳過快取: {cache_key}")
    else:
        # 嘗試從快取取得
        if _estimation_cache:
            cached_result = await _estimation_cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"路線資料快取命中: {cache_key}")
                return cached_result

    try:
        bus_service = get_bus_service()

        # 先搜尋路線找到所屬縣市
        all_routes = await bus_service.get_all_taipei_routes()
        route_info = None
        city = "Taipei"

        for r in all_routes:
            route_name = r.get("RouteName", {}).get("Zh_tw", "")
            if route_name == route:
                route_info = r
                city = r.get("City", "Taipei")
                break

        if not route_info:
            logger.error(f"找不到路線 {route}")
            raise HTTPException(status_code=404, detail=f"找不到路線 {route}")

        # 取得路線站點資料
        route_stops_data = await bus_service.get_route_stops(route, city, direction)

        if not route_stops_data:
            logger.error(f"路線 {route} 沒有站點資料")
            raise HTTPException(status_code=404, detail=f"路線 {route} 沒有站點資料")

        # 取得預估到站時間資料（可選，失敗不影響基本功能）
        eta_data = []
        try:
            eta_data = await bus_service.get_estimated_time_of_arrival(route, city, direction)
        except Exception as e:
            logger.warning(f"無法取得路線 {route} 的預估到站時間: {e}")
            # ETA 失敗不影響基本路線資訊回傳

        # 建立站點 ETA 對照表
        eta_map = {}
        for eta in eta_data:
            stop_uid = eta.get("StopUID", "")
            estimate_time = eta.get("EstimateTime")
            stop_status = eta.get("StopStatus", 0)

            # 轉換時間為文字
            eta_text = "未發車"
            status = "normal"
            if stop_status == 1:
                eta_text = "未發車"
                status = "not_started"
            elif stop_status == 2:
                eta_text = "進站中"
                status = "arriving"
            elif stop_status == 3:
                eta_text = "已過站"
                status = "passed"
            elif estimate_time is not None:
                minutes = estimate_time // 60
                if minutes < 1:
                    eta_text = "即將進站"
                    status = "arriving"
                elif minutes < 3:
                    eta_text = f"{minutes}分鐘"
                    status = "near"
                else:
                    eta_text = f"{minutes}分鐘"

            eta_map[stop_uid] = {"text": eta_text, "status": status}

        # 處理站點資料
        stops = []
        buses = []
        seen_stop_uids = set()  # 用於去重（以 StopUID）
        seen_sequences = set()  # 用於去重（以 StopSequence）

        # 收集所有站點 UID 用於批量查詢經緯度
        all_stop_uids = []
        # 同時建立從 stop_uid 到 stop 資料的映射，用於直接取得經緯度
        stop_data_map = {}  # {stop_uid: stop_data}

        for route_stop in route_stops_data:
            route_stop_direction = route_stop.get("Direction", 0)
            if route_stop_direction != direction:
                continue
            stops_list = route_stop.get("Stops", [])
            for stop in stops_list:
                stop_uid = stop.get("StopUID", "")
                if stop_uid:
                    all_stop_uids.append(stop_uid)
                    stop_data_map[stop_uid] = stop  # 儲存完整的 stop 資料

        # 批量取得站點經緯度（從快取，作為備援）
        stop_positions = {}
        try:
            stop_positions = await bus_service.get_stop_positions_batch(all_stop_uids)
            logger.info(f"從快取取得 {len(stop_positions)} 個站點的經緯度資料")
        except Exception as e:
            logger.warning(f"從快取取得站點經緯度資料失敗: {e}")

        for route_stop in route_stops_data:
            # 檢查方向是否匹配（避免重複加入其他方向的站點）
            route_stop_direction = route_stop.get("Direction", 0)
            if route_stop_direction != direction:
                continue

            stops_list = route_stop.get("Stops", [])
            for stop in stops_list:
                stop_uid = stop.get("StopUID", "")
                stop_name = stop.get("StopName", {}).get("Zh_tw", "")
                stop_sequence = stop.get("StopSequence", 0)

                # 檢查是否已經加入過此站點（避免重複）
                # 以 StopUID 或 StopSequence 去重
                if stop_uid and stop_uid in seen_stop_uids:
                    continue
                if stop_sequence in seen_sequences:
                    continue

                if stop_uid:
                    seen_stop_uids.add(stop_uid)
                seen_sequences.add(stop_sequence)

                # 取得 ETA 資訊
                eta_info = eta_map.get(stop_uid, {"text": "未發車", "status": "not_started"})

                # 取得站點經緯度（優先從 stop 資料直接取得，若失敗則從快取）
                latitude = None
                longitude = None

                # 方法 1: 直接從 stop 資料取得（最可靠）
                stop_position = stop.get("StopPosition", {})
                if stop_position:
                    latitude = stop_position.get("PositionLat")
                    longitude = stop_position.get("PositionLon")

                # 方法 2: 若直接取得失敗，嘗試從快取取得
                if latitude is None or longitude is None:
                    position = stop_positions.get(stop_uid, {})
                    latitude = position.get("latitude")
                    longitude = position.get("longitude")

                if latitude is None or longitude is None:
                    logger.debug(f"站點 {stop_name} (UID: {stop_uid}) 沒有經緯度資料")

                stops.append(BusStop(
                    sequence=stop_sequence,
                    name=stop_name,
                    eta=eta_info["text"],
                    status=eta_info["status"],
                    buses=[],
                    latitude=latitude,
                    longitude=longitude
                ))

                # 如果即將進站或接近，建立車輛資訊
                if eta_info["status"] in ["arriving", "near"]:
                    buses.append(BusVehicle(
                        id=f"bus-{stop_sequence}",
                        plate_number="",
                        bus_type="一般公車",
                        at_stop=stop_sequence,
                        eta_next=eta_info["text"],
                        heading_to=min(stop_sequence + 1, len(stops_list))
                    ))

        # 排序站點
        stops.sort(key=lambda x: x.sequence)

        # 取得路線起訖站資訊
        departure = route_info.get("DepartureStopNameZh", "") or route_info.get("DepartureStopName", "")
        destination = route_info.get("DestinationStopNameZh", "") or route_info.get("DestinationStopName", "")

        # 建立方向資訊
        direction_info = DirectionInfo(
            direction=direction,
            direction_name="去程" if direction == 0 else "返程",
            departure=departure if direction == 0 else destination,
            arrival=destination if direction == 0 else departure,
            go=DirectionDetail(
                direction=0,
                direction_name=f"往 {destination}",
                departure=departure,
                arrival=destination
            ),
            back=DirectionDetail(
                direction=1,
                direction_name=f"往 {departure}",
                departure=destination,
                arrival=departure
            )
        )

        # 如果沒有接近的車輛，建立一些模擬車輛
        if not buses and stops:
            for j in range(1, 4):
                position = min(j * (len(stops) // 3), len(stops) - 1)
                if position < len(stops):
                    buses.append(BusVehicle(
                        id=f"{route}-bus-{j}",
                        plate_number="",
                        bus_type="一般公車",
                        at_stop=position,
                        eta_next=f"{j * 5}分後到達",
                        heading_to=min(position + 1, len(stops) - 1)
                    ))

        result = BusRouteData(
            route=route,
            route_name=route,
            direction=direction_info,
            stops=stops,
            buses=buses,
            updated=datetime.now().isoformat()
        )

        # 存入快取（30 秒 TTL）
        if _estimation_cache:
            await _estimation_cache.set(cache_key, result, ttl_seconds=30)

        logger.info(f"TDX API: 路線 {route} 有 {len(stops)} 個站牌, {len(buses)} 輛車")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取得路線 {route} 資料失敗：{e}")
        import traceback
        logger.error(f"詳細錯誤堆疊：{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"取得路線資料失敗：{str(e)}")


@app.get("/api/bus/cache/status")
async def get_bus_cache_status():
    """
    取得公車快取狀態

    返回快取中路線數量、最後更新時間等資訊
    """
    global bus_cache_manager

    if not bus_cache_manager:
        return {"status": "not_initialized", "message": "快取管理器尚未初始化"}

    status = await bus_cache_manager.get_cache_status()
    return status


@app.post("/api/bus/cache/refresh/{route}")
async def refresh_bus_route_cache(route: str, direction: int = Query(0, description="方向：0=去程, 1=返程")):
    """
    手動重新整理特定路線的快取

    參數:
        route: 路線名稱（如：藍15, 235, 307）
        direction: 方向（0=去程, 1=返程），預設為去程
    """
    global bus_cache_manager

    if not bus_cache_manager:
        raise HTTPException(status_code=503, detail="快取管理器尚未初始化")

    try:
        success = await bus_cache_manager.refresh_route(route, direction)
        if success:
            return {"success": True, "message": f"路線 {route} 方向 {direction} 快取已更新"}
        else:
            raise HTTPException(status_code=500, detail=f"更新路線 {route} 快取失敗")
    except Exception as e:
        logger.error(f"手動更新快取失敗：{e}")
        raise HTTPException(status_code=500, detail=f"更新快取失敗：{str(e)}")


@app.post("/api/bus/cache/clear")
async def clear_bus_cache():
    """
    清空所有公車快取資料

    下次請求時會重新爬取最新資料
    """
    global bus_cache_manager

    if not bus_cache_manager:
        raise HTTPException(status_code=503, detail="快取管理器尚未初始化")

    try:
        await bus_cache_manager.clear_cache()
        return {"success": True, "message": "已清空所有公車快取資料"}
    except Exception as e:
        logger.error(f"清空快取失敗：{e}")
        raise HTTPException(status_code=500, detail=f"清空快取失敗：{str(e)}")


# ==================== 統一快取管理 API ====================

@app.get("/api/cache/status")
async def get_cache_status():
    """
    取得統一快取管理器的狀態資訊

    返回所有快取的統計資訊，包括命中率、項目數量等
    """
    try:
        cache_manager = get_cache_manager()
        return cache_manager.get_all_stats()
    except Exception as e:
        logger.error(f"取得快取狀態失敗：{e}")
        raise HTTPException(status_code=500, detail=f"取得快取狀態失敗：{str(e)}")


@app.post("/api/cache/clear/{service}")
async def clear_service_cache(service: str):
    """
    清除指定服務的快取

    參數:
        service: 服務名稱 (bus, tra, thsr, bike, all)
    """
    try:
        cache_manager = get_cache_manager()

        if service == "all":
            await cache_manager.clear_all()
            return {"success": True, "message": "所有快取已清除"}
        elif service in ["bus", "tra", "thsr", "bike"]:
            await cache_manager.clear_service_cache(service)
            return {"success": True, "message": f"{service} 服務的快取已清除"}
        else:
            raise HTTPException(status_code=400, detail=f"未知的服務名稱: {service}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清除快取失敗：{e}")
        raise HTTPException(status_code=500, detail=f"清除快取失敗：{str(e)}")


# ----- 台鐵 API (使用 TDX) -----

@app.get("/api/railway/stations")
async def get_railway_stations():
    """取得台鐵車站列表 (使用 TDX API)，包含經緯度座標和縣市資訊"""
    try:
        tra_service = get_tra_service()
        # 使用新的方法取得包含經緯度的站點資料
        stations_with_pos = await tra_service.get_stations_with_positions()

        stations = []
        for station in stations_with_pos:
            station_id = station.get("StationID", "")
            station_name = station.get("StationName", {}).get("Zh_tw", "")
            station_name_en = station.get("StationName", {}).get("En", "")
            latitude = station.get("latitude")
            longitude = station.get("longitude")
            city = station.get("LocationCity", "")

            if station_id and station_name:
                stations.append({
                    "station_code": station_id,
                    "station_name": station_name,
                    "station_name_en": station_name_en,
                    "latitude": latitude,
                    "longitude": longitude,
                    "city": city,
                })

        return stations
    except Exception as e:
        logger.error(f"取得台鐵站點列表失敗: {e}")
        # 如果 TDX API 失敗，回傳靜態站點列表作為備援（無經緯度）
        stations = []
        for code, name in TaiwanRailwayScraper.STATIONS.items():
            stations.append({
                "station_code": code,
                "station_name": name,
                "station_name_en": name,
                "latitude": None,
                "longitude": None,
                "city": "",
            })
        return stations


@app.get("/api/railway/timetable", response_model=List[TrainTimeEntry])
async def get_railway_timetable(
    from_station: str = Query(..., description="出發站代碼或名稱"),
    to_station: str = Query(..., description="抵達站代碼或名稱"),
    date: str = Query(None, description="日期 YYYY/MM/DD"),
    time: str = Query(None, description="時間 HH:MM")
):
    """查詢台鐵時刻表 (使用 TDX API)"""
    try:
        tra_service = get_tra_service()

        # 將站點代碼轉換為站名（如果是數字代碼）
        from_name = from_station
        to_name = to_station

        # 如果是數字代碼，嘗試轉換為站名
        if from_station.isdigit():
            station = await tra_service.get_station_by_id(from_station)
            if station:
                from_name = station.get("StationName", {}).get("Zh_tw", from_station)

        if to_station.isdigit():
            station = await tra_service.get_station_by_id(to_station)
            if station:
                to_name = station.get("StationName", {}).get("Zh_tw", to_station)

        # 搜尋時刻表
        trains = await tra_service.search_timetable(from_name, to_name, date)

        # 轉換為 API 回傳格式
        results = []
        for train in trains:
            # 將分鐘數轉換為 HH:MM 格式
            duration_minutes = train.get("duration")
            duration_str = None
            if duration_minutes:
                hours = duration_minutes // 60
                mins = duration_minutes % 60
                duration_str = f"{hours}:{mins:02d}"

            results.append(TrainTimeEntry(
                train_no=train.get("train_no", ""),
                train_type=train.get("train_type", ""),
                departure_station=train.get("from_station", ""),
                arrival_station=train.get("to_station", ""),
                departure_time=train.get("departure_time", ""),
                arrival_time=train.get("arrival_time", ""),
                duration=duration_str,
                transferable=True
            ))

        return results

    except Exception as e:
        logger.error(f"查詢台鐵時刻表失敗: {e}")
        # 如果 TDX API 失敗，使用舊的 Playwright 爬蟲作為備援
        return await railway_scraper.search_timetable(from_station, to_station, date, time)


# ----- 高鐵 API (使用 TDX) -----

@app.get("/api/thsr/stations")
async def get_thsr_stations():
    """取得高鐵車站列表 (使用 TDX API)，包含經緯度座標"""
    try:
        thsr_service = get_thsr_service()
        # 使用新的方法取得包含經緯度的站點資料
        stations_with_pos = await thsr_service.get_stations_with_positions()

        stations = []
        for station in stations_with_pos:
            station_id = station.get("StationID", "")
            station_name = station.get("StationName", {}).get("Zh_tw", "")
            station_name_en = station.get("StationName", {}).get("En", "")
            latitude = station.get("latitude")
            longitude = station.get("longitude")

            if station_id and station_name:
                stations.append({
                    "code": station_id,
                    "name": station_name,
                    "name_en": station_name_en,
                    "latitude": latitude,
                    "longitude": longitude,
                })

        return stations
    except Exception as e:
        logger.error(f"取得高鐵站點列表失敗: {e}")
        # 如果 TDX API 失敗，回傳靜態站點列表作為備援（無經緯度）
        stations = []
        for code, name in THSRScraper.STATIONS.items():
            stations.append({
                "code": code,
                "name": name,
                "latitude": None,
                "longitude": None,
            })
        return stations


@app.get("/api/thsr/timetable", response_model=List[THSRTrainEntry])
async def get_thsr_timetable(
    from_station: str = Query(..., description="出發站代碼或名稱"),
    to_station: str = Query(..., description="抵達站代碼或名稱"),
    date: str = Query(None, description="日期 YYYY-MM-DD")
):
    """查詢高鐵時刻表 (使用 TDX API)"""
    try:
        thsr_service = get_thsr_service()

        # 將站點代碼轉換為站名（如果是數字代碼）
        from_name = from_station
        to_name = to_station

        # 如果是數字代碼，嘗試轉換為站名
        if from_station.isdigit():
            station = await thsr_service.get_station_by_id(from_station)
            if station:
                from_name = station.get("StationName", {}).get("Zh_tw", from_station)

        if to_station.isdigit():
            station = await thsr_service.get_station_by_id(to_station)
            if station:
                to_name = station.get("StationName", {}).get("Zh_tw", to_station)

        # 搜尋時刻表
        trains = await thsr_service.search_timetable(from_name, to_name, date)

        # 轉換為 API 回傳格式
        results = []
        for train in trains:
            # 將分鐘數轉換為 HH:MM 格式
            duration_minutes = train.get("duration")
            duration_str = None
            if duration_minutes:
                hours = duration_minutes // 60
                mins = duration_minutes % 60
                duration_str = f"{hours}:{mins:02d}"

            results.append(THSRTrainEntry(
                train_no=train.get("train_no", ""),
                departure_station=train.get("from_station", ""),
                arrival_station=train.get("to_station", ""),
                departure_time=train.get("departure_time", ""),
                arrival_time=train.get("arrival_time", ""),
                duration=duration_str,
                business_seat_available=True,
                standard_seat_available=True,
                free_seat_available=True
            ))

        return results

    except Exception as e:
        logger.error(f"查詢高鐵時刻表失敗: {e}")
        # 如果 TDX API 失敗，使用舊的 Playwright 爬蟲作為備援
        return await thsr_scraper.search_timetable(from_station, to_station, date)


# ----- 測試用端點 -----

@app.get("/api/health")
async def health_check():
    """健康檢查端點"""
    global _ntpc_bus_service, _route_cache, _estimation_cache

    # 收集 CSV 資料狀態
    csv_status = "inactive"
    routes_count = 0
    if _ntpc_bus_service:
        routes_count = len(_ntpc_bus_service._routes)
        csv_status = "active" if routes_count > 0 else "loading"

    # 收集快取統計
    cache_stats = {}
    if _route_cache:
        cache_stats["route_cache"] = _route_cache.get_stats()
    if _estimation_cache:
        cache_stats["estimation_cache"] = _estimation_cache.get_stats()

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "playwright": "active" if _browser else "inactive",
        "csv_data": {
            "status": csv_status,
            "routes_count": routes_count
        },
        "cache": cache_stats
    }


@app.get("/api/system/status")
async def system_status():
    """
    系統狀態監控

    提供詳細的系統運行狀態資訊。
    """
    global _ntpc_bus_service, _background_scheduler

    status = {
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }

    # CSV 資料狀態
    if _ntpc_bus_service:
        status["components"]["csv_data"] = {
            "status": "active",
            "routes_count": len(_ntpc_bus_service._routes),
            "stops_count": sum(len(stops) for stops in _ntpc_bus_service._stops.values()),
            "estimations_count": len(_ntpc_bus_service._estimations)
        }
    else:
        status["components"]["csv_data"] = {"status": "inactive"}

    # 背景排程器狀態
    if _background_scheduler:
        status["components"]["scheduler"] = _background_scheduler.get_status()
    else:
        status["components"]["scheduler"] = {"status": "inactive"}

    # 快取狀態
    cache_stats = {}
    if _route_cache:
        cache_stats["route_cache"] = _route_cache.get_stats()
    if _estimation_cache:
        cache_stats["estimation_cache"] = _estimation_cache.get_stats()
    status["components"]["memory_cache"] = cache_stats

    return status


@app.post("/api/system/refresh")
async def system_refresh():
    """
    手動重新整理系統資料

    強制重新下載 CSV 資料並清除快取。
    """
    global _ntpc_bus_service

    try:
        if _ntpc_bus_service:
            # 重新下載資料
            await _ntpc_bus_service.initialize()

            # 清除快取
            if _route_cache:
                await _route_cache.clear()
            if _estimation_cache:
                await _estimation_cache.clear()

            return {
                "status": "success",
                "message": "資料已重新整理",
                "routes_count": len(_ntpc_bus_service._routes),
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=503, detail="CSV 資料服務未初始化")

    except Exception as e:
        logger.error(f"資料重新整理失敗：{e}")
        raise HTTPException(status_code=500, detail=f"重新整理失敗：{str(e)}")


@app.get("/api/test/railway")
async def test_railway():
    """測試台鐵爬蟲"""
    results = await railway_scraper.search_timetable("108", "212")  # 台北到台中
    return {"count": len(results), "results": results[:5]}


@app.get("/api/test/thsr")
async def test_thsr():
    """測試高鐵爬蟲"""
    results = await thsr_scraper.search_timetable("TPE", "TCH")  # 台北到台中
    return {"count": len(results), "results": results[:5]}


# ==================== UBike API ====================

@app.get("/api/bike/stations", response_model=BikeStationsResponse)
async def get_bike_stations(
    city: str = Query(..., description="縣市代碼（Taipei, NewTaipei, Taichung 等）")
):
    """
    取得縣市所有腳踏車租借站

    回傳指定縣市的所有 YouBike 租借站資訊，包含站點基本資料與即時車位資訊。
    資料來自快取管理器，若快取不存在則會自動從 TDX API 撈取。
    """
    # 驗證縣市代碼
    if city not in SUPPORTED_CITIES:
        raise HTTPException(
            status_code=400,
            detail=f"不支援的縣市代碼: {city}。支援的縣市: {', '.join(SUPPORTED_CITIES[:6])}..."
        )

    try:
        # 優先從快取管理器讀取
        if bike_cache_manager:
            stations = bike_cache_manager.get_cached_merged(city)
            if stations:
                logger.info(f"從快取回傳 {city} 的 {len(stations)} 個站點")
                data = [BikeStation(**station) for station in stations]
                return BikeStationsResponse(
                    success=True,
                    data=data,
                    total=len(data),
                    city=city
                )

        # 若快取沒有，fallback 到直接呼叫 TDX API
        logger.info(f"快取未命中，從 TDX API 撈取 {city} 站點資料")
        bike_service = get_bike_service()
        stations = await bike_service.get_stations_with_availability(city)

        # 轉換為回應格式
        data = [BikeStation(**station) for station in stations]

        return BikeStationsResponse(
            success=True,
            data=data,
            total=len(data),
            city=city
        )
    except Exception as e:
        logger.error(f"取得租借站資料失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bike/stations/nearby", response_model=BikeNearbyStationsResponse)
async def get_nearby_bike_stations(
    lat: float = Query(..., description="緯度（-90 ~ 90）", ge=-90, le=90),
    lon: float = Query(..., description="經度（-180 ~ 180）", ge=-180, le=180),
    radius: int = Query(1000, description="搜尋半徑（公尺，最大 5000）", ge=100, le=5000),
    limit: int = Query(20, description="回傳數量上限", ge=1, le=100),
    city: str = Query("Taipei", description="縣市代碼")
):
    """
    取得附近腳踏車租借站

    使用 Haversine Formula 計算距離，回傳指定範圍內的租借站，
    按距離由近到遠排序。資料來自快取管理器。
    """
    # 驗證縣市代碼
    if city not in SUPPORTED_CITIES:
        raise HTTPException(
            status_code=400,
            detail=f"不支援的縣市代碼: {city}"
        )

    try:
        bike_service = get_bike_service()

        # 優先從快取讀取站點資料
        if bike_cache_manager:
            stations = bike_cache_manager.get_cached_merged(city)
            if stations:
                logger.info(f"從快取取得 {city} 站點進行附近搜尋")
                # 使用快取資料進行附近搜尋
                nearby = bike_service.calculate_nearby_from_list(
                    stations, lat, lon, radius, limit
                )
                data = [BikeStationWithDistance(**station) for station in nearby]
                return BikeNearbyStationsResponse(
                    success=True,
                    data=data,
                    center={"lat": lat, "lon": lon},
                    radius=radius,
                    total=len(data)
                )

        # 若快取沒有，fallback 到直接呼叫 TDX API
        logger.info(f"快取未命中，從 TDX API 撈取 {city} 附近站點")
        nearby = await bike_service.get_nearby_stations(city, lat, lon, radius, limit)

        # 轉換為回應格式
        data = [BikeStationWithDistance(**station) for station in nearby]

        return BikeNearbyStationsResponse(
            success=True,
            data=data,
            center={"lat": lat, "lon": lon},
            radius=radius,
            total=len(data)
        )
    except Exception as e:
        logger.error(f"搜尋附近租借站失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bike/search", response_model=BikeSearchResponse)
async def search_bike_stations(
    keyword: str = Query(..., description="搜尋關鍵字", min_length=1),
    city: Optional[str] = Query(None, description="指定縣市（未提供則搜尋預設縣市）"),
    limit: int = Query(20, description="回傳數量上限", ge=1, le=100)
):
    """
    搜尋腳踏車租借站

    依關鍵字搜尋租借站名稱或地址，支援模糊比對。
    優先從快取搜尋，若快取不存在則從 TDX API 撈取。
    """
    try:
        bike_service = get_bike_service()

        # 如果指定了縣市，優先從快取讀取
        if city and bike_cache_manager:
            stations = bike_cache_manager.get_cached_merged(city)
            if stations:
                logger.info(f"從快取搜尋 {city} 的站點")
                # 在快取資料中搜尋
                keyword_lower = keyword.lower()
                results = []
                for station in stations:
                    name = station.get("name", "").lower()
                    name_en = station.get("name_en", "").lower()
                    address = station.get("address", "").lower()

                    if (keyword_lower in name or
                        keyword_lower in name_en or
                        keyword_lower in address):
                        station_copy = station.copy()
                        station_copy["city"] = city
                        results.append(station_copy)

                results = results[:limit]
                data = [BikeStation(**station) for station in results]
                return BikeSearchResponse(
                    success=True,
                    data=data,
                    keyword=keyword,
                    total=len(data)
                )

        # 若快取沒有或未指定縣市，fallback 到直接呼叫 TDX API
        logger.info(f"從 TDX API 搜尋站點: {keyword}")
        results = await bike_service.search_stations(keyword, city, limit)

        # 轉換為回應格式
        data = [BikeStation(**station) for station in results]

        return BikeSearchResponse(
            success=True,
            data=data,
            keyword=keyword,
            total=len(data)
        )
    except Exception as e:
        logger.error(f"搜尋租借站失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bike/cache/status")
async def get_bike_cache_status():
    """
    取得 UBike 快取狀態

    回傳快取管理器的狀態資訊，包含各縣市資料更新時間和統計。
    """
    if bike_cache_manager is None:
        raise HTTPException(status_code=503, detail="UBike 快取管理器未啟動")

    try:
        status = bike_cache_manager.get_cache_status()
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        logger.error(f"取得快取狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bike/stations/{station_uid}", response_model=BikeStationDetailResponse)
async def get_bike_station_detail(
    station_uid: str,
    city: str = Query(..., description="縣市代碼")
):
    """
    取得特定站點詳細資訊

    回傳指定站點的完整資訊，包含即時車位狀態。
    優先從快取讀取，若快取不存在則從 TDX API 撈取。
    """
    # 驗證縣市代碼
    if city not in SUPPORTED_CITIES:
        raise HTTPException(
            status_code=400,
            detail=f"不支援的縣市代碼: {city}"
        )

    try:
        # 優先從快取管理器讀取
        if bike_cache_manager:
            stations = bike_cache_manager.get_cached_merged(city)
            if stations:
                logger.info(f"從快取查找站點 {station_uid}")
                for station in stations:
                    if station.get("station_uid") == station_uid:
                        return BikeStationDetailResponse(
                            success=True,
                            data=BikeStation(**station)
                        )

        # 若快取沒有，fallback 到直接呼叫 TDX API
        logger.info(f"快取未命中，從 TDX API 取得站點 {station_uid}")
        bike_service = get_bike_service()
        station = await bike_service.get_station_detail(city, station_uid)

        if not station:
            raise HTTPException(status_code=404, detail=f"找不到站點: {station_uid}")

        return BikeStationDetailResponse(
            success=True,
            data=BikeStation(**station)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取得站點詳細資訊失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
