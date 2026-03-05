"""
Playwright 爬蟲測試腳本 - 探索網站結構
"""
import asyncio
from playwright.async_api import async_playwright

async def test_ebus():
    """測試大台北公車網站"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # 訪問公車網站
            await page.goto("https://ebus.gov.taipei/ebus", timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)
            
            # 獲取頁面標題
            title = await page.title()
            print(f"Page title: {title}")
            
            # 嘗試獲取頁面內容
            content = await page.content()
            print(f"Content length: {len(content)}")
            
            # 查找表單或輸入元素
            inputs = await page.query_selector_all("input")
            print(f"Found {len(inputs)} input elements")
            
            # 查找按鈕
            buttons = await page.query_selector_all("button")
            print(f"Found {len(buttons)} button elements")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

async def test_thsrc():
    """測試高鐵網站"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto("https://www.thsrc.com.tw", timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)
            
            title = await page.title()
            print(f"THSR Page title: {title}")
            
            content = await page.content()
            print(f"Content length: {len(content)}")
            
            # 查找常見元素
            elements = await page.query_selector_all("a, button, input")
            print(f"Found {len(elements)} interactive elements")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

async def test_railway():
    """測試台鐵網站"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto("https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip112/gobytime", timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)
            
            title = await page.title()
            print(f"Railway Page title: {title}")
            
            content = await page.content()
            print(f"Content length: {len(content)}")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    print("=== Testing eBus ===")
    asyncio.run(test_ebus())
    print("\n=== Testing THSR ===")
    asyncio.run(test_thsrc())
    print("\n=== Testing Railway ===")
    asyncio.run(test_railway())
