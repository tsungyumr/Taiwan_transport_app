import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

async def test_tra_scrape(from_name="台北", to_name="台中", date=None):
    date = date or datetime.now().strftime("%Y/%m/%d")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip112/gobytime")
        await page.wait_for_load_state("networkidle")
        
        # Fill form
        await page.fill('input[name="startStation"]', from_name)
        await page.fill('input[name="endStation"]', to_name)
        await page.fill('input[name="rideDate"]', date)
        await page.click('input[name="query"]')
        
        # Wait for results
        await page.wait_for_selector('table tbody tr', timeout=10000)
        
        # Extract
        rows = await page.query_selector_all('table tbody tr')
        results = []
        for row in rows[:10]:  # first 10
            cells = await row.query_selector_all('td')
            if len(cells) >= 7:
                try:
                    train_no = await cells[1].inner_text()
                    train_type = await cells[2].inner_text()
                    dep_time = await cells[3].inner_text()
                    arr_time = await cells[5].inner_text()
                    results.append({
                        'train_no': train_no.strip(),
                        'train_type': train_type.strip(),
                        'dep_time': dep_time.strip(),
                        'arr_time': arr_time.strip()
                    })
                except:
                    pass
        await browser.close()
        print(f"Found {len(results)} trains from {from_name} to {to_name}")
        for r in results:
            print(r)

if __name__ == "__main__":
    asyncio.run(test_tra_scrape())
