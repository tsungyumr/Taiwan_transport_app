"""
台鐵車種過濾測試腳本
測試短距離區間（如五堵到南港）是否只返回區間車
"""

import asyncio
import sys
sys.path.insert(0, r'D:\source\Taiwan_transport_app\backend')

from main import TaiwanRailwayScraper

async def test_train_filter():
    """測試車種過濾功能"""
    scraper = TaiwanRailwayScraper()

    print("=" * 60)
    print("台鐵車種過濾測試")
    print("=" * 60)

    # 測試案例1: 五堵到南港（短距離，應該只有區間車）
    print("\n1. 測試短距離區間：五堵 -> 南港")
    print("-" * 40)
    is_short = scraper._is_short_distance("五堵", "南港")
    print(f"   是否為短距離: {is_short}")

    distance = scraper._get_station_distance("103", "106")  # 五堵:103, 南港:106
    print(f"   距離: {distance} 公里")

    mock_data = scraper._get_mock_data("103", "106")
    print(f"   返回列車數: {len(mock_data)}")
    print(f"   車種: {list(set(t.train_type for t in mock_data))}")

    # 驗證是否只有區間車
    train_types = set(t.train_type for t in mock_data)
    has_long_distance = any(t in scraper.LONG_DISTANCE_TRAINS for t in train_types)
    print(f"   [OK] 無長途列車: {not has_long_distance}")

    # 測試案例2: 台北到台中（長距離，應該有多種車種）
    print("\n2. 測試長距離區間：台北 -> 台中")
    print("-" * 40)
    is_short = scraper._is_short_distance("台北", "台中")
    print(f"   是否為短距離: {is_short}")

    distance = scraper._get_station_distance("108", "212")  # 台北:108, 台中:212
    print(f"   距離: {distance} 公里")

    mock_data = scraper._get_mock_data("108", "212")
    print(f"   返回列車數: {len(mock_data)}")
    print(f"   車種: {list(set(t.train_type for t in mock_data))}")

    # 測試案例3: 基隆到八堵（短距離）
    print("\n3. 測試短距離區間：基隆 -> 八堵")
    print("-" * 40)
    is_short = scraper._is_short_distance("基隆", "八堵")
    print(f"   是否為短距離: {is_short}")

    distance = scraper._get_station_distance("100", "101")  # 基隆:100, 八堵:101
    print(f"   距離: {distance} 公里")

    mock_data = scraper._get_mock_data("100", "101")
    print(f"   返回列車數: {len(mock_data)}")
    print(f"   車種: {list(set(t.train_type for t in mock_data))}")

    # 驗證是否只有區間車
    train_types = set(t.train_type for t in mock_data)
    has_long_distance = any(t in scraper.LONG_DISTANCE_TRAINS for t in train_types)
    print(f"   [OK] 無長途列車: {not has_long_distance}")

    # 測試案例4: 過濾功能測試
    print("\n4. 測試過濾功能")
    print("-" * 40)

    from main import TrainTimeEntry

    # 建立測試資料
    test_trains = [
        TrainTimeEntry(train_no="1", train_type="自強", departure_station="五堵", arrival_station="南港",
                      departure_time="08:00", arrival_time="08:10", duration="0:10", transferable=True),
        TrainTimeEntry(train_no="2", train_type="區間", departure_station="五堵", arrival_station="南港",
                      departure_time="08:15", arrival_time="08:25", duration="0:10", transferable=True),
        TrainTimeEntry(train_no="3", train_type="莒光", departure_station="五堵", arrival_station="南港",
                      departure_time="08:30", arrival_time="08:40", duration="0:10", transferable=True),
        TrainTimeEntry(train_no="4", train_type="太魯閣", departure_station="五堵", arrival_station="南港",
                      departure_time="08:45", arrival_time="08:55", duration="0:10", transferable=True),
        TrainTimeEntry(train_no="5", train_type="區間快", departure_station="五堵", arrival_station="南港",
                      departure_time="09:00", arrival_time="09:10", duration="0:10", transferable=True),
    ]

    print(f"   原始資料: {[t.train_type for t in test_trains]}")

    filtered = scraper._filter_trains_by_distance(test_trains, "五堵", "南港")
    print(f"   過濾後: {[t.train_type for t in filtered]}")
    print(f"   [OK] 過濾正確: {len(filtered) == 2 and all('區間' in t.train_type for t in filtered)}")

    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_train_filter())
