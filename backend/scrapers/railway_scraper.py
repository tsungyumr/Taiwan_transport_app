"""
台灣鐵路 (TRA) 爬蟲模組

這個模組負責抓取台鐵的火車時刻表資訊。
台鐵是台灣最主要的鐵路系統，覆蓋全台各地。

使用 Playwright 來模擬瀏覽器操作，因為台鐵網站有動態生成的內容。
就像請一位助手幫你打開瀏覽器、填表單、看結果。
"""

from playwright.async_api import Browser
from typing import List, Optional
from datetime import datetime
from .base_scraper import BaseScraper
from models.railway_models import TrainTimeEntry


class TaiwanRailwayScraper(BaseScraper):
    """
    台灣鐵路爬蟲

    提供查詢台鐵時刻表的功能，包含所有主要車站。

    台鐵站點代碼說明：
    - 1xx = 西部干線 (基隆-屏東)
    - 2xx = 西部干線山線 (苗栗-彰化)
    - 270-278 = 西部干線 (高雄-屏東)
    - 280-289 = 南迴線 (屏東-台東)
    - 3xx = 東部干線 (花蓮-台東)
    - 4xx = 宜蘭線 (八堵-蘇澳)
    - 5xx = 北迴線 (花蓮-蘇澳)
    - 7xx = 支線 (內灣/六家/沙崙)

    使用方式：
        scraper = TaiwanRailwayScraper(browser)
        results = await scraper.search_timetable("台北", "台中", "2024/03/15")
    """

    # 台鐵所有車站的代碼對照表
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

    # 反向對照：站名 → 代碼
    STATION_NAMES = {v: k for k, v in STATIONS.items()}

    def __init__(self, browser: Optional[Browser] = None):
        """
        初始化台鐵爬蟲

        Args:
            browser: Playwright Browser 實例，如果為 None 則使用 mock 資料
        """
        super().__init__("TaiwanRailwayScraper")
        self.browser = browser

    async def search_timetable(
        self,
        from_station: str,
        to_station: str,
        date: Optional[str] = None,
        time: Optional[str] = None
    ) -> List[TrainTimeEntry]:
        """
        查詢台鐵時刻表

        優先使用 Playwright 爬取真實資料，如果失敗則回退到模擬資料。

        Args:
            from_station: 出發站名稱或代碼
            to_station: 抵達站名稱或代碼
            date: 日期 (YYYY/MM/DD)
            time: 時間 (HH:MM)

        Returns:
            List[TrainTimeEntry]: 火車班次列表
        """
        ride_date = date or datetime.now().strftime("%Y/%m/%d")

        # 嘗試使用 Playwright 爬取
        if self.browser:
            try:
                results = await self._scrape_with_playwright(from_station, to_station, ride_date)
                if results:
                    self.logger.info(f"✅ 從 Playwright 取得 {len(results)} 筆台鐵資料")
                    return results
            except Exception as e:
                self.logger.warning(f"⚠️ Playwright 爬取失敗: {e}")

        # 回退到模擬資料
        self.logger.info("📝 使用模擬資料")
        return self._get_mock_data(from_station, to_station)

    async def _scrape_with_playwright(self, from_station: str, to_station: str, ride_date: str) -> List[TrainTimeEntry]:
        """
        使用 Playwright 爬取台鐵時刻表

        這個方法會開啟瀏覽器，訪問台鐵網站，填入查詢條件，然後解析結果。
        """
        if not self.browser:
            raise Exception("Browser 未初始化")

        context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        try:
            # 訪問台鐵訂票頁面
            await page.goto(
                "https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip112/gobytime",
                timeout=30000
            )
            await page.wait_for_load_state("domcontentloaded")

            # 等待表單載入
            await page.wait_for_selector('input[name="startStation"]', timeout=10000)

            # 轉換站名為代碼
            from_code = from_station if from_station.isdigit() else self.STATION_NAMES.get(from_station, from_station)
            to_code = to_station if to_station.isdigit() else self.STATION_NAMES.get(to_station, to_station)

            from_name = self.STATIONS.get(from_code, from_station)
            to_name = self.STATIONS.get(to_code, to_station)

            # 填入表單（使用 JavaScript 直接設定值）
            await page.evaluate(f"""
                document.querySelector('input[name="startStation"]').value = '{from_name}';
                document.querySelector('input[name="endStation"]').value = '{to_name}';
            """)

            # 填入日期
            await page.fill('input[name="rideDate"]', ride_date)

            # 點擊查詢按鈕
            await page.click('input[value="查詢"]')

            # 等待結果載入
            await page.wait_for_load_state("networkidle", timeout=20000)

            # 解析結果表格
            return await self._parse_results(page, from_name, to_name)

        except Exception as e:
            self.logger.error(f"爬取過程發生錯誤: {e}")
            raise
        finally:
            await context.close()

    async def _parse_results(self, page, from_name: str, to_name: str) -> List[TrainTimeEntry]:
        """
        解析台鐵查詢結果頁面的表格

        嘗試多種可能的表格選擇器，因為網站結構可能會改變。
        """
        results = []

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

        # 如果都找不到，嘗試找所有表格
        if not rows:
            all_tables = await page.query_selector_all('table')
            for table in all_tables:
                rows = await table.query_selector_all('tr')
                if len(rows) > 2:
                    break

        # 解析每一列資料
        for row in rows[:20]:  # 限制最多 20 筆
            cells = await row.query_selector_all('td')
            if len(cells) >= 6:
                try:
                    cell_texts = [await cell.inner_text() for cell in cells]
                    cell_texts = [t.strip() for t in cell_texts]

                    if len(cell_texts) >= 6:
                        train_no = cell_texts[1] if cell_texts[1] else cell_texts[0]
                        train_type = cell_texts[2] if len(cell_texts) > 2 else "自強"
                        dep_time = cell_texts[3] if len(cell_texts) > 3 else ""
                        arr_time = cell_texts[5] if len(cell_texts) > 5 else ""

                        duration = self._calculate_duration(dep_time, arr_time)

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
                except Exception:
                    continue

        return results

    def _get_mock_data(self, from_station: str, to_station: str) -> List[TrainTimeEntry]:
        """
        產生模擬的台鐵時刻表資料

        當真實爬蟲不可用時，產生合理的模擬資料。
        根據兩站之間的距離估算行車時間。
        """
        from_name = self.STATIONS.get(from_station, from_station)
        to_name = self.STATIONS.get(to_station, to_station)

        # 計算兩站代碼差距來估算行車時間
        from_code = int(from_station) if from_station.isdigit() else 100
        to_code = int(to_station) if to_station.isdigit() else 200
        diff = abs(to_code - from_code)

        train_types = ["自強", "區間車", "莒光", "太魯閣", "普悠瑪"]

        entries = []
        base_times = [
            "06:00", "06:30", "07:00", "07:30", "08:00", "08:30", "09:00",
            "10:00", "11:00", "12:00", "13:00", "14:00", "15:00",
            "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00"
        ]

        for i, base_time in enumerate(base_times):
            hour, minute = map(int, base_time.split(':'))
            duration_minutes = diff * 3 + 10  # 簡單估算：每站 3 分鐘 + 基礎時間

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
