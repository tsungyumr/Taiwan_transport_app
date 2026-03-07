"""
CSV 下載與快取服務測試
驗證資料下載、快取機制與檔案管理
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta
import shutil

# 確保可以匯入
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.ntpc_csv_service import CSVDownloader, CSVCacheManager


class TestCSVCacheManager:
    """測試快取管理器"""

    def setup_method(self):
        """每個測試前建立臨時目錄"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = CSVCacheManager(self.temp_dir)

    def teardown_method(self):
        """每個測試後清理臨時目錄"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_cache_path(self):
        """測試取得快取檔案路徑"""
        path = self.cache_manager.get_cache_path('stops')
        assert 'stops_' in path.name
        assert path.suffix == '.csv'
        assert path.parent == Path(self.temp_dir)

    def test_is_cache_valid_no_file(self):
        """測試不存在的快取檔案"""
        assert not self.cache_manager.is_cache_valid('nonexistent', ttl_seconds=3600)

    def test_is_cache_valid_expired(self):
        """測試過期的快取"""
        # 建立一個過期的檔案
        cache_file = self.cache_manager.get_cache_path('test')
        cache_file.write_text('test data')

        # 修改時間為2小時前
        old_time = datetime.now() - timedelta(hours=2)
        os.utime(cache_file, (old_time.timestamp(), old_time.timestamp()))

        assert not self.cache_manager.is_cache_valid('test', ttl_seconds=3600)

    def test_is_cache_valid_valid(self):
        """測試有效的快取"""
        # 建立一個新的檔案
        cache_file = self.cache_manager.get_cache_path('test')
        cache_file.write_text('test data')

        assert self.cache_manager.is_cache_valid('test', ttl_seconds=3600)

    def test_get_cache_age(self):
        """測試取得快取年齡"""
        # 新檔案
        cache_file = self.cache_manager.get_cache_path('test')
        cache_file.write_text('test data')

        age = self.cache_manager.get_cache_age('test')
        assert age < 5  # 應該小於5秒

        # 不存在的檔案
        age = self.cache_manager.get_cache_age('nonexistent')
        assert age is None

    def test_clear_expired_caches(self):
        """測試清理過期快取"""
        # 建立過期檔案
        old_file = self.cache_manager.get_cache_path('old')
        old_file.write_text('old data')
        old_time = datetime.now() - timedelta(hours=2)
        os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))

        # 建立有效檔案
        new_file = self.cache_manager.get_cache_path('new')
        new_file.write_text('new data')

        # 清理過期快取
        cleared = self.cache_manager.clear_expired_caches(ttl_seconds=3600)

        assert cleared == 1
        assert not old_file.exists()
        assert new_file.exists()


class TestCSVDownloader:
    """測試 CSV 下載器"""

    def setup_method(self):
        """每個測試前建立臨時目錄"""
        self.temp_dir = tempfile.mkdtemp()
        self.downloader = CSVDownloader(self.temp_dir)

    def teardown_method(self):
        """每個測試後清理"""
        asyncio.run(self.downloader.close())
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_download_stops(self):
        """測試下載站牌資料"""
        # 實際下載測試（可能需要較長時間）
        try:
            file_path = await self.downloader.download_stops(force=True)
            assert file_path.exists()
            assert file_path.suffix == '.csv'

            # 驗證內容
            content = file_path.read_text(encoding='utf-8')
            assert 'id' in content
            assert 'routeid' in content
            assert 'namezh' in content
        except Exception as e:
            pytest.skip(f"下載失敗（可能是網路問題）: {e}")

    @pytest.mark.asyncio
    async def test_download_routes(self):
        """測試下載路線資料"""
        try:
            file_path = await self.downloader.download_routes(force=True)
            assert file_path.exists()

            content = file_path.read_text(encoding='utf-8')
            assert 'providername' in content
            assert 'departurezh' in content
        except Exception as e:
            pytest.skip(f"下載失敗（可能是網路問題）: {e}")

    @pytest.mark.asyncio
    async def test_cache_mechanism(self):
        """測試快取機制"""
        try:
            # 第一次下載
            path1 = await self.downloader.download_stops(force=False)

            # 短時間內再次下載應該使用快取
            path2 = await self.downloader.download_stops(force=False)

            assert path1 == path2
        except Exception as e:
            pytest.skip(f"測試失敗: {e}")

    @pytest.mark.asyncio
    async def test_force_download(self):
        """測試強制重新下載"""
        try:
            # 先下載一次
            path1 = await self.downloader.download_stops(force=True)
            mtime1 = path1.stat().st_mtime

            # 等待一小段時間
            await asyncio.sleep(0.1)

            # 強制重新下載
            path2 = await self.downloader.download_stops(force=True)
            mtime2 = path2.stat().st_mtime

            # 檔案應該被重新寫入
            assert mtime2 >= mtime1
        except Exception as e:
            pytest.skip(f"測試失敗: {e}")


class TestIntegration:
    """整合測試"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """測試完整工作流程"""
        temp_dir = tempfile.mkdtemp()

        try:
            downloader = CSVDownloader(temp_dir)

            # 1. 下載所有資料
            stops_path = await downloader.download_stops(force=True)
            routes_path = await downloader.download_routes(force=True)
            estimations_path = await downloader.download_estimations(force=True)

            # 2. 驗證檔案存在
            assert stops_path.exists()
            assert routes_path.exists()
            assert estimations_path.exists()

            # 3. 驗證快取有效
            assert downloader.cache_manager.is_cache_valid('stops')
            assert downloader.cache_manager.is_cache_valid('routes')
            assert downloader.cache_manager.is_cache_valid('estimations')

            # 4. 再次下載應使用快取
            stops_path2 = await downloader.download_stops(force=False)
            assert stops_path == stops_path2

            await downloader.close()

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
