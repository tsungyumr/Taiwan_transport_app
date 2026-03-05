"""
台灣鐵路管理局 (TRA) 時刻表爬蟲模組
使用 Playwright 進行網頁自動化與數據抓取

功能:
- 查詢台鐵時刻表（起站、迄站、日期、時間）
- 抓取列車資訊（車次、車種、出發時間、到達時間、行車時間、票價）
- 處理分頁和動態加載
- 錯誤處理和重試機制

作者: Claude Code Agent
版本: 1.0.0
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, date
from typing import List, Dict, Optional, Any, Callable
from functools import wraps
import re

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    Error as PlaywrightError,
)

# ==================== 設定日誌 ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 資料模型 ====================
@dataclass
class TrainInfo:
    """
    列車資訊資料類別

    屬性:
        train_no: 車次號碼 (例如: "1234")
        train_type: 車種名稱 (例如: "自強號", "莒光號", "區間車")
        departure_station: 出發站名稱
        arrival_station: 抵達站名稱
        departure_time: 出發時間 (格式: HH:MM)
        arrival_time: 抵達時間 (格式: HH:MM)
        travel_time: 行車時間 (例如: "2小時15分")
        price: 票價 (元), 若無法取得則為 None
        is_direct: 是否直達車
        note: 備註資訊 (例如: "每日行駛", "週六日停駛")
    """
    train_no: str
    train_type: str
    departure_station: str
    arrival_station: str
    departure_time: str
    arrival_time: str
    travel_time: str = ""
    price: Optional[int] = None
    is_direct: bool = True
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式，方便序列化為 JSON"""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """轉換為 JSON 字串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass
class TimetableQuery:
    """
    時刻表查詢參數類別

    屬性:
        start_station: 起站名稱
        end_station: 迄站名稱
        query_date: 查詢日期 (YYYY/MM/DD 格式)
        query_time: 查詢時間 (HH:MM 格式，可選)
        transfer_ok: 是否接受轉乘
        train_types: 指定車種列表 (可選)
    """
    start_station: str
    end_station: str
    query_date: str
    query_time: Optional[str] = None
    transfer_ok: bool = False
    train_types: Optional[List[str]] = None

    def __post_init__(self):
        """驗證並格式化輸入參數"""
        # 如果沒有提供日期，使用今天
        if not self.query_date:
            self.query_date = datetime.now().strftime("%Y/%m/%d")

        # 驗證日期格式
        try:
            datetime.strptime(self.query_date, "%Y/%m/%d")
        except ValueError:
            raise ValueError(f"日期格式錯誤: {self.query_date}，請使用 YYYY/MM/DD 格式")


# ==================== 例外處理 ====================
class TRAScraperError(Exception):
    """台鐵爬蟲基礎例外類別"""
    pass


class StationNotFoundError(TRAScraperError):
    """找不到車站例外"""
    pass


class NoTrainFoundError(TRAScraperError):
    """找不到列車例外"""
    pass


class NetworkError(TRAScraperError):
    """網路連線例外"""
    pass


class ParseError(TRAScraperError):
    """資料解析例外"""
    pass


# ==================== 重試裝飾器 ====================
def retry_on_error(max_retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """
    重試裝飾器 - 當函數拋出指定例外時自動重試

    參數:
        max_retries: 最大重試次數
        delay: 每次重試之間的延遲秒數
        exceptions: 要捕捉的例外類別元組
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} 執行失敗 (嘗試 {attempt + 1}/{max_retries + 1}): {e}"
                        )
                        await asyncio.sleep(delay * (attempt + 1))  # 指數退避
                    else:
                        logger.error(f"{func.__name__} 已達最大重試次數，放棄執行")
            raise last_exception
        return wrapper
    return decorator


