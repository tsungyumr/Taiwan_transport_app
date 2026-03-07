"""
新北市公車 CSV 資料模型測試
驗證欄位映射與資料解析正確性
"""

import pytest
from datetime import datetime

# 確保可以匯入模型
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.ntpc_bus_models import (
    BusStopInfo,
    BusRouteInfo,
    BusEstimation,
    BusStopWithETA,
    BusRouteSummary
)


class TestBusStopInfo:
    """測試公車站位資訊模型"""

    def test_from_csv_row_basic(self):
        """測試基本 CSV 行解析"""
        csv_row = {
            'id': '2347',
            'routeid': '935',
            'namezh': '捷運新埔站',
            'nameen': 'MRT Xinpu Station',
            'seqno': '1',
            'pgp': '0',
            'goback': '0',
            'longitude': '121.4665',
            'latitude': '25.0228',
            'address': '民生路3段',
            'stoplocationid': '2347',
            'showlon': '121.4665',
            'showlat': '25.0228',
            'vector': '90'
        }

        stop = BusStopInfo.from_csv_row(csv_row)

        assert stop.stop_id == '2347'
        assert stop.route_id == '935'
        assert stop.name_zh == '捷運新埔站'
        assert stop.name_en == 'MRT Xinpu Station'
        assert stop.sequence == 1
        assert stop.direction == 0
        assert stop.longitude == 121.4665
        assert stop.latitude == 25.0228

    def test_from_csv_row_with_empty_values(self):
        """測試帶有空值的 CSV 行解析"""
        csv_row = {
            'id': '1234',
            'routeid': '235',
            'namezh': '測試站',
            'nameen': '',
            'seqno': '5',
            'pgp': '',
            'goback': '1',
            'longitude': '',
            'latitude': '',
            'address': '',
            'stoplocationid': '',
            'showlon': '',
            'showlat': '',
            'vector': ''
        }

        stop = BusStopInfo.from_csv_row(csv_row)

        assert stop.stop_id == '1234'
        assert stop.route_id == '235'
        assert stop.name_zh == '測試站'
        assert stop.name_en is None
        assert stop.sequence == 5
        assert stop.direction == 1
        assert stop.longitude is None
        assert stop.latitude is None

    def test_model_validation(self):
        """測試模型驗證"""
        # 測試必填欄位
        with pytest.raises(Exception):
            BusStopInfo(
                stop_id='',
                route_id='',
                name_zh='',
                sequence=-1,  # 應該 >= 1
                direction=0
            )


class TestBusRouteInfo:
    """測試公車路線資訊模型"""

    def test_from_csv_row_basic(self):
        """測試基本 CSV 行解析"""
        csv_row = {
            'id': '935',
            'providerid': '1001',
            'providername': '台北客運',
            'namezh': '935',
            'nameen': '935',
            'pathattributeid': '',
            'pathattributename': '',
            'pathattributeename': '',
            'buildperiod': '',
            'departurezh': '林口',
            'departureen': 'Linkou',
            'destinationzh': '捷運新埔站',
            'destinationen': 'MRT Xinpu Sta.',
            'realsequence': '100',
            'distance': '25.5',
            'gofirstbustime': '05:30',
            'backfirstbustime': '05:30',
            'golastbustime': '22:30',
            'backlastbustime': '22:30',
            'peakheadway': '10-15',
            'offpeakheadway': '15-20',
            'bustimedesc': '林口05:30-22:30',
            'headwaydesc': '尖峰10-15分 離峰15-20分',
            'holidaygofirstbustime': '05:30',
            'holidaybackfirstbustime': '05:30',
            'holidaygolastbustime': '22:30',
            'holidaybacklastbustime': '22:30',
            'holidaybustimedesc': '林口05:30-22:30',
            'holidaypeakheadway': '10-15',
            'holidayoffpeakheadway': '15-20',
            'holidayheadwaydesc': '尖峰10-15分 離峰15-20分',
            'segmentbufferzh': '',
            'segmentbufferen': '',
            'ticketpricedescriptionzh': '二段票',
            'ticketpricedescriptionen': 'Two-section fare'
        }

        route = BusRouteInfo.from_csv_row(csv_row)

        assert route.route_id == '935'
        assert route.provider_name == '台北客運'
        assert route.name_zh == '935'
        assert route.departure_zh == '林口'
        assert route.destination_zh == '捷運新埔站'
        assert route.go_first_bus_time == '05:30'
        assert route.go_last_bus_time == '22:30'
        assert route.peak_headway == '10-15'
        assert route.distance == 25.5
        assert route.real_sequence == 100

    def test_get_display_name(self):
        """測試取得顯示名稱"""
        route = BusRouteInfo(
            route_id='935',
            provider_name='台北客運',
            name_zh='935',
            departure_zh='林口',
            destination_zh='捷運新埔站'
        )

        assert route.get_display_name() == '935'

    def test_get_direction_name(self):
        """測試取得方向名稱"""
        route = BusRouteInfo(
            route_id='935',
            provider_name='台北客運',
            name_zh='935',
            departure_zh='林口',
            destination_zh='捷運新埔站'
        )

        assert route.get_direction_name(0) == '往捷運新埔站'
        assert route.get_direction_name(1) == '往林口'


