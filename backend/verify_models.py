"""
快速驗證新北市公車資料模型
執行基本功能測試確認模型正確運作
"""

import sys
from pathlib import Path

# 添加專案路徑
sys.path.insert(0, str(Path(__file__).parent))

from models.ntpc_bus_models import (
    BusStopInfo,
    BusRouteInfo,
    BusEstimation,
    BusStopWithETA,
    BusRouteSummary
)


def test_stop_info():
    """測試站牌資訊模型"""
    print("\n【測試站牌資訊模型】")

    # 模擬 CSV 資料
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
    print(f"  站牌代碼: {stop.stop_id}")
    print(f"  路線代碼: {stop.route_id}")
    print(f"  站名: {stop.name_zh}")
    print(f"  站序: {stop.sequence}")
    print(f"  方向: {'去程' if stop.direction == 0 else '返程'}")
    print(f"  座標: ({stop.longitude}, {stop.latitude})")
    print("  [OK] 站牌資訊模型測試通過")


def test_route_info():
    """測試路線資訊模型"""
    print("\n【測試路線資訊模型】")

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
        'holidaygofirstbustime': '',
        'holidaybackfirstbustime': '',
        'holidaygolastbustime': '',
        'holidaybacklastbustime': '',
        'holidaybustimedesc': '',
        'holidaypeakheadway': '',
        'holidayoffpeakheadway': '',
        'holidayheadwaydesc': '',
        'segmentbufferzh': '',
        'segmentbufferen': '',
        'ticketpricedescriptionzh': '二段票',
        'ticketpricedescriptionen': ''
    }

    route = BusRouteInfo.from_csv_row(csv_row)
    print(f"  路線代碼: {route.route_id}")
    print(f"  路線名稱: {route.name_zh}")
    print(f"  營運業者: {route.provider_name}")
    print(f"  起點: {route.departure_zh}")
    print(f"  終點: {route.destination_zh}")
    print(f"  去程時間: {route.go_first_bus_time} - {route.go_last_bus_time}")
    print(f"  發車間距: {route.headway_desc}")
    print(f"  顯示名稱: {route.get_display_name()}")
    print(f"  去程方向: {route.get_direction_name(0)}")
    print(f"  返程方向: {route.get_direction_name(1)}")
    print("  [OK] 路線資訊模型測試通過")


def test_estimation():
    """測試預估到站時間模型"""
    print("\n【測試預估到站時間模型】")

    test_cases = [
        {'routeid': '935', 'stopid': '2347', 'estimatetime': '0', 'goback': '0'},
        {'routeid': '935', 'stopid': '2348', 'estimatetime': '30', 'goback': '0'},
        {'routeid': '935', 'stopid': '2349', 'estimatetime': '120', 'goback': '0'},
        {'routeid': '935', 'stopid': '2350', 'estimatetime': '300', 'goback': '0'},
        {'routeid': '935', 'stopid': '2351', 'estimatetime': '3600', 'goback': '0'},
    ]

    for csv_row in test_cases:
        estimation = BusEstimation.from_csv_row(csv_row)
        print(f"  站牌 {estimation.stop_id}: {estimation.get_estimate_text()} (狀態: {estimation.get_status()})")

    print("  ✅ 預估到站時間模型測試通過")


def test_integration():
    """測試資料整合"""
    print("\n【測試資料整合】")

    # 建立路線
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
    print(f"\n  路線: {route.name_zh} {route.get_direction_name(0)}")
    print(f"  業者: {route.provider_name}")
    print(f"  營運時間: {route.go_first_bus_time} - {route.go_last_bus_time}")
    print("\n  站牌資訊:")

    for stop in stops:
        estimation = estimations.get(stop.stop_id)
        stop_with_eta = BusStopWithETA.from_stop_and_estimation(stop, estimation)
        print(f"    {stop_with_eta.sequence}. {stop_with_eta.name_zh} - {stop_with_eta.estimate_text}")

    # 建立路線摘要
    summary = BusRouteSummary.from_route_info(route)
    print(f"\n  路線摘要: {summary.name_zh} ({summary.provider_name})")
    print(f"  起迄: {summary.departure_zh} - {summary.destination_zh}")

    print("  ✅ 資料整合測試通過")


def test_edge_cases():
    """測試邊界情況"""
    print("\n【測試邊界情況】")

    # 空值處理
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
    assert stop.name_en is None
    assert stop.longitude is None
    print("  ✅ 空值處理測試通過")

    # 特殊字元
    csv_row_special = {
        'id': '5678',
        'routeid': '藍15',
        'namezh': '捷運中山站(志仁高中)',
        'nameen': 'MRT Zhongshan Sta. (Zhiren High School)',
        'seqno': '1',
        'goback': '0',
    }

    stop_special = BusStopInfo.from_csv_row(csv_row_special)
    assert stop_special.route_id == '藍15'
    assert '志仁高中' in stop_special.name_zh
    print("  ✅ 特殊字元測試通過")


def main():
    """主程式"""
    print("=" * 60)
    print("新北市公車 CSV 資料模型驗證")
    print("=" * 60)

    try:
        test_stop_info()
        test_route_info()
        test_estimation()
        test_integration()
        test_edge_cases()

        print("\n" + "=" * 60)
        print("✅ 所有測試通過！模型建立成功。")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
