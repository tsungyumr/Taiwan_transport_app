"""
台灣交通時刻表爬蟲 API - Playwright版
Taiwan Transport Timetable Scraper API with Playwright
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

app = FastAPI(title="台灣交通時刻表 Playwright API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Models (same as before)
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

class TrainStation(BaseModel):
    station_code: str
    station_name: str
    station_name_en: str
    latitude: float = None
    longitude: float = None
    address: str = None
    available: bool = True
    station_type: str = "normal"  # normal, major, minor

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

class PlaywrightScraper:
    """Playwright 爬蟲基類"""
    @classmethod
    async def create_browser(cls):
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)
        return pw, browser

# ==================== 台鐵 Playwright 爬蟲 ====================

class TaiwanRailwayScraper:
    STATIONS = {
        "100": "基隆", "108": "台北", "110": "板橋", "212": "台中", "232": "嘉義", "244": "台南", "270": "高雄"
        # Add more as needed
    }

    async def search_timetable(self, from_station: str, to_station: str, date: str = None, time: str = None) -> List[TrainTimeEntry]:
        date = date or datetime.now().strftime("%Y/%m/%d")
        
        pw, browser = await PlaywrightScraper.create_browser()
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()
        
        try:
            await page.goto("https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip112/gobytime", timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            
            # Fill form
            await page.fill('input[name="startStation"]', from_station)
            await page.fill('input[name="endStation"]', to_station)
            await page.fill('input[name="rideDate"]', date)
            await page.click('input[value="查詢"]')
            
            await page.wait_for_load_state("networkidle", timeout=20000)
            
            # Parse results - use specific selector from analysis
            rows = await page.query_selector_all('body > table:nth-child(4) tbody tr')
            results = []
            
            for row in rows[:20]:
                cells = await row.query_selector_all('td')
                if len(cells) >= 6:
                    try:
                        train_no = await cells[1].inner_text()
                        train_type = await cells[2].inner_text()
                        dep_time = await cells[3].inner_text()
                        arr_time = await cells[5].inner_text()
                        
                        duration = "N/A"  # Calculate or extract
                        transferable = True
                        
                        results.append(TrainTimeEntry(
                            train_no=train_no.strip(),
                            train_type=train_type.strip(),
                            departure_station=from_station,
                            arrival_station=to_station,
                            departure_time=dep_time.strip(),
                            arrival_time=arr_time.strip(),
                            duration=duration,
                            transferable=transferable
                        ))
                    except:
                        continue
            
            return results
            
        except Exception as e:
            print(f"TRA scrape error: {e}")
            return []
        finally:
            await browser.close()
            await pw.stop()

# ==================== 高鐵 & 公車 (TBD) ====================

class TaipeiBusScraper:
    async def get_bus_routes(self, route_name: str = None, limit: int = 50) -> List[BusRoute]:
        # Playwright for eBus - complex, use API fallback for now
        return []  # Mock or API

class THSRScraper:
    async def search_timetable(self, from_station: str, to_station: str, date: str = None) -> List[THSRTrainEntry]:
        # THSR needs reverse engineering
        return []  # Mock for now

# Instances
tra_scraper = TaiwanRailwayScraper()
bus_scraper = TaipeiBusScraper()
thsr_scraper = THSRScraper()

@app.get("/")
async def root():
    return {"message": "台灣交通時刻表 Playwright API v1.1.0", "status": "TRA ready"}

@app.get("/api/railway/timetable", response_model=List[TrainTimeEntry])
async def get_railway_timetable(
    from_station: str = Query(..., description="出發站 e.g. 台北"),
    to_station: str = Query(..., description="抵達站 e.g. 台中"),
    date: str = Query(None, description="日期 YYYY/MM/DD"),
    time: str = Query(None)
):
    return await tra_scraper.search_timetable(from_station, to_station, date, time)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "playwright": "ready", "railway": "ready"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
