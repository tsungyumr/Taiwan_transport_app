"""
CSV 下載與快取服務驗證
測試新北市公車 CSV 資料下載功能
"""

import sys
import asyncio
from pathlib import Path

# 添加專案路徑
sys.path.insert(0, str(Path(__file__).parent))

from services.ntpc_csv_service import CSVDownloader, CSVCacheManager


async def test_cache_manager():
    """測試快取管理器"""
    print("\n【測試快取管理器】")

    import tempfile
    import os
    from datetime import datetime, timedelta

    temp_dir = tempfile.mkdtemp()
    cache = CSVCacheManager(temp_dir)

    # 測試路徑生成
    path = cache.get_file_path('stops')
    print(f"  快取路徑: {path}")
    assert path.suffix == '.csv'

    # 測試不存在的快取
    assert not cache.is_cache_valid('nonexistent', ttl_seconds=3600)
    print("  [OK] 不存在的快取檢測正確")

    # 建立測試檔案
    test_file = cache.get_file_path('test')
    test_file.write_text('test data')

    # 測試有效快取
    assert cache.is_cache_valid('test', ttl_seconds=3600)
    print("  [OK] 有效快取檢測正確")

    # 測試快取年齡
    age = cache.get_cache_age('test')
    print(f"  快取年齡: {age:.2f} 秒")
    assert age < 5

    # 測試過期快取
    old_time = datetime.now() - timedelta(hours=2)
    os.utime(test_file, (old_time.timestamp(), old_time.timestamp()))
    assert not cache.is_cache_valid('test', ttl_seconds=3600)
    print("  [OK] 過期快取檢測正確")

    # 清理
    import shutil
    shutil.rmtree(temp_dir)
    print("  [OK] 快取管理器測試通過")


async def test_downloader():
    """測試下載器"""
    print("\n【測試 CSV 下載器】")

    import tempfile
    import shutil

    temp_dir = tempfile.mkdtemp()
    downloader = CSVDownloader(temp_dir)

    try:
        # 測試下載站牌資料
        print("  正在下載站牌資料...")
        stops_path = await downloader.download_stops(force=True)
        print(f"  站牌資料已下載: {stops_path}")
        assert stops_path.exists()

        # 驗證內容
        content = stops_path.read_text(encoding='utf-8')
        lines = content.strip().split('\n')
        print(f"  行數: {len(lines)}")
        print(f"  標題列: {lines[0][:100]}...")
        assert 'id' in lines[0]
        assert 'routeid' in lines[0]
        assert 'namezh' in lines[0]
        print("  [OK] 站牌資料格式正確")

        # 測試快取機制
        print("\n  測試快取機制...")
        stops_path2 = await downloader.download_stops(force=False)
        assert stops_path == stops_path2
        print("  [OK] 快取機制運作正常")

        # 測試強制重新下載
        print("\n  測試強制重新下載...")
        import time
        mtime1 = stops_path.stat().st_mtime
        await asyncio.sleep(0.5)
        stops_path3 = await downloader.download_stops(force=True)
        mtime2 = stops_path3.stat().st_mtime
        assert mtime2 >= mtime1
        print("  [OK] 強制重新下載運作正常")

        print("  [OK] 下載器測試通過")

    finally:
        await downloader.close()
        shutil.rmtree(temp_dir)


async def test_all_downloads():
    """測試下載所有資料"""
    print("\n【測試下載所有資料類型】")

    import tempfile
    import shutil

    temp_dir = tempfile.mkdtemp()
    downloader = CSVDownloader(temp_dir)

    try:
        # 下載所有類型
        print("  下載站牌資料...")
        stops = await downloader.download_stops(force=True)
        print(f"    -> {stops.name}")

        print("  下載路線資料...")
        routes = await downloader.download_routes(force=True)
        print(f"    -> {routes.name}")

        print("  下載到站預估資料...")
        estimations = await downloader.download_estimations(force=True)
        print(f"    -> {estimations.name}")

        # 驗證檔案大小
        for name, path in [('站牌', stops), ('路線', routes), ('預估', estimations)]:
            size = path.stat().st_size
            print(f"  {name}資料大小: {size:,} bytes ({size/1024:.1f} KB)")
            assert size > 0

        # 驗證快取
        assert downloader.cache_manager.is_cache_valid('stops')
        assert downloader.cache_manager.is_cache_valid('routes')
        assert downloader.cache_manager.is_cache_valid('estimations')
        print("  [OK] 所有快取皆有效")

        print("  [OK] 所有資料下載測試通過")

    finally:
        await downloader.close()
        shutil.rmtree(temp_dir)


async def test_data_directory():
    """測試資料目錄結構"""
    print("\n【測試資料目錄結構】")

    import tempfile
    import shutil

    temp_dir = tempfile.mkdtemp()
    downloader = CSVDownloader(temp_dir)

    try:
        # 下載資料
        await downloader.download_stops(force=True)
        await downloader.download_routes(force=True)

        # 檢查目錄內容
        files = list(Path(temp_dir).glob('*.csv'))
        print(f"  資料目錄檔案數: {len(files)}")
        for f in files:
            print(f"    - {f.name}")

        assert len(files) >= 2

        # 檢查檔案命名格式
        stops_files = list(Path(temp_dir).glob('stops_*.csv'))
        routes_files = list(Path(temp_dir).glob('routes_*.csv'))

        assert len(stops_files) > 0
        assert len(routes_files) > 0

        print("  [OK] 資料目錄結構測試通過")

    finally:
        await downloader.close()
        shutil.rmtree(temp_dir)


async def main():
    """主程式"""
    print("=" * 60)
    print("CSV 下載與快取服務驗證")
    print("=" * 60)

    try:
        await test_cache_manager()
        await test_downloader()
        await test_all_downloads()
        await test_data_directory()

        print("\n" + "=" * 60)
        print("所有測試通過！CSV 下載與快取服務運作正常。")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n[FAIL] 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(asyncio.run(main()))
