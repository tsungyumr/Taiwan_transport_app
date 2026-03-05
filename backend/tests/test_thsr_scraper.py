"""
台灣高鐵爬蟲測試腳本
測試 thsr_scraper 模組的各項功能
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加 backend 目錄到路徑
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# 直接匯入模組，避免 __init__.py 的問題
import importlib.util
spec = importlib.util.spec_from_file_location("thsr_scraper", os.path.join(backend_dir, "scrapers", "thsr_scraper.py"))
thsr_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(thsr_module)

# 取得需要的類別和函數
THSRScraper = thsr_module.THSRScraper
search_thsr_timetable = thsr_module.search_thsr_timetable
get_station_list = thsr_module.get_station_list
THSR_STATIONS = thsr_module.THSR_STATIONS
STATION_CODE_MAP = thsr_module.STATION_CODE_MAP
THSRScraperValidationError = thsr_module.THSRScraperValidationError


async def test_basic_functionality():
    """測試基本功能"""
    print("=" * 60)
    print("測試 1: 基本功能測試")
    print("=" * 60)

    # 測試取得車站列表
    stations = get_station_list()
    print(f"[OK] 取得 {len(stations)} 個車站資訊")

    # 驗證車站資料結構
    station = stations[0]
    assert 'code' in station
    assert 'name' in station
    assert 'sequence' in station
    print("[OK] 車站資料結構正確")

    # 測試車站對照表
    assert STATION_CODE_MAP["台北"] == "TPE"
    assert STATION_CODE_MAP["左營"] == "ZUY"
    print("[OK] 車站對照表正常")

    print("\n【所有高鐵車站】")
    for s in THSR_STATIONS:
        print(f"  {s.sequence}. {s.name} ({s.code})")


async def test_scraper_initialization():
    """測試爬蟲初始化"""
    print("\n" + "=" * 60)
    print("測試 2: 爬蟲初始化測試")
    print("=" * 60)

    try:
        async with THSRScraper(headless=True) as scraper:
            print("[OK] 爬蟲初始化成功")

            # 測試取得車站
            stations = await scraper.get_stations()
            print(f"[OK] 透過爬蟲取得 {len(stations)} 個車站")

            # 測試查詢特定車站
            station = scraper.get_station_by_name("台北")
            assert station is not None
            assert station.name == "台北"
            print("[OK] 車站查詢功能正常")

            # 測試快取功能
            scraper.clear_cache()
            print("[OK] 快取清除功能正常")

    except Exception as e:
        print(f"[FAIL] 測試失敗: {e}")
        raise


async def test_validation():
    """測試輸入驗證"""
    print("\n" + "=" * 60)
    print("測試 3: 輸入驗證測試")
    print("=" * 60)

    async with THSRScraper(headless=True) as scraper:
        # 測試相同起迄站
        try:
            await scraper.search_timetable("台北", "台北")
            print("[FAIL] 應該要拒絕相同的起迄站")
        except THSRScraperValidationError as e:
            print(f"[OK] 正確拒絕相同起迄站: {e}")

        # 測試無效車站
        try:
            await scraper.search_timetable("台北", "不存在的站")
            print("[FAIL] 應該要拒絕無效車站")
        except THSRScraperValidationError as e:
            print(f"[OK] 正確拒絕無效車站: {e}")

        # 測試日期格式
        today = datetime.now().strftime("%Y-%m-%d")
        validated_date = scraper._validate_date(today)
        print(f"[OK] 日期驗證通過: {validated_date}")

        # 測試車站名稱標準化
        assert scraper._validate_station("臺北") == "台北"
        assert scraper._validate_station("台北 ") == "台北"
        print("[OK] 車站名稱標準化正常")


async def test_timetable_search():
    """測試時刻表查詢 (使用模擬資料)"""
    print("\n" + "=" * 60)
    print("測試 4: 時刻表查詢測試")
    print("=" * 60)

    today = datetime.now().strftime("%Y-%m-%d")

    async with THSRScraper(headless=True) as scraper:
        print(f"\n查詢: 台北 -> 左營, 日期: {today}")
        print("-" * 40)

        try:
            result = await scraper.search_timetable("台北", "左營", today)

            print(f"[OK] 查詢成功，找到 {result.total_count} 班列車")
            print(f"[OK] 起站: {result.departure_station}")
            print(f"[OK] 迄站: {result.arrival_station}")
            print(f"[OK] 查詢時間: {result.query_time}")

            # 顯示部分結果
            print("\n【部分列車資訊】")
            for i, train in enumerate(result.trains[:3], 1):
                print(f"\n  {i}. 車次 {train.train_number} ({train.train_type})")
                print(f"     時間: {train.departure_time} -> {train.arrival_time}")
                print(f"     行車: {train.duration_text} ({train.duration}分鐘)")
                print(f"     票價: 標準艙 ${train.price_standard}")
                if train.early_bird_discount:
                    print(f"     優惠: {train.early_bird_discount}")

            # 驗證資料完整性
            if result.trains:
                train = result.trains[0]
                assert train.train_number
                assert train.departure_time
                assert train.arrival_time
                assert train.duration >= 0
                print("\n[OK] 列車資料結構完整")

        except Exception as e:
            print(f"[FAIL] 查詢失敗: {e}")
            raise


async def test_convenience_function():
    """測試便捷函數"""
    print("\n" + "=" * 60)
    print("測試 5: 便捷函數測試")
    print("=" * 60)

    today = datetime.now().strftime("%Y-%m-%d")

    print(f"\n使用便捷函數查詢: 台中 -> 台北")
    print("-" * 40)

    try:
        result = await search_thsr_timetable("台中", "台北", today, headless=True)
        print(f"[OK] 便捷函數查詢成功，找到 {result.total_count} 班列車")

        # 顯示前 3 班
        for train in result.trains[:3]:
            print(f"  - 車次{train.train_number}: {train.departure_time}-{train.arrival_time} "
                  f"(${train.price_standard})")

    except Exception as e:
        print(f"[FAIL] 便捷函數測試失敗: {e}")
        raise


async def test_duration_calculation():
    """測試行車時間計算"""
    print("\n" + "=" * 60)
    print("測試 6: 行車時間計算測試")
    print("=" * 60)

    async with THSRScraper(headless=True) as scraper:
        test_cases = [
            (("08:00", "10:30"), (150, "2小時30分")),
            (("14:00", "14:45"), (45, "45分")),
            (("23:00", "01:30"), (150, "2小時30分")),  # 跨日
            (("09:00", "09:05"), (5, "5分")),
        ]

        for (dep, arr), (expected_min, expected_text) in test_cases:
            duration, text = scraper._calculate_duration(dep, arr)
            status = "[OK]" if duration == expected_min else "[FAIL]"
            print(f"{status} {dep} -> {arr}: {text} ({duration}分鐘)")


async def test_price_estimation():
    """測試票價估算"""
    print("\n" + "=" * 60)
    print("測試 7: 票價估算測試")
    print("=" * 60)

    async with THSRScraper(headless=True) as scraper:
        test_routes = [
            ("台北", "台中"),
            ("台北", "左營"),
            ("桃園", "台南"),
            ("新竹", "嘉義"),
        ]

        for dep, arr in test_routes:
            std, bus, free = scraper._estimate_price(dep, arr)
            print(f"  {dep} -> {arr}:")
            print(f"    標準艙: ${std}, 商務艙: ${bus}, 自由座: ${free}")


async def run_all_tests():
    """執行所有測試"""
    print("\n" + "=" * 70)
    print("  台灣高鐵爬蟲模組測試套件")
    print("=" * 70)

    start_time = datetime.now()

    try:
        await test_basic_functionality()
        await test_scraper_initialization()
        await test_validation()
        await test_timetable_search()
        await test_convenience_function()
        await test_duration_calculation()
        await test_price_estimation()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print("\n" + "=" * 70)
        print(f"  [SUCCESS] 所有測試通過! (耗時: {duration:.2f} 秒)")
        print("=" * 70)

        return True

    except Exception as e:
        print("\n" + "=" * 70)
        print(f"  [FAILED] 測試失敗: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
