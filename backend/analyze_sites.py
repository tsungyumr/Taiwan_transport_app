# Playwright 網站元素分析腳本
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def analyze_page(url, name):
    print(f"\n=== {name} ({url}) ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(5000)  # Wait for JS

            # Get page content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')

            print("Title:", await page.title())

            # Forms
            forms = soup.find_all('form')
            print(f"Forms found: {len(forms)}")
            for i, form in enumerate(forms[:3]):
                action = form.get('action', 'N/A')
                method = form.get('method', 'N/A')
                print(f"  Form {i}: action={action}, method={method}")
                inputs = form.find_all(['input', 'select'])
                for inp in inputs:
                    inp_type = inp.get('type', inp.name)
                    name = inp.get('name', 'N/A')
                    id_ = inp.get('id', 'N/A')
                    print(f"    {inp_type}: name={name}, id={id_}")

            # Selectors for stations - properly await
            selects = await page.query_selector_all("select")
            print(f"Select elements: {len(selects)}")

            # Buttons
            buttons = await page.query_selector_all("button, input[type=button], input[type=submit]")
            print(f"Buttons: {len(buttons)}")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

async def analyze_stations():
    print("\n=== 台鐵站點分析 ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        try:
            await page.goto("https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip112/gobytime", timeout=30000)
            await page.wait_for_load_state("domcontentloaded")

            # 分析站點選擇器
            start_select = await page.query_selector('select[name="startStation"]')
            if start_select:
                options = await start_select.query_selector_all('option')
                station_names = []
                for option in options[:10]:  # 只取前幾個
                    value = await option.get_attribute('value')
                    text = await option.inner_text()
                    station_names.append(f"{value}: {text}")

                print(f"\nFound {len(options)} station options:")
                for name in station_names:
                    print(f"  {name}")

            # 分析其他站點相關元素
            inputs = await page.query_selector_all('input')
            print(f"\nFound {len(inputs)} input elements:")
            for i, inp in enumerate(inputs[:5]):
                type_ = await inp.get_attribute('type') or "N/A"
                name = await inp.get_attribute('name') or "N/A"
                print(f"  Input {i}: type={type_}, name={name}")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

async def main():
    await analyze_page("https://ebus.gov.taipei/ebus", "eBus")
    await analyze_page("https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip112/gobytime", "TRA")
    await analyze_page("https://www.thsrc.com.tw", "THSR")
    await analyze_stations()

if __name__ == "__main__":
    asyncio.run(main())
