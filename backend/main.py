"""
台灣交通時刻表爬蟲 API - 整合 Playwright 版本
Taiwan Transport Timetable Scraper API with Playwright

Target Sources:
1. 高鐵時刻表: https://www.thsrc.com.tw (使用 Playwright)
2. 台鐵時刻表: https://www.railway.gov.tw/tra-tip-web (使用 Playwright)
3. 公車: ebus.gov.taipei (使用 mock data)
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global _pw, _browser, bus_cache_manager

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

    yield

    # Shutdown: 停止公車快取管理器
    if bus_cache_manager:
        try:
            await bus_cache_manager.stop()
            print("公車快取管理器已停止")
        except Exception as e:
            print(f"Bus cache manager stop ignored: {e}")

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


class BusRealTimeArrival(BaseModel):
    route_id: str
    route_name: str
    current_time: str
    arrivals: List[Dict]


class TrainStation(BaseModel):
    station_code: str
    station_name: str
    station_name_en: str


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

@app.get("/api/thsr/stations", response_model=List[THSRStation])
async def get_thsr_stations() -> List[THSRStation]:
    """
    取得高鐵站點列表

    Returns:
        List[THSRStation]: 高鐵站點列表
    """
    # 檢查快取
    cached_stations = await thsr_stations_cache.get()
    if cached_stations:
        return [THSRStation(**station) for station in cached_stations]

    # 爬取新資料
    stations = await scrape_thsr_stations()

    if stations:
        # 更新快取
        await thsr_stations_cache.set(stations)
        return [THSRStation(**station) for station in stations]
    else:
        raise HTTPException(status_code=500, detail="無法取得高鐵站點資料")

@app.get("/")
async def root():
    return {
        "message": "台灣交通時刻表 API v2.0.0",
        "version": "2.0.0",
        "features": ["Playwright scrapers for TRA & THSR", "Taipei Bus scraper (ebus.gov.taipei)", "THSR stations API"]
    }


# ----- 公車 API -----

@app.get("/api/bus/routes", response_model=List[BusRoute])
async def get_bus_routes(route_name: str = Query(None, description="路線名稱關鍵字")):
    """
    取得公車路線列表

    懶加載模式：
    - 首次請求時爬取資料並存入快取
    - 後續請求從快取讀取（快取有效期1分鐘）
    - 快取過期後自動重新爬取
    """
    global bus_cache_manager

    try:
        # 從快取管理器取得路線列表
        if bus_cache_manager:
            routes = await bus_cache_manager.get_all_routes()
        else:
            # 快取管理器尚未初始化，直接爬取
            async with TaipeiBusScraper(headless=True) as scraper:
                routes = await scraper.get_all_routes()

        # 如果有搜尋關鍵字，進行過濾
        if route_name:
            routes = [r for r in routes if route_name.lower() in r.route_name.lower()]

        # 轉換為 API 需要的格式
        result = []
        for route in routes:
            parts = route.description.split("-") if "-" in route.description else ["", ""]
            result.append(BusRoute(
                route_id=route.route_id,
                route_name=route.route_name,
                departure_stop=parts[0].strip(),
                arrival_stop=parts[-1].strip() if len(parts) > 1 else "",
                operator=""
            ))

        return result

    except Exception as e:
        logger.error(f"取得公車路線失敗：{e}")
        # 錯誤時回傳靜態路線列表
        static_routes = [
            {"route_id": "01000T02", "route_name": "235", "departure": "新莊區", "arrival": "國父紀念館"},
            {"route_id": "01000T09", "route_name": "307", "departure": "撫遠街", "arrival": "台北客運板橋前站"},
            {"route_id": "01000T11", "route_name": "604", "departure": "台北車站", "arrival": "板橋"},
            {"route_id": "01000B15", "route_name": "藍15", "departure": "捷運昆陽站", "arrival": "捷運南港展覽館站"},
            {"route_id": "01000R10", "route_name": "紅10", "departure": "台北車站", "arrival": "故宮博物院"},
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


@app.get("/api/bus/timetable/{route_id}", response_model=List[BusTimeEntry])
async def get_bus_timetable(route_id: str):
    """
    取得公車時刻表

    使用 ebus.gov.taipei 爬蟲取得真實的時刻表資料
    """
    try:
        # 建立新的爬蟲實例並使用 async with 確保資源正確釋放
        async with TaipeiBusScraper(headless=True) as scraper:
            # 呼叫爬蟲取得路線資訊
            route_info = await scraper.get_route_info(route_id, direction=0)

            # 轉換為時刻表格式
            timetable = []
            for stop in route_info.stops:
                eta_str = f"{stop.eta}min" if stop.eta is not None else "N/A"
                timetable.append(BusTimeEntry(
                    stop_name=stop.name,
                    arrival_time=eta_str,
                    route_name=route_info.route_name
                ))
            return timetable[:50]

    except Exception as e:
        logger.error(f"取得公車時刻表失敗：{e}")
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


@app.get("/api/bus/{route}", response_model=BusRouteData)
async def get_bus_route(route: str, direction: int = Query(0, description="方向：0=去程, 1=返程")):
    """
    公車路線即時資料 - 站點列表 + 多輛公車位置 + ETA

    懶加載模式：
    - 首次請求時爬取資料並存入快取
    - 後續請求從快取讀取（快取有效期1分鐘）
    - 快取過期後自動重新爬取

    參數:
        route: 路線名稱（如：藍15, 235, 307）
        direction: 方向（0=去程, 1=返程），預設為去程
    """
    global bus_cache_manager

    try:
        logger.info(f"API 收到請求: /api/bus/{route}, direction={direction}")

        # 從快取管理器取得路線資料（懶加載：無快取或過期時會自動爬取）
        if bus_cache_manager:
            cached_data = await bus_cache_manager.get_route_data(route, direction)

            if cached_data:
                logger.info(f"取得路線 {route} 資料成功，快取時間: {cached_data.timestamp}")

                # 嘗試取得另一個方向的資訊（用於顯示起訖站）
                opposite_direction = 1 if direction == 0 else 0
                opposite_cached = await bus_cache_manager.get_route_data(route, opposite_direction)

                # 準備方向資訊
                direction_name_go = cached_data.direction_name_go or "往 終點站"
                direction_name_back = cached_data.direction_name_back or "往 起點站"
                current_departure = cached_data.departure_stop or ""
                current_arrival = cached_data.arrival_stop or ""

                opposite_departure = ""
                opposite_arrival = ""
                if opposite_cached:
                    opposite_departure = opposite_cached.departure_stop or ""
                    opposite_arrival = opposite_cached.arrival_stop or ""
                    if not direction_name_go and opposite_cached.direction_name_back:
                        direction_name_go = opposite_cached.direction_name_back
                    if not direction_name_back and opposite_cached.direction_name_go:
                        direction_name_back = opposite_cached.direction_name_go

                direction_info = DirectionInfo(
                    direction=direction,
                    direction_name="去程" if direction == 0 else "返程",
                    departure=current_departure,
                    arrival=current_arrival,
                    go=DirectionDetail(
                        direction=0,
                        direction_name=direction_name_go,
                        departure=current_departure if direction == 0 else opposite_departure,
                        arrival=current_arrival if direction == 0 else opposite_arrival
                    ),
                    back=DirectionDetail(
                        direction=1,
                        direction_name=direction_name_back,
                        departure=opposite_departure if direction == 0 else current_departure,
                        arrival=opposite_arrival if direction == 0 else current_arrival
                    )
                )

                # 轉換站點資料
                stops = [
                    BusStop(
                        sequence=s["sequence"],
                        name=s["name"],
                        eta=s["eta"],
                        status=s["status"],
                        buses=s["buses"]
                    )
                    for s in cached_data.stops
                ]

                # 轉換車輛資料
                buses = [
                    BusVehicle(
                        id=b["id"],
                        plate_number=b["plate_number"],
                        bus_type=b["bus_type"],
                        at_stop=b["at_stop"],
                        eta_next=b["eta_next"],
                        heading_to=b["heading_to"],
                        remaining_seats=b.get("remaining_seats")
                    )
                    for b in cached_data.buses
                ]

                return BusRouteData(
                    route=route,
                    route_name=cached_data.route_name or route,
                    direction=direction_info,
                    stops=stops if stops else [BusStop(sequence=i, name=f"{route} 第{i+1}站", eta="未發車", status="not_started", buses=[]) for i in range(25)],
                    buses=buses if buses else [],
                    updated=cached_data.timestamp.isoformat()
                )

        # 快取管理器未初始化，直接爬取
        logger.warning("快取管理器未初始化，直接爬取路線資料...")
        async with TaipeiBusScraper(headless=True) as scraper:
            route_info = await scraper.get_route_info(route, direction=direction)

            # 簡易轉換（略去完整轉換邏輯）
            stops = [
                BusStop(
                    sequence=i,
                    name=stop.name,
                    eta=f"{stop.eta} 分鐘" if stop.eta else "未發車",
                    status="normal" if stop.eta else "not_started",
                    buses=[]
                )
                for i, stop in enumerate(route_info.stops)
            ]

            direction_info = DirectionInfo(
                direction=direction,
                direction_name="去程" if direction == 0 else "返程",
                departure=route_info.departure_stop or "",
                arrival=route_info.arrival_stop or "",
                go=DirectionDetail(direction=0, direction_name="往 終點站", departure="", arrival=""),
                back=DirectionDetail(direction=1, direction_name="往 起點站", departure="", arrival="")
            )

            return BusRouteData(
                route=route,
                route_name=route_info.route_name or route,
                direction=direction_info,
                stops=stops,
                buses=[],
                updated=datetime.now().isoformat()
            )

    except Exception as e:
        logger.error(f"取得公車路線資料失敗：{e}")
        import traceback
        logger.error(f"詳細錯誤堆疊：{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"無法取得路線資料：{str(e)}")


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


# ----- 台鐵 API -----

@app.get("/api/railway/stations", response_model=List[TrainStation])
async def get_railway_stations():
    """取得台鐵車站列表"""
    stations = []
    for code, name in TaiwanRailwayScraper.STATIONS.items():
        stations.append(TrainStation(
            station_code=code,
            station_name=name,
            station_name_en=name
        ))
    return stations


@app.get("/api/railway/timetable", response_model=List[TrainTimeEntry])
async def get_railway_timetable(
    from_station: str = Query(..., description="出發站代碼或名稱"),
    to_station: str = Query(..., description="抵達站代碼或名稱"),
    date: str = Query(None, description="日期 YYYY/MM/DD"),
    time: str = Query(None, description="時間 HH:MM")
):
    """查詢台鐵時刻表"""
    return await railway_scraper.search_timetable(from_station, to_station, date, time)


# ----- 高鐵 API -----

@app.get("/api/thsr/stations")
async def get_thsr_stations():
    """取得高鐵車站列表"""
    stations = []
    for code, name in THSRScraper.STATIONS.items():
        stations.append({"code": code, "name": name})
    return stations


@app.get("/api/thsr/timetable", response_model=List[THSRTrainEntry])
async def get_thsr_timetable(
    from_station: str = Query(..., description="出發站代碼"),
    to_station: str = Query(..., description="抵達站代碼"),
    date: str = Query(None, description="日期 YYYY-MM-DD")
):
    """查詢高鐵時刻表"""
    return await thsr_scraper.search_timetable(from_station, to_station, date)


# ----- 測試用端點 -----

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "playwright": "active" if _browser else "inactive"
    }


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