class TestBusEstimation:
    """測試公車預估到站時間模型"""

    def test_from_csv_row_basic(self):
        """測試基本 CSV 行解析"""
        csv_row = {
            'routeid': '935',
            'stopid': '2347',
            'estimatetime': '180',
            'goback': '0'
        }

        estimation = BusEstimation.from_csv_row(csv_row)

        assert estimation.route_id == '935'
        assert estimation.stop_id == '2347'
        assert estimation.estimate_seconds == 180
        assert estimation.direction == 0

    def test_get_estimate_text_arriving(self):
        """測試即將進站文字"""
        estimation = BusEstimation(
            route_id='935',
            stop_id='2347',
            estimate_seconds=30,
            direction=0
        )

        assert estimation.get_estimate_text() == '即將進站'
        assert estimation.get_status() == 'arriving'

    def test_get_estimate_text_minutes(self):
        """測試分鐘格式文字"""
        estimation = BusEstimation(
            route_id='935',
            stop_id='2347',
            estimate_seconds=300,  # 5分鐘
            direction=0
        )

        assert estimation.get_estimate_text() == '5 分鐘'
        assert estimation.get_status() == 'normal'

    def test_get_estimate_text_hours(self):
        """測試小時格式文字"""
        estimation = BusEstimation(
            route_id='935',
            stop_id='2347',
            estimate_seconds=5400,  # 1小時30分
            direction=0
        )

        assert estimation.get_estimate_text() == '1 小時 30 分鐘'

    def test_get_estimate_text_not_started(self):
        """測試尚未發車文字"""
        estimation = BusEstimation(
            route_id='935',
            stop_id='2347',
            estimate_seconds=0,
            direction=0
        )

        assert estimation.get_estimate_text() == '尚未發車'
        assert estimation.get_status() == 'not_started'

    def test_get_status_near(self):
        """測試接近中狀態"""
        estimation = BusEstimation(
            route_id='935',
            stop_id='2347',
            estimate_seconds=120,  # 2分鐘
            direction=0
        )

        assert estimation.get_status() == 'near'


class TestBusStopWithETA:
    """測試帶有到站時間的站牌模型"""

    def test_from_stop_and_estimation_with_eta(self):
        """測試結合預估資料的建立"""
        stop = BusStopInfo(
            stop_id='2347',
            route_id='935',
            name_zh='捷運新埔站',
            sequence=1,
            direction=0,
            longitude=121.4665,
            latitude=25.0228
        )

        estimation = BusEstimation(
            route_id='935',
            stop_id='2347',
            estimate_seconds=180,
            direction=0
        )

        stop_with_eta = BusStopWithETA.from_stop_and_estimation(stop, estimation)

        assert stop_with_eta.stop_id == '2347'
        assert stop_with_eta.name_zh == '捷運新埔站'
        assert stop_with_eta.sequence == 1
        assert stop_with_eta.estimate_seconds == 180
        assert stop_with_eta.estimate_text == '3 分鐘'
        assert stop_with_eta.status == 'near'

    def test_from_stop_and_estimation_without_eta(self):
        """測試無預估資料的建立"""
        stop = BusStopInfo(
            stop_id='2347',
            route_id='935',
            name_zh='捷運新埔站',
            sequence=1,
            direction=0
        )

        stop_with_eta = BusStopWithETA.from_stop_and_estimation(stop, None)

        assert stop_with_eta.stop_id == '2347'
        assert stop_with_eta.name_zh == '捷運新埔站'
        assert stop_with_eta.estimate_seconds is None
        assert stop_with_eta.estimate_text == '無資料'
        assert stop_with_eta.status == 'normal'


class TestBusRouteSummary:
    """測試公車路線摘要模型"""

    def test_from_route_info(self):
        """測試從路線資訊建立摘要"""
        route = BusRouteInfo(
            route_id='935',
            provider_name='台北客運',
            name_zh='935',
            departure_zh='林口',
            destination_zh='捷運新埔站',
            go_first_bus_time='05:30',
            go_last_bus_time='22:30',
            headway_desc='尖峰10-15分 離峰15-20分'
        )

        summary = BusRouteSummary.from_route_info(route)

        assert summary.route_id == '935'
        assert summary.name_zh == '935'
        assert summary.provider_name == '台北客運'
        assert summary.departure_zh == '林口'
        assert summary.destination_zh == '捷運新埔站'
        assert summary.first_bus_time == '05:30'
        assert summary.last_bus_time == '22:30'
        assert summary.headway_desc == '尖峰10-15分 離峰15-20分'


class TestModelIntegration:
    """測試模型整合情境"""

    def test_route_with_stops_and_estimations(self):
        """測試路線、站牌、預估資料的整合"""
        # 建立路線
        route = BusRouteInfo(
            route_id='935',
            provider_name='台北客運',
            name_zh='935',
            departure_zh='林口',
            destination_zh='捷運新埔站'
        )

        # 建立站牌
        stops = [
            BusStopInfo(stop_id='1', route_id='935', name_zh='林口', sequence=1, direction=0),
            BusStopInfo(stop_id='2', route_id='935', name_zh='文化一路', sequence=2, direction=0),
            BusStopInfo(stop_id='3', route_id='935', name_zh='捷運新埔站', sequence=3, direction=0),
        ]

        # 建立預估時間
        estimations = {
            '1': BusEstimation(route_id='935', stop_id='1', estimate_seconds=0, direction=0),
            '2': BusEstimation(route_id='935', stop_id='2', estimate_seconds=120, direction=0),
            '3': BusEstimation(route_id='935', stop_id='3', estimate_seconds=300, direction=0),
        }

        # 整合資料
        stops_with_eta = []
        for stop in stops:
            estimation = estimations.get(stop.stop_id)
            stops_with_eta.append(BusStopWithETA.from_stop_and_estimation(stop, estimation))

        # 驗證
        assert len(stops_with_eta) == 3
        assert stops_with_eta[0].estimate_text == '尚未發車'
        assert stops_with_eta[1].estimate_text == '2 分鐘'
        assert stops_with_eta[2].estimate_text == '5 分鐘'

        # 驗證站序
        sequences = [s.sequence for s in stops_with_eta]
        assert sequences == [1, 2, 3]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