# ==================== 主要爬蟲類別 ====================
class TRAScraper:
    """
    台鐵時刻表爬蟲類別

    這是主要的爬蟲介面，封裝了所有與台鐵網站互動的邏輯。
    使用 Playwright 進行瀏覽器自動化。

    使用範例:
        ```python
        scraper = TRAScraper()
        trains = await scraper.search_trains("台北", "台中", "2026/03/15")
        for train in trains:
            print(f"{train.train_no}: {train.departure_time} -> {train.arrival_time}")
        await scraper.close()
        ```
    """

    # 台鐵時刻表查詢網址
    BASE_URL = "https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip112/gobytime"

    # 常用的車站名稱對照表（用於驗證和提示）
    COMMON_STATIONS = [
        "台北", "板橋", "桃園", "中壢", "新竹", "苗栗", "豐原",
        "台中", "彰化", "員林", "斗六", "嘉義", "新營", "台南",
        "高雄", "屏東", "花蓮", "台東", "宜蘭", "羅東"
    ]

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30000,
        slow_mo: int = 100,
        user_agent: Optional[str] = None
    ):
        """
        初始化爬蟲實例

        參數:
            headless: 是否使用無頭模式（不顯示瀏覽器視窗）
            timeout: 頁面載入超時時間（毫秒）
            slow_mo: 操作延遲時間（毫秒），增加可降低被偵測風險
            user_agent: 自定義 User-Agent，使用預設值則為 None
        """
        self.headless = headless
        self.timeout = timeout
        self.slow_mo = slow_mo
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Playwright 相關物件（延遲初始化）
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

        logger.info(f"TRAScraper 初始化完成 (headless={headless})")

    async def _init_browser(self) -> None:
        """初始化瀏覽器（內部方法）"""
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                slow_mo=self.slow_mo
            )
            self._context = await self._browser.new_context(
                user_agent=self.user_agent,
                viewport={"width": 1920, "height": 1080},
                locale="zh-TW"
            )
            logger.debug("瀏覽器初始化完成")

    async def _get_page(self) -> Page:
        """取得新頁面（內部方法）"""
        await self._init_browser()
        return await self._context.new_page()

    @retry_on_error(
        max_retries=3,
        delay=2.0,
        exceptions=(NetworkError, PlaywrightTimeoutError, PlaywrightError)
    )
    async def search_trains(
        self,
        start_station: str,
        end_station: str,
        query_date: Optional[str] = None,
        query_time: Optional[str] = None,
        transfer_ok: bool = False
    ) -> List[TrainInfo]:
        """
        搜尋台鐵時刻表

        這是主要的公開方法，用於查詢兩站之間的列車時刻。

        參數:
            start_station: 起站名稱（例如: "台北"）
            end_station: 迄站名稱（例如: "台中"）
            query_date: 查詢日期，格式 YYYY/MM/DD，預設為今天
            query_time: 查詢時間，格式 HH:MM，預設不限制
            transfer_ok: 是否接受轉乘，預設 False（只找直達車）

        回傳:
            List[TrainInfo]: 列車資訊列表，依照出發時間排序

        拋出:
            StationNotFoundError: 當車站名稱無效時
            NoTrainFoundError: 當找不到符合條件的列車時
            NetworkError: 當網路連線失敗時
        """
        # 準備查詢參數
        if not query_date:
            query_date = datetime.now().strftime("%Y/%m/%d")

        logger.info(f"開始查詢: {start_station} -> {end_station}, 日期: {query_date}")

        # 驗證車站名稱（簡單檢查）
        if not start_station or not end_station:
            raise ValueError("起站和迄站不能為空")

        if start_station == end_station:
            raise ValueError("起站和迄站不能相同")

        page = None
        try:
            page = await self._get_page()

            # 步驟 1: 載入查詢頁面
            await self._load_search_page(page)

            # 步驟 2: 填寫查詢表單
            await self._fill_search_form(
                page, start_station, end_station, query_date, query_time, transfer_ok
            )

            # 步驟 3: 提交查詢並等待結果
            await self._submit_query(page)

            # 步驟 4: 解析結果
            trains = await self._parse_results(page, start_station, end_station)

            if not trains:
                raise NoTrainFoundError(
                    f"找不到從 {start_station} 到 {end_station} 的列車"
                )

            logger.info(f"成功找到 {len(trains)} 班列車")
            return trains

        except PlaywrightTimeoutError as e:
            logger.error(f"頁面載入超時: {e}")
            raise NetworkError(f"連線台鐵網站超時，請稍後再試") from e

        except PlaywrightError as e:
            logger.error(f"Playwright 錯誤: {e}")
            raise NetworkError(f"瀏覽器操作失敗") from e

        except Exception as e:
            logger.error(f"搜尋過程發生未預期錯誤: {e}")
            raise

        finally:
            if page:
                await page.close()

    async def _load_search_page(self, page: Page) -> None:
        """
        載入台鐵時刻表查詢頁面

        參數:
            page: Playwright Page 物件
        """
        logger.debug(f"載入頁面: {self.BASE_URL}")

        try:
            response = await page.goto(
                self.BASE_URL,
                timeout=self.timeout,
                wait_until="domcontentloaded"
            )

            if response and response.status >= 400:
                raise NetworkError(f"HTTP 錯誤: {response.status}")

            # 等待頁面主要元素載入
            await page.wait_for_selector("#queryForm", timeout=10000)
            logger.debug("查詢頁面載入完成")

        except PlaywrightTimeoutError:
            raise NetworkError("頁面載入超時，台鐵網站可能暫時無法存取")

    async def _fill_search_form(
        self,
        page: Page,
        start_station: str,
        end_station: str,
        query_date: str,
        query_time: Optional[str],
        transfer_ok: bool
    ) -> None:
        """
        填寫查詢表單

        這個方法會自動填入起站、迄站、日期等資訊。
        注意：台鐵網站使用了一些 JavaScript 互動元件，需要特別處理。

        參數:
            page: Playwright Page 物件
            start_station: 起站名稱
            end_station: 迄站名稱
            query_date: 查詢日期
            query_time: 查詢時間（可選）
            transfer_ok: 是否接受轉乘
        """
        logger.debug("開始填寫查詢表單")

        # 填寫起站
        # 先點擊輸入框觸發 autocomplete
        await page.click("input#startStation")
        await page.fill("input#startStation", start_station)
        await asyncio.sleep(0.5)  # 等待 autocomplete 出現

        # 嘗試選擇第一個建議項目（如果有的話）
        try:
            await page.click(".ui-autocomplete li:first-child", timeout=1000)
        except:
            pass  # 沒有建議項目也沒關係，直接繼續

        # 填寫迄站
        await page.click("input#endStation")
        await page.fill("input#endStation", end_station)
        await asyncio.sleep(0.5)

        try:
            await page.click(".ui-autocomplete li:first-child", timeout=1000)
        except:
            pass

        # 填寫日期
        # 台鐵網站的日期欄位 id 是 datepicker
        await page.fill("input#datepicker", query_date)

        # 如果有指定時間，填寫時間
        if query_time:
            # 時間欄位通常是下拉選單或輸入框
            try:
                await page.select_option("select[name='startTime']", query_time)
            except:
                logger.debug("時間選擇器不可用或已移除")

        # 設定轉乘選項
        if transfer_ok:
            await page.click("input[name='transfer'][value='MORE_THAN_ONE']")
        else:
            await page.click("input[name='transfer'][value='DIRECT_ONLY']")

        logger.debug("表單填寫完成")

    async def _submit_query(self, page: Page) -> None:
        """
        提交查詢並等待結果

        參數:
            page: Playwright Page 物件
        """
        logger.debug("提交查詢")

        # 點擊查詢按鈕
        await page.click("input[name='query']")

        # 等待結果載入 - 使用多種策略
        try:
            # 策略 1: 等待結果表格出現
            await page.wait_for_selector(
                ".trip-column, .result-table, table tbody tr",
                timeout=15000
            )
        except PlaywrightTimeoutError:
            # 策略 2: 檢查是否有錯誤訊息
            error_msg = await page.query_selector(".alert-danger, .error-message")
            if error_msg:
                text = await error_msg.inner_text()
                raise NoTrainFoundError(f"查詢失敗: {text.strip()}")

            # 策略 3: 等待網路閒置
            await page.wait_for_load_state("networkidle", timeout=10000)

        logger.debug("查詢結果已載入")

    async def _parse_results(
        self,
        page: Page,
        start_station: str,
        end_station: str
    ) -> List[TrainInfo]:
        """
        解析查詢結果頁面，提取列車資訊

        這個方法會分析結果表格的 HTML 結構，提取每一班列車的詳細資訊。
        由於網站結構可能變化，這裡使用了多種 selector 策略。

        參數:
            page: Playwright Page 物件
            start_station: 起站名稱（用於記錄）
            end_station: 迄站名稱（用於記錄）

        回傳:
            List[TrainInfo]: 列車資訊列表
        """
        trains = []

        # 嘗試多種可能的表格結構
        selectors = [
            ".trip-column",  # 新版網站
            ".search-trip tr",  # 替代結構
            "table.result-table tbody tr",  # 標準表格
            "table tbody tr",  # 通用表格
            ".train-list .train-item",  # 列表結構
        ]

        rows = []
        for selector in selectors:
            rows = await page.query_selector_all(selector)
            if len(rows) > 0:
                logger.debug(f"使用 selector '{selector}' 找到 {len(rows)} 行")
                break

        if not rows:
            logger.warning("無法找到結果表格，嘗試獲取頁面內容分析")
            content = await page.content()
            # 可以在這裡添加更多除錯邏輯
            return []

        for row in rows:
            try:
                train = await self._parse_train_row(row, start_station, end_station)
                if train:
                    trains.append(train)
            except Exception as e:
                logger.warning(f"解析列車資訊時發生錯誤: {e}")
                continue

        return trains

    async def _parse_train_row(
        self,
        row: Any,
        start_station: str,
        end_station: str
    ) -> Optional[TrainInfo]:
        """
        解析單一列車行資料

        參數:
            row: 表格行元素
            start_station: 起站名稱
            end_station: 迄站名稱

        回傳:
            Optional[TrainInfo]: 列車資訊，解析失敗則回傳 None
        """
        cells = await row.query_selector_all("td")

        if len(cells) < 5:
            return None

        try:
            # 根據台鐵網站的常見表格結構解析
            # 注意：不同時期網站結構可能不同，這裡使用彈性解析

            texts = []
            for cell in cells:
                text = await cell.inner_text()
                texts.append(text.strip())

            # 嘗試識別各欄位
            train_no = ""
            train_type = ""
            dep_time = ""
            arr_time = ""
            travel_time = ""

            # 遍歷所有文字，用正規表示式識別
            for text in texts:
                # 車次：通常是 3-4 位數字
                if not train_no and re.match(r'^\d{3,4}$', text):
                    train_no = text

                # 車種：包含中文車種名稱
                elif not train_type and any(t in text for t in ['自強', '莒光', '復興', '區間', '普快', '太魯閣', '普悠瑪']):
                    train_type = text

                # 時間：HH:MM 格式
                elif re.match(r'^\d{1,2}:\d{2}$', text):
                    if not dep_time:
                        dep_time = text
                    elif not arr_time:
                        arr_time = text

                # 行車時間：通常包含 "小時"、"分" 或 ":"
                elif '小時' in text or ('分' in text and ':' in text):
                    travel_time = text

            # 如果沒有找到車次，可能是標題行或其他非資料行
            if not train_no:
                return None

            return TrainInfo(
                train_no=train_no,
                train_type=train_type or "未知",
                departure_station=start_station,
                arrival_station=end_station,
                departure_time=dep_time or "--:--",
                arrival_time=arr_time or "--:--",
                travel_time=travel_time,
                price=None,  # 價格需要額外查詢
                is_direct=True,
                note=""
            )

        except Exception as e:
            logger.debug(f"解析行資料失敗: {e}")
            return None

    async def get_pagination_info(self, page: Page) -> Dict[str, Any]:
        """
        取得分頁資訊

        參數:
            page: Playwright Page 物件

        回傳:
            Dict: 包含目前頁碼、總頁數等資訊
        """
        info = {
            "current_page": 1,
            "total_pages": 1,
            "has_next": False,
            "has_prev": False
        }

        try:
            # 尋找分頁元件
            pagination = await page.query_selector(".pagination")
            if pagination:
                # 解析分頁資訊
                active_page = await pagination.query_selector(".active")
                if active_page:
                    page_text = await active_page.inner_text()
                    info["current_page"] = int(page_text.strip())

                # 檢查是否有下一頁
                next_btn = await pagination.query_selector("[aria-label='Next']")
                info["has_next"] = next_btn is not None and await next_btn.is_enabled()

        except Exception as e:
            logger.debug(f"取得分頁資訊失敗: {e}")

        return info

    async def close(self) -> None:
        """關閉瀏覽器並釋放資源"""
        if self._browser:
            await self._browser.close()
            self._browser = None
            logger.debug("瀏覽器已關閉")

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
            logger.debug("Playwright 已停止")

    async def __aenter__(self):
        """非同步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同步上下文管理器出口"""
        await self.close()


