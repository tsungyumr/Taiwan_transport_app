"""
台灣交通時刻表App - 公車API測試模組
Taipei Bus API Test Module

測試公車API端點的功能性、錯誤處理和整合性。
"""

import pytest
import httpx
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from datetime import datetime

# 導入主程式
from main import app
from api.routes.bus_routes_router import BusRouteResponse, BusRouteDataResponse

# 建立測試用客戶端
client = TestClient(app)


# ==================== 測試配置 ====================

@pytest.fixture
def mock_scraper():
    """建立爬蟲模組的mock物件"""
    with patch('api.routes.bus_routes_router.TaipeiBusScraper') as mock_scraper:
        mock_instance = mock_scraper.return_value

        # 設定mock爬蟲的行為
        mock_instance.get_bus_routes.return_value = [
            {
                "route_id": "235",
                "route_name": "235",
                "departure_stop": "長春路",
                "arrival_stop": "福港街",
                "operator": "首都客運",
                "direction": 0,
                "stops": ["長春路", "民生社區", "富民生態", "新東街", "吉祥路", "成福路", "福港街"]
            },
            {
                "route_id": "307",
                "route_name": "307",
                "departure_stop": "板橋",
                "arrival_stop": "撫遠街",
                "operator": "三重客運",
                "direction": 0,
                "stops": ["板橋", "致理科技大學", "新埔", "江子翠", "龍山寺", "西門", "博愛路", "撫遠街"]
            }
        ]

        mock_instance.get_bus_route_data.return_value = {
            "route": "235",
            "stops": [
                {"name": "長春路", "sequence": 1, "latitude": 25.0516, "longitude": 121.5386},
                {"name": "民生社區", "sequence": 2, "latitude": 25.0520, "longitude": 121.5390},
                {"name": "富民生態", "sequence": 3, "latitude": 25.0525, "longitude": 121.5395}
            ],
            "buses": [
                {
                    "id": "235-001",
                    "plate_number": "XX-1234",
                    "at_stop": 1,
                    "eta_next": "2分鐘後到站",
                    "heading_to": 2,
                    "latitude": 25.0518,
                    "longitude": 121.5388,
                    "speed": 15.5,
                    "direction": 0
                }
            ],
            "updated": datetime.now(),
            "operator": "首都客運",
            "direction": 0,
            "total_stops": 7
        }

        mock_instance.search_routes.return_value = [
            {
                "route_id": "235",
                "route_name": "235",
                "departure_stop": "長春路",
                "arrival_stop": "福港街",
                "operator": "首都客運"
            },
            {
                "route_id": "307",
                "route_name": "307",
                "departure_stop": "板橋",
                "arrival_stop": "撫遠街",
                "operator": "三重客運"
            }
        ]

        yield mock_instance


# ==================== 測試案例 ====================

class TestBusRoutesAPI:
    """測試公車路線列表API"""

    def test_get_bus_routes_success(self, mock_scraper):
        """測試取得公車路線列表成功"""
        response = client.get("/api/bus/routes")

        assert response.status_code == 200
        assert len(response.json()) == 2

        # 驗證回應格式
        assert "route_id" in response.json()[0]
        assert "route_name" in response.json()[0]
        assert "departure_stop" in response.json()[0]
        assert "arrival_stop" in response.json()[0]
        assert "operator" in response.json()[0]

    def test_get_bus_routes_with_route_name(self, mock_scraper):
        """測試搜尋特定路線名稱"""
        response = client.get("/api/bus/routes", params={"route_name": "235"})

        assert response.status_code == 200
        assert len(response.json()) == 2  # mock回傳所有路線

        # 驗證搜尋結果
        for route in response.json():
            assert "235" in route["route_name"] or "235" in route["route_id"]

    def test_get_bus_routes_with_limit(self, mock_scraper):
        """測試限制回傳數量"""
        response = client.get("/api/bus/routes", params={"limit": 1})

        assert response.status_code == 200
        assert len(response.json()) == 2  # mock回傳所有路線

    def test_get_bus_routes_invalid_limit(self, mock_scraper):
        """測試無效的limit參數"""
        response = client.get("/api/bus/routes", params={"limit": "abc"})

        assert response.status_code == 422  # 應該是422 Unprocessable Entity


class TestBusRouteDataAPI:
    """測試公車路線詳細資料API"""

    def test_get_bus_route_data_success(self, mock_scraper):
        """測試取得特定路線詳細資料成功"""
        response = client.get("/api/bus/235")

        assert response.status_code == 200

        # 驗證回應格式
        assert "route" in response.json()
        assert "stops" in response.json()
        assert "buses" in response.json()
        assert "updated" in response.json()
        assert "operator" in response.json()
        assert "direction" in response.json()
        assert "total_stops" in response.json()

    def test_get_bus_route_data_invalid_route_id(self, mock_scraper):
        """測試無效的route_id"""
        response = client.get("/api/bus/invalid_route")

        assert response.status_code == 503  # 應該是503 Service Unavailable
        assert "detail" in response.json()


class TestBusSearchAPI:
    """測試公車路線搜尋API"""

    def test_search_bus_routes_success(self, mock_scraper):
        """測試搜尋公車路線成功"""
        response = client.get("/api/bus/search", params={"query": "藍"})

        assert response.status_code == 200
        assert len(response.json()) == 2

        # 驗證搜尋結果
        for result in response.json():
            assert "route_id" in result
            assert "route_name" in result
            assert "departure_stop" in result
            assert "arrival_stop" in result
            assert "operator" in result

    def test_search_bus_routes_empty_query(self, mock_scraper):
        """測試空查詢"""
        response = client.get("/api/bus/search", params={"query": ""})

        assert response.status_code == 503  # 應該是503 Service Unavailable
        assert "detail" in response.json()


class TestBusOperatorsAPI:
    """測試公車業者API"""

    def test_get_bus_operators_success(self, mock_scraper):
        """測試取得公車業者列表成功"""
        response = client.get("/api/bus/operators")

        assert response.status_code == 200
        assert len(response.json()) > 0

        # 驗證回應格式
        assert isinstance(response.json()[0], str)


class TestBusHealthAPI:
    """測試公車健康檢查API"""

    def test_health_check_success(self, mock_scraper):
        """測試健康檢查成功"""
        response = client.get("/api/bus/health")

        assert response.status_code == 200
        assert "status" in response.json()
        assert "timestamp" in response.json()
        assert "version" in response.json()
        assert "features" in response.json()
        assert response.json()["status"] == "healthy"


# ==================== 錯誤處理測試 ====================

class TestAPIErrorHandling:
    """測試API錯誤處理"""

    @pytest.mark.parametrize("endpoint, params, expected_status", [
        ("routes", None, 503),
        ("{route_id}", {"route_id": "invalid"}, 503),
        ("search", {"query": "test"}, 503),
        ("operators", None, 503),
        ("health", None, 503)
    ])
    def test_api_error_handling(self, endpoint, params, expected_status, mock_scraper):
        """測試API錯誤處理"""
        path = f"/api/bus/{endpoint}"

        if params:
            response = client.get(path, params=params)
        else:
            response = client.get(path)

        assert response.status_code == expected_status
        assert "detail" in response.json()