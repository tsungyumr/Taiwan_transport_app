"""
台鐵 Playwright 爬蟲
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
from typing import List, Dict

async def scrape_tra_timetable(start_station: str, end_station: str, ride_date: str = None) -> List[Dict]:
    """
    使用 Playwright 爬取台鐵時刻表
    
    Args:
        start_station: 出發站名稱 (e.g. "台北")
        end_station: 抵達站名稱 (e.g. "台中") 
        ride_date: 日期 YYYY/MM/DD
    """
    ride_date = ride_date or datetime.now().strftime("%Y/%m/%d")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        try:
            await page.goto("https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip112/gobytime", timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            
            # Fill form
            await page.fill('input[name="startStation"]', start_station)
            await page.fill('input[name="endStation"]', end_station)
            await page.fill('input[name="rideDate"]', ride_date)
            
            # Click query
            await page.click('input[name="query"]')
            await page.wait_for_load_state("networkidle", timeout=15000)
            
            # Wait for results table
            await page.wait_for_selector('body > table:nth-child(4) tbody tr', timeout=10000)
            
            # Extract rows
            rows = await page.query_selector_all('body > table:nth-child(4) tbody tr')
            results = []
            
            for row in rows[:20]:  # Limit to 20 results
                cells = await row.query_selector_all('td')
                if len(cells) >= 7:
                    try:
                        train_no = await (await cells[1].query_selector('a')).inner_text() or await cells[1].inner_text()
                        train_type = await cells[2].inner_text()
                        dep_time = await cells[3].inner_text()
                        arr_time = await cells[5].inner_text()
                        
                        results.append({
                            'train_no': train_no.strip(),
                            'train_type': train_type.strip(),
                            'departure_time': dep_time.strip(),
                            'arrival_time': arr_time.strip(),
                            'departure_station': start_station,
                            'arrival_station': end_station
                        })
                    except Exception as e:
                        continue
            
            return results
            
        except Exception as e:
            print(f"TRA scrape error: {e}")
            return []
        finally:
            await browser.close()

# Test
if __name__ == "__main__":
    async def test():
        results = await scrape_tra_timetable("台北", "台中")
        print(f"Found {len(results)} trains")
        for r in results:
            print(r)
    
    asyncio.run(test())
