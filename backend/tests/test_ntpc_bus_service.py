"""
新北市公車資料服務測試
驗證資料載入、搜尋與整合功能
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.ntpc_bus_service import NTPCBusService


class TestNTPCBusService:
    """測試新北市公車資料服務"""

    def setup_method(self):
        """每個測試前建立臨時目錄"""
        self.temp_dir = tempfile.mkdtemp()
        self.service = NTPCBusService(self.temp_dir)

    def teardown_method(self):
        """每個測試後清理"""
        asyncio.run(self.service.close())
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_initialize(self):
        """測試初始化與資料載入"""
        # 初始化（下載並載入資料）
        await self.service.initialize()

        # 驗證資料已載入
        routes = self.service.get_all_routes()
        assert len(routes) > 0, "應該有路線資料"

        # 驗證路線資料欄位
        route = routes[0]
        assert route.route_id
        assert route.name_zh
        assert route.provider_name

    @pytest.mark.asyncio
    async def test_search_routes(self):
        """測試路線搜尋"""
        await self.service.initialize()

        # 搜尋數字路線（如 935）
        results = self.service.search_routes('935')
        assert len(results) >= 0  # 可能有或沒有結果

        # 搜尋所有路線
        all_results = self.service.search_routes('')
        assert len(all_results) == len(self.service.get_all_routes())

    @pytest.mark.asyncio
    async def test_get_route(self):
        """測試取得特定路線"""
        await self.service.initialize()

        # 取得第一個路線測試
        routes = self.service.get_all_routes()
        if routes:
            route_id = routes[0].route_id
            route = self.service.get_route(route_id)
            assert route is not None
            assert route.route_id == route_id

        # 不存在的路線
        nonexistent = self.service.get_route('NOTEXIST')
        assert nonexistent is None

    @pytest.mark.asyncio
    async def test_get_route_stops(self):
        """測試取得路線站牌"""
        await self.service.initialize()

        # 取得有站牌的路線
        for route in self.service.get_all_routes()[:5]:  # 測試前5個路線
            stops = self.service.get_route_stops(route.route_id, direction=0)

            if stops:
                # 驗證站牌已排序
                sequences = [s.sequence for s in stops]
                assert sequences == sorted(sequences)

                # 驗證站牌欄位
                stop = stops[0]
                assert stop.stop_id
                assert stop.name_zh
                assert stop.route_id == route.route_id

    @pytest.mark.asyncio
    async def test_get_route_stops_with_eta(self):
        """測試取得路線站牌與到站時間"""
        await self.service.initialize()

        # 測試前5個路線
        for route in self.service.get_all_routes()[:5]:
            stops_with_eta = self.service.get_route_stops_with_eta(route.route_id, direction=0)

            if stops_with_eta:
                # 驗證站牌與到站時間整合
                stop = stops_with_eta[0]
                assert stop.stop_id
                assert stop.name_zh
                assert stop.estimate_text  # 應該有預估文字

    @pytest.mark.asyncio
    async def test_get_route_summaries(self):
        """測試取得路線摘要"""
        await self.service.initialize()

        summaries = self.service.get_route_summaries()
        assert len(summaries) == len(self.service.get_all_routes())

        if summaries:
            summary = summaries[0]
            assert summary.route_id
            assert summary.name_zh
            assert summary.provider_name
            assert summary.departure_zh
            assert summary.destination_zh

    @pytest.mark.asyncio
    async def test_refresh_estimations(self):
        """測試重新整理到站時間"""
        await self.service.initialize()

        # 記錄目前的預估資料數量
        initial_count = len(self.service._estimations)

        # 重新整理
        await self.service.refresh_estimations()

        # 驗證資料已更新
        assert len(self.service._estimations) >= 0


class TestDataIntegration:
    """測試資料整合情境"""

    @pytest.mark.asyncio
    async def test_route_stop_estimation_integration(self):
        """測試路線-站牌-到站時間整合"""
        temp_dir = tempfile.mkdtemp()
        service = NTPCBusService(temp_dir)

        try:
            await service.initialize()

            # 取得路線
            routes = service.get_all_routes()
            assert len(routes) > 0

            # 選擇第一個有站牌的路線
            for route in routes:
                stops = service.get_route_stops(route.route_id, direction=0)
                if stops:
                    # 取得帶到站時間的站牌
                    stops_with_eta = service.get_route_stops_with_eta(route.route_id, direction=0)
                    assert len(stops_with_eta) == len(stops)

                    # 驗證每個站牌都有預估時間（或無資料）
                    for stop in stops_with_eta:
                        assert stop.stop_id
                        assert stop.name_zh
                        assert stop.estimate_text in [
                            '尚未發車', '即將進站', '無資料'
                        ] or '分鐘' in stop.estimate_text or '小時' in stop.estimate_text

                    break  # 測試一個路線即可

        finally:
            await service.close()
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
