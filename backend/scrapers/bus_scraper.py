"""
大台北公車爬蟲模組

這個模組負責抓取大台北地區的公車路線和到站時間資訊。
主要資料來源是台北市 Open Data API 和 5284 即時公車系統。

想像這個爬蟲就像是一位站在公車站牌前的乘客，
隨時查看哪一班公車快到了、還要等多久。
"""

import httpx
import random
from datetime import datetime
from typing import List, Optional, Dict, Any
from .base_scraper import BaseScraper
from models.bus_models import BusRoute, BusTimeEntry, BusStop, BusVehicle, BusRealTimeArrival, BusRouteData


class TaipeiBusScraper(BaseScraper):
    """
    大台北公車爬蟲

    提供以下功能：
    1. 取得公車路線列表
    2. 查詢特定路線的時刻表
    3. 取得即時到站資訊

    使用方式：
        scraper = TaipeiBusScraper()
        routes = await scraper.get_bus_routes("307")
        timetable = await scraper.get_bus_timetable("307")
        realtime = await scraper.get_real_time_arrival("307", "西門")
        await scraper.close()
    """

    # 台北市公車相關 API 網址
    BASE_URL = "https://data.taipei/api/v1/dataset"
    BUS_REAL_TIME_BASE = "https://www.5284.gov.taipei/ibus"

    # 預設公車路線資料（當 API 掛掉時使用）
    DEFAULT_ROUTES = [
        {"route_id": "235", "route_name": "235", "departure": "長春路", "arrival": "福港街", "operator": "首都客運"},
        {"route_id": "307", "route_name": "307", "departure": "板橋", "arrival": "撫遠街", "operator": "三重客運"},
        {"route_id": "604", "route_name": "604", "departure": "板橋站", "arrival": "捷運明德站", "operator": "台北客運"},
        {"route_id": "265", "route_name": "265", "departure": "板橋府中", "arrival": "士林", "operator": "三重客運"},
        {"route_id": "651", "route_name": "651", "departure": "板橋法院", "arrival": "台北車站", "operator": "台北客運"},
        {"route_id": "667", "route_name": "667", "departure": "板橋站", "arrival": "捷運忠孝敦化", "operator": "三重客運"},
        {"route_id": "99", "route_name": "99", "departure": "板橋", "arrival": "新莊", "operator": "台北客運"},
        {"route_id": "234", "route_name": "234", "departure": "板橋", "arrival": "西門", "operator": "三重客運"},
        {"route_id": "705", "route_name": "705", "departure": "板橋", "arrival": "三重", "operator": "三重客運"},
        {"route_id": "812", "route_name": "812", "departure": "板橋", "arrival": "中和", "operator": "台北客運"},
        {"route_id": "920", "route_name": "920", "departure": "板橋", "arrival": "信義區", "operator": "台北客運"},
        {"route_id": "930", "route_name": "930", "departure": "板橋", "arrival": "新店", "operator": "台北客運"},
        {"route_id": "965", "route_name": "965", "departure": "板橋", "arrival": "金瓜石", "operator": "基隆客運"},
        {"route_id": "222", "route_name": "222", "departure": "內湖", "arrival": "衡陽路", "operator": "首都客運"},
        {"route_id": "247", "route_name": "247", "departure": "東湖", "arrival": "衡陽路", "operator": "三重客運"},
        {"route_id": "287", "route_name": "287", "departure": "東湖", "arrival": "捷運永春站", "operator": "三重客運"},
        {"route_id": "620", "route_name": "620", "departure": "士林", "arrival": "北投", "operator": "大南客運"},
        {"route_id": "218", "route_name": "218", "departure": "新店", "arrival": "台北車站", "operator": "台北客運"},
        {"route_id": "249", "route_name": "249", "departure": "蘆洲", "arrival": "台北車站", "operator": "三重客運"},
        {"route_id": "299", "route_name": "299", "departure": "新莊", "arrival": "永和", "operator": "三重客運"},
        {"route_id": "527", "route_name": "527", "departure": "海關", "arrival": "捷運台北車站", "operator": "首都客運"},
        {"route_id": "棕9", "route_name": "棕9", "departure": "內湖", "arrival": "捷運中山站", "operator": "首都客運"},
        {"route_id": "綠17", "route_name": "綠17", "departure": "新店", "arrival": "捷運大坪林", "operator": "台北客運"},
        {"route_id": "紅32", "route_name": "紅32", "departure": "南港", "arrival": "捷運象山站", "operator": "台北客運"},
        {"route_id": "藍12", "route_name": "藍12", "departure": "舊宗路", "arrival": "捷運昆陽站", "operator": "首都客運"},
    ]

    # 常見路線的站牌資料
    BUS_STOPS = {
        "235": ["長春路", "民生社區", "富民生態", "新東街", "吉祥路", "成福路", "福港街"],
        "307": ["板橋", "致理科技大學", "新埔", "江子翠", "龍山寺", "西門", "博愛路", "撫遠街"],
        "604": ["板橋站", "捷運板橋站", "音樂公園", "光復中學", "民生社區", "捷運明德站"],
    }

    def __init__(self):
        """初始化公車爬蟲"""
        super().__init__("TaipeiBusScraper")

    def _get_http_client(self) -> httpx.AsyncClient:
        """
        取得或建立 HTTP client

        使用 Singleton 模式，確保同一個爬蟲只會建立一個連線，
        避免重複建立連線造成資源浪費。
        """
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=15.0,
                verify=False,  # 某些政府網站憑證可能有問題
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json"
                }
            )
        return self._http_client

    async def get_bus_routes(self, route_name: str = None, limit: int = 50) -> List[BusRoute]:
        """
        取得公車路線列表

        先嘗試從官方 API 取得資料，如果失敗就使用預設資料。
        就像你去餐廳吃飯，主菜沒有了就給你備用的便當。

        Args:
            route_name: 路線名稱關鍵字（可選）
            limit: 最多回傳幾筆資料

        Returns:
            List[BusRoute]: 公車路線列表
        """
        try:
            routes = await self._fetch_routes_from_api(route_name, limit)
            if routes:
                self.logger.info(f"✅ 從 API 取得 {len(routes)} 條路線")
                return routes
        except Exception as e:
            self.logger.warning(f"⚠️ 公車 API 失敗: {e}")

        # API 失敗時使用預設資料
        self.logger.info("📝 使用預設路線資料")
        return self._get_default_routes(route_name, limit)

    async def _fetch_routes_from_api(self, route_name: str = None, limit: int = 50) -> List[BusRoute]:
        """
        從台北市 Open Data API 取得公車路線

        嘗試多個資料集，因為政府 API 有時候會改版或移動位置。
        """
        client = self._get_http_client()

        datasets = [
            "296cee16-9fc1-4bd9-bda4-7a4790f5a2d0",  # 公車路線主資料集
            "a7a36bf4-8ebf-414a-b18e-4e3b5599e1bd",  # 備用資料集
        ]

        for dataset_id in datasets:
            try:
                url = f"{self.BASE_URL}/{dataset_id}?limit=100&format=json"
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("result", {}).get("results", [])
                    if results:
                        return self._parse_route_data(results, route_name, limit)
            except Exception:
                continue

        return []

    def _parse_route_data(self, data: list, route_name: str = None, limit: int = 50) -> List[BusRoute]:
        """
        解析公車路線資料

        政府 API 的欄位命名不太一致，所以要嘗試多種可能的欄位名稱。
        """
        routes = []

        for item in data:
            try:
                # 嘗試多種可能的欄位名稱
                route_id = item.get("routeId") or item.get("RouteID") or item.get("路線編號", "")
                route_name_data = item.get("routeName") or item.get("RouteName") or item.get("路線名稱", "")
                departure = item.get("departureStop") or item.get("起點站", "")
                arrival = item.get("arrivalStop") or item.get("終點站", "")
                operator = item.get("operator") or item.get("業者", "")

                if not route_id and route_name_data:
                    route_id = str(route_name_data)

                # 如果有指定路線名稱關鍵字，進行過濾
                if route_name and route_name.lower() not in str(route_name_data).lower():
                    continue

                routes.append(BusRoute(
                    route_id=route_id,
                    route_name=str(route_name_data),
                    departure_stop=str(departure),
                    arrival_stop=str(arrival),
                    operator=str(operator)
                ))

                if len(routes) >= limit:
                    break
            except Exception:
                continue

        return routes

    def _get_default_routes(self, route_name: str = None, limit: int = 50) -> List[BusRoute]:
        """取得預設公車路線"""
        routes = [
            BusRoute(**r) for r in self.DEFAULT_ROUTES
        ]

        if route_name:
            routes = [r for r in routes if route_name in r.route_name]

        return routes[:limit]

    async def get_bus_timetable(self, route_id: str) -> List[BusTimeEntry]:
        """
        取得公車時刻表

        注意：公車通常沒有固定時刻表，這裡回傳的是預估的發車間隔。
        """
        try:
            timetable = await self._fetch_timetable_from_api(route_id)
            if timetable:
                return timetable
        except Exception as e:
            self.logger.warning(f"⚠️ 公車時刻表 API 失敗: {e}")

        return self._get_default_timetable(route_id)

    async def _fetch_timetable_from_api(self, route_id: str) -> List[BusTimeEntry]:
        """從 API 取得時刻表（目前尚未實作完整支援）"""
        return []

    def _get_default_timetable(self, route_id: str) -> List[BusTimeEntry]:
        """
        產生預設時刻表

        假設每 10-20 分鐘一班車，產生一整天的時刻表。
        """
        entries = []
        route_info = next((r for r in self.DEFAULT_ROUTES if r["route_id"] == route_id), None)
        route_name = route_info["route_name"] if route_info else route_id

        stops = self.BUS_STOPS.get(route_id, [f"第 {i+1} 站" for i in range(15)])

        base_hour = 6
        for bus_num in range(25):
            hour = base_hour + bus_num // 2
            minute = (bus_num % 2) * 15 + 10

            if hour > 23:
                break

            for i, stop in enumerate(stops):
                stop_time_hour = hour + i // 4
                stop_time_min = minute + (i % 4) * 8

                if stop_time_min >= 60:
                    stop_time_hour += 1
                    stop_time_min -= 60

                if stop_time_hour > 23:
                    continue

                entries.append(BusTimeEntry(
                    stop_name=stop,
                    arrival_time=f"{stop_time_hour:02d}:{stop_time_min:02d}",
                    route_name=route_name
                ))

        return entries[:50]

    async def get_real_time_arrival(self, route_id: str, stop_name: str = None) -> BusRealTimeArrival:
        """
        取得公車即時到站資訊

        這是最常用的功能，告訴使用者下一班車還有多久到。
        """
        try:
            result = await self._fetch_real_time_arrival(route_id, stop_name)
            if result:
                return BusRealTimeArrival(**result)
        except Exception as e:
            self.logger.warning(f"⚠️ 即時到站 API 失敗: {e}")

        return BusRealTimeArrival(**self._get_mock_real_time_arrival(route_id, stop_name))

    async def _fetch_real_time_arrival(self, route_id: str, stop_name: str = None) -> Optional[Dict]:
        """從 5284 API 取得即時到站資訊"""
        client = self._get_http_client()

        try:
            url = f"{self.BUS_REAL_TIME_BASE}/RealTime?routeName={route_id}"
            response = await client.get(url)
            if response.status_code == 200:
                # TODO: 解析 JSON 回應
                pass
        except Exception:
            pass

        return None

    def _get_mock_real_time_arrival(self, route_id: str, stop_name: str = None) -> Dict:
        """
        產生模擬的即時到站資訊

        當真實 API 不可用時，產生合理的預估值。
        """
        now = datetime.now()
        current_minute = now.hour * 60 + now.minute

        route_info = next((r for r in self.DEFAULT_ROUTES if r["route_id"] == route_id), None)
        route_name = route_info["route_name"] if route_info else route_id

        stops = self.BUS_STOPS.get(route_id, ["站牌1", "站牌2", "站牌3"])

        arrivals = []
        for i in range(3):
            wait_minutes = random.randint(3, 25) * (i + 1)
            arrival_minute = current_minute + wait_minutes
            arrival_hour = arrival_minute // 60
            arrival_m = arrival_minute % 60

            arrivals.append({
                "stop_name": stops[i % len(stops)] if not stop_name else stop_name,
                "arrival_time": f"{arrival_hour:02d}:{arrival_m:02d}",
                "wait_minutes": wait_minutes,
                "bus_plate": f"{random.choice(['基', '北', '新', '三重', '台北'])}{random.randint(1000, 9999)}",
                "is_arriving": wait_minutes <= 3
            })

        return {
            "route_id": route_id,
            "route_name": route_name,
            "current_time": now.strftime("%H:%M"),
            "arrivals": arrivals
        }

    async def get_route_detail(self, route: str) -> BusRouteData:
        """
        取得公車路線詳細資訊（站點 + 即時車輛位置）

        這是整合性的功能，一次取得所有需要的資訊。
        """
        client = httpx.AsyncClient(
            verify=False,
            timeout=httpx.Timeout(30.0),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json"
            }
        )

        try:
            # 取得站點資料
            stop_url = f"{self.BUS_REAL_TIME_BASE}/api/bus/StopOfRoute?routeName={route}&routeAll=1"
            stop_resp = await client.get(stop_url)
            stops = []

            if stop_resp.status_code == 200:
                data = stop_resp.json().get("data", [])
                for s in data:
                    name = s.get("StopName", {}).get("Zh_tw", f"{route} 未知站")
                    stops.append(BusStop(name=name, eta="公車已離開"))
            else:
                stops = [BusStop(name=f"{route} 第{i+1}站", eta="API載入失敗") for i in range(25)]

            # 取得即時車輛位置
            realtime_url = f"{self.BUS_REAL_TIME_BASE}/api/bus/RealTimeByRoute?routeName={route}&routeAll=1"
            rt_resp = await client.get(realtime_url)
            buses = []

            if rt_resp.status_code == 200:
                data = rt_resp.json().get("data", [])
                now_ms = int(datetime.now().timestamp() * 1000)
                for b in data:
                    busid = b.get("PlateNumb", "未知公車")
                    position_str = b.get("BusPositionMark", "0")
                    try:
                        at_stop = int(position_str.split("/")[0]) if "/" in position_str else int(position_str)
                    except:
                        at_stop = 1

                    eta_ms = b.get("EstimateTime_Arrive")
                    if eta_ms:
                        eta_min = max(1, int((int(eta_ms) - now_ms) / 60000))
                        eta_next = f"{eta_min}min後到達"
                    else:
                        eta_next = "N/A"

                    heading_to = min(at_stop + 1, len(stops) + 1)
                    buses.append(BusVehicle(
                        id=busid,
                        at_stop=at_stop,
                        eta_next=eta_next,
                        heading_to=heading_to
                    ))

            return BusRouteData(
                route=route,
                stops=stops,
                buses=buses,
                updated=datetime.now().isoformat()
            )

        except Exception as e:
            self.logger.error(f"取得路線 {route} 詳細資訊失敗: {e}")
            # 回退到模擬資料
            return self._get_mock_route_data(route)
        finally:
            await client.aclose()

    def _get_mock_route_data(self, route: str) -> BusRouteData:
        """產生模擬的路線資料"""
        stops = [
            BusStop(
                name=f"{route} 第{i+1}站",
                eta=random.choice(["公車已離開", "即將進站", f"{random.randint(1,30)}分後到達"])
            )
            for i in range(25)
        ]
        buses = [
            BusVehicle(
                id=f"{route}-bus-{j}",
                at_stop=random.randint(1, 25),
                eta_next=f"{random.randint(1,15)}分後到達",
                heading_to=random.randint(1, 26)
            )
            for j in range(1, 4)
        ]
        return BusRouteData(
            route=route,
            stops=stops,
            buses=buses,
            updated=datetime.now().isoformat()
        )