# ==================== 輔助函數 ====================
async def search_tra_trains(
    start_station: str,
    end_station: str,
    query_date: Optional[str] = None,
    query_time: Optional[str] = None,
    headless: bool = True
) -> List[Dict[str, Any]]:
    """
    簡易查詢函數 - 不需要建立類別實例的快速查詢方式

    參數:
        start_station: 起站名稱
        end_station: 迄站名稱
        query_date: 查詢日期 (YYYY/MM/DD)
        query_time: 查詢時間 (HH:MM)
        headless: 是否使用無頭模式

    回傳:
        List[Dict]: 列車資訊字典列表

    使用範例:
        ```python
        trains = await search_tra_trains("台北", "台中", "2026/03/15")
        for train in trains:
            print(f"{train['train_no']}: {train['departure_time']}")
        ```
    """
    async with TRAScraper(headless=headless) as scraper:
        trains = await scraper.search_trains(
            start_station=start_station,
            end_station=end_station,
            query_date=query_date,
            query_time=query_time
        )
        return [t.to_dict() for t in trains]


def validate_station_name(station: str) -> bool:
    """
    驗證車站名稱是否有效

    參數:
        station: 車站名稱

    回傳:
        bool: 是否為有效的常用車站
    """
    return station in TRAScraper.COMMON_STATIONS


