import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

async def test_submit():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Headless false to debug
        page = await browser.new_page()
        await page.goto("https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip112/gobytime")
        
        # Screenshot before
        await page.screenshot(path="before_submit.png")
        
        # Fill
        await page.fill('input[name="startStation"]', "台北")
        await page.wait_for_timeout(1000)
        await page.fill('input[name="endStation"]', "台中")
        await page.fill('input[name="rideDate"]', "2026/02/28")
        
        # Click query
        await page.click('input[value="查詢"]')
        await page.wait_for_load_state("networkidle")
        
        # Screenshot after
        await page.screenshot(path="after_submit.png")
        
        # Try to find results
        tables = page.query_selector_all("table")
        print(f"Found {len(await tables)} tables")
        
        content = await page.content()
        with open("page_content.html", "w") as f:
            f.write(content)
        print("Page content saved to page_content.html")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_submit())
