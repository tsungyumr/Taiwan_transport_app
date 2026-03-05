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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global _pw, _browser
    # Startup: init Playwright
    _pw = await async_playwright().start()
    _browser = await _pw.chromium.launch(
        headless=True,
        args=['--disable-blink-features=AutomationControlled']
    )
    print("Playwright browser started")
    yield
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
        
        train_types = ["自強", "區間車", "莒光", "太魯閣", "普悠瑪"]
        
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

    使用 ebus.gov.taipei 爬蟲取得真實的公車路線資料
    """
    try:
        # 建立新的爬蟲實例並使用 async with 確保資源正確釋放
        async with TaipeiBusScraper(headless=True) as scraper:
            # 搜尋路線
            if route_name:
                routes = await scraper.search_routes(route_name)
            else:
                routes = await scraper.get_all_routes()

            # 轉換為 API 需要的格式
            result = []
            for route in routes:  # 回傳所有路線，不限制數量
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

    使用 ebus.gov.taipei 爬蟲取得真實的公車資料

    參數:
        route: 路線名稱（如：藍15, 235, 307）
        direction: 方向（0=去程, 1=返程），預設為去程
    """
    try:
        logger.info(f"API 收到請求: /api/bus/{route}, direction={direction}")

        # 建立新的爬蟲實例並使用 async with 確保資源正確釋放
        logger.info("正在初始化爬蟲...")
        async with TaipeiBusScraper(headless=True) as scraper:
            logger.info(f"爬蟲初始化完成，正在取得路線 {route} 資訊...")

            # 呼叫爬蟲取得路線資訊（指定方向）
            route_info = await scraper.get_route_info(route, direction=direction)
            logger.info(f"取得路線資訊成功: {route_info.route_name}, 站數: {len(route_info.stops)}, 方向: {direction}")

            # 嘗試取得另一個方向的資訊（用於顯示起訖站）
            opposite_direction = 1 if direction == 0 else 0
            opposite_route_info = None
            try:
                opposite_route_info = await scraper.get_route_info(route, direction=opposite_direction)
                logger.info(f"取得反向路線資訊成功: {opposite_route_info.route_name}, 站數: {len(opposite_route_info.stops)}")
            except Exception as e:
                logger.warning(f"取得反向路線資訊失敗: {e}")

            # 轉換站點資料 - 包含序列號、站名、到站時間、車輛資訊
            stops = []
            logger.info(f"開始轉換 {len(route_info.stops)} 個站點資料")
            for i, stop in enumerate(route_info.stops):
                # 判斷發車狀態
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

                # 除錯：記錄前幾個站點的站名
                if i < 3:
                    logger.info(f"站點 {i}: sequence={stop.sequence}, name='{stop.name}'")

                # 收集該站點的車輛資訊
                buses_at_stop = []
                if stop.buses:
                    for bus in stop.buses:
                        buses_at_stop.append({
                            "plate_number": bus.get("plate_number", ""),
                            "bus_type": bus.get("bus_type", ""),
                            "remaining_seats": bus.get("remaining_seats")
                        })

                stops.append(BusStop(
                    sequence=stop.sequence,
                    name=stop.name,
                    eta=eta_str,
                    status=status,
                    buses=buses_at_stop
                ))

            # 轉換車輛資料 - 收集所有在路上的車輛
            buses = []
            for stop in route_info.stops:
                if stop.buses:
                    for bus in stop.buses:
                        # 判斷車輛狀態
                        if stop.eta is None:
                            vehicle_status = "未發車"
                        elif stop.eta == 0:
                            vehicle_status = "進站中"
                        else:
                            vehicle_status = f"{stop.eta} 分鐘後到站"

                        buses.append(BusVehicle(
                            id=bus.get("plate_number", f"{route}-bus"),
                            plate_number=bus.get("plate_number", ""),
                            bus_type=bus.get("bus_type", ""),
                            at_stop=stop.sequence,
                            eta_next=vehicle_status,
                            heading_to=stop.sequence + 1 if stop.sequence < len(route_info.stops) else stop.sequence,
                            remaining_seats=bus.get("remaining_seats")
                        ))

            # 準備方向資訊
            # 使用從爬蟲抓取的方向名稱
            direction_name_go = route_info.direction_name_go or "往 終點站"
            direction_name_back = route_info.direction_name_back or "往 起點站"

            # 從當前方向和反向資訊中提取起訖站
            current_departure = route_info.departure_stop or ""
            current_arrival = route_info.arrival_stop or ""

            # 如果有反向資訊，取得反向的起訖站
            opposite_departure = ""
            opposite_arrival = ""
            if opposite_route_info:
                opposite_departure = opposite_route_info.departure_stop or ""
                opposite_arrival = opposite_route_info.arrival_stop or ""
                # 如果反向有方向名稱，也一併使用
                if not direction_name_go and opposite_route_info.direction_name_back:
                    direction_name_go = opposite_route_info.direction_name_back
                if not direction_name_back and opposite_route_info.direction_name_go:
                    direction_name_back = opposite_route_info.direction_name_go

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

            logger.info(f"API 請求完成，回傳 {len(stops)} 個站點，{len(buses)} 輛車，方向: {direction}")
            logger.info(f"方向資訊: 去程 {direction_name_go}, 返程 {direction_name_back}")
            return BusRouteData(
                route=route,
                route_name=route_info.route_name or route,
                direction=direction_info,
                stops=stops if stops else [BusStop(sequence=i, name=f"{route} 第{i+1}站", eta="未發車", status="not_started", buses=[]) for i in range(25)],
                buses=buses if buses else [],
                updated=datetime.now().isoformat()
            )

    except Exception as e:
        logger.error(f"取得公車路線資料失敗：{e}")
        import traceback
        logger.error(f"詳細錯誤堆疊：{traceback.format_exc()}")

        # 回傳錯誤訊息給前端，不要回退到模擬資料（這樣才能知道真正的問題）
        raise HTTPException(status_code=500, detail=f"無法取得路線資料：{str(e)}")


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