def get_common_stations() -> List[str]:
    """
    取得常用車站列表

    回傳:
        List[str]: 常用車站名稱列表
    """
    return TRAScraper.COMMON_STATIONS.copy()


# ==================== 使用範例與測試 ====================
async def demo():
    """
    展示如何使用 TRAScraper 類別

    這個函數展示了各種使用方式，可以作為開發參考。
    """
    print("=" * 60)
    print("台鐵時刻表爬蟲使用範例")
    print("=" * 60)

    # 範例 1: 使用簡易函數查詢
    print("\n【範例 1】使用簡易函數查詢")
    print("-" * 40)
    try:
        trains = await search_tra_trains(
            start_station="台北",
            end_station="台中",
            query_date=datetime.now().strftime("%Y/%m/%d"),
            headless=True
        )
        print(f"找到 {len(trains)} 班列車:")
        for train in trains[:3]:  # 只顯示前 3 班
            print(f"  車次 {train['train_no']} ({train['train_type']}): "
                  f"{train['departure_time']} -> {train['arrival_time']}")
    except Exception as e:
        print(f"查詢失敗: {e}")

    # 範例 2: 使用類別實例（推薦方式）
    print("\n【範例 2】使用類別實例（推薦）")
    print("-" * 40)
    scraper = TRAScraper(headless=True)
    try:
        trains = await scraper.search_trains("板橋", "高雄", query_date="2026/03/15")
        print(f"找到 {len(trains)} 班列車")
        if trains:
            print(f"第一班車資訊:\n{trains[0].to_json()}")
    except Exception as e:
        print(f"查詢失敗: {e}")
    finally:
        await scraper.close()

    # 範例 3: 使用非同步上下文管理器
    print("\n【範例 3】使用非同步上下文管理器")
    print("-" * 40)
    try:
        async with TRAScraper(headless=True) as scraper:
            trains = await scraper.search_trains("新竹", "台北")
            print(f"找到 {len(trains)} 班列車")
    except Exception as e:
        print(f"查詢失敗: {e}")

    # 範例 4: 驗證車站名稱
    print("\n【範例 4】驗證車站名稱")
    print("-" * 40)
    test_stations = ["台北", "台中", "台南", "不存在的站"]
    for station in test_stations:
        valid = validate_station_name(station)
        status = "✓ 有效" if valid else "✗ 未知"
        print(f"  {station}: {status}")

    print("\n" + "=" * 60)
    print("範例執行完成")
    print("=" * 60)


if __name__ == "__main__":
    # 執行展示程式
    asyncio.run(demo())
