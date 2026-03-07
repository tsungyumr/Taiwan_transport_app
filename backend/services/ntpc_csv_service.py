"""
新北市公車 CSV 下載與快取服務

提供自動下載與快取管理功能，確保資料及時更新且不重複下載。

快取策略：
- 站牌資料: 24 小時 TTL
- 路線資料: 24 小時 TTL
- 到站預估: 1 分鐘 TTL
"""

import os
import csv
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import logging

# 設定 logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """快取項目"""
    file_path: Path
    download_time: datetime
    ttl_seconds: int

    def is_valid(self) -> bool:
        """檢查快取是否有效"""
        if not self.file_path.exists():
            return False
        elapsed = (datetime.now() - self.download_time).total_seconds()
        return elapsed < self.ttl_seconds


class CSVCacheManager:
    """
    CSV 快取管理器

    管理下載的 CSV 檔案快取，避免重複下載。
    """

    # 資料來源設定
    DATA_SOURCES = {
        'stops': {
            'url': 'https://data.ntpc.gov.tw/api/datasets/34b402a8-53d9-483d-9406-24a682c2d6dc/csv/file',
            'ttl': 24 * 60 * 60,  # 24 小時
            'description': '公車站位資訊'
        },
        'routes': {
            'url': 'https://data.ntpc.gov.tw/api/datasets/0ee4e6bf-cee6-4ec8-8fe1-71f544015127/csv/file',
            'ttl': 24 * 60 * 60,  # 24 小時
            'description': '公車路線清單'
        },
        'estimations': {
            'url': 'https://data.ntpc.gov.tw/api/datasets/07f7ccb3-ed00-43c4-966d-08e9dab24e95/csv/file',
            'ttl': 60,  # 1 分鐘
            'description': '公車預估到站時間'
        }
    }

    def __init__(self, data_dir: Optional[Path] = None):
        """
        初始化快取管理器

        Args:
            data_dir: 資料儲存目錄，預設為專案目錄下的 data/ntpc_bus
        """
        if data_dir is None:
            # 預設路徑：專案根目錄/backend/data/ntpc_bus
            self.data_dir = Path(__file__).parent.parent / 'data' / 'ntpc_bus'
        else:
            self.data_dir = Path(data_dir)

        # 確保目錄存在
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 記憶體快取
        self._cache: Dict[str, CacheEntry] = {}

        logger.info(f"CSV 快取管理器初始化完成，資料目錄: {self.data_dir}")

    def _get_file_path(self, data_type: str, date_str: Optional[str] = None) -> Path:
        """
        取得檔案儲存路徑

        Args:
            data_type: 資料類型 (stops/routes/estimations)
            date_str: 日期字串 (YYYYMMDD)，預設為今天

        Returns:
            Path: 檔案完整路徑
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y%m%d')

        if data_type == 'estimations':
            # 到站預估使用固定檔名（因為更新頻繁）
            return self.data_dir / f'{data_type}_latest.csv'
        else:
            return self.data_dir / f'{data_type}_{date_str}.csv'

    def is_cache_valid(self, data_type: str) -> bool:
        """
        檢查快取是否有效

        Args:
            data_type: 資料類型

        Returns:
            bool: 快取是否有效
        """
        if data_type not in self._cache:
            # 檢查磁碟檔案
            file_path = self._get_file_path(data_type)
            if not file_path.exists():
                return False

            # 檢查檔案修改時間
            stat = file_path.stat()
            file_mtime = datetime.fromtimestamp(stat.st_mtime)
            ttl = self.DATA_SOURCES[data_type]['ttl']
            elapsed = (datetime.now() - file_mtime).total_seconds()

            return elapsed < ttl

        return self._cache[data_type].is_valid()

    def get_cache_info(self, data_type: str) -> Optional[Dict[str, Any]]:
        """
        取得快取資訊

        Args:
            data_type: 資料類型

        Returns:
            快取資訊字典，若無快取則回傳 None
        """
        file_path = self._get_file_path(data_type)

        if not file_path.exists():
            return None

        stat = file_path.stat()
        file_mtime = datetime.fromtimestamp(stat.st_mtime)
        ttl = self.DATA_SOURCES[data_type]['ttl']
        elapsed = (datetime.now() - file_mtime).total_seconds()
        remaining = max(0, ttl - elapsed)

        return {
            'data_type': data_type,
            'file_path': str(file_path),
            'file_size': stat.st_size,
            'modified_time': file_mtime.isoformat(),
            'ttl_seconds': ttl,
            'elapsed_seconds': int(elapsed),
            'remaining_seconds': int(remaining),
            'is_valid': remaining > 0
        }

    def update_cache(self, data_type: str, file_path: Path) -> None:
        """
        更新快取記錄

        Args:
            data_type: 資料類型
            file_path: 檔案路徑
        """
        ttl = self.DATA_SOURCES[data_type]['ttl']
        self._cache[data_type] = CacheEntry(
            file_path=file_path,
            download_time=datetime.now(),
            ttl_seconds=ttl
        )
        logger.info(f"快取已更新: {data_type} -> {file_path}")

    def get_file_path(self, data_type: str) -> Path:
        """
        取得資料檔案路徑

        Args:
            data_type: 資料類型

        Returns:
            Path: 檔案路徑
        """
        return self._get_file_path(data_type)

    def clear_cache(self, data_type: Optional[str] = None) -> None:
        """
        清除快取

        Args:
            data_type: 資料類型，若為 None 則清除所有快取
        """
        if data_type:
            if data_type in self._cache:
                del self._cache[data_type]
                logger.info(f"已清除快取: {data_type}")
        else:
            self._cache.clear()
            logger.info("已清除所有快取")

    def list_cached_files(self) -> List[Dict[str, Any]]:
        """
        列出所有快取檔案

        Returns:
            快取檔案資訊列表
        """
        files = []
        for csv_file in self.data_dir.glob('*.csv'):
            stat = csv_file.stat()
            files.append({
                'file_name': csv_file.name,
                'file_path': str(csv_file),
                'file_size': stat.st_size,
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        return sorted(files, key=lambda x: x['modified_time'], reverse=True)


class CSVDownloader:
    """
    CSV 檔案下載器

    負責從新北市開放資料平台下載 CSV 檔案。
    """

    def __init__(self, data_dir: Optional[str] = None, cache_manager: Optional[CSVCacheManager] = None):
        """
        初始化下載器

        Args:
            data_dir: 資料儲存目錄路徑（與 cache_manager 二選一）
            cache_manager: 快取管理器實例（與 data_dir 二選一）
        """
        if cache_manager is not None:
            self.cache = cache_manager
        elif data_dir is not None:
            self.cache = CSVCacheManager(data_dir)
        else:
            self.cache = CSVCacheManager()

        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """取得或建立 HTTP session"""
        if self._session is None or self._session.closed:
            import ssl
            # 建立不驗證 SSL 的 context（適用於開發環境）
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                connector=aiohttp.TCPConnector(ssl=ssl_context)
            )
        return self._session

    async def close(self) -> None:
        """關閉 HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def download(self, data_type: str, force: bool = False) -> Optional[Path]:
        """
        下載 CSV 檔案

        Args:
            data_type: 資料類型 (stops/routes/estimations)
            force: 是否強制重新下載，忽略快取

        Returns:
            下載的檔案路徑，若失敗則回傳 None
        """
        if data_type not in self.cache.DATA_SOURCES:
            logger.error(f"未知的資料類型: {data_type}")
            return None

        # 檢查快取
        if not force and self.cache.is_cache_valid(data_type):
            file_path = self.cache.get_file_path(data_type)
            logger.info(f"使用快取檔案: {file_path}")
            return file_path

        # 開始下載
        source = self.cache.DATA_SOURCES[data_type]
        url = source['url']
        file_path = self.cache.get_file_path(data_type)

        logger.info(f"開始下載 {source['description']}: {url}")

        try:
            session = await self._get_session()
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"下載失敗，HTTP {response.status}: {url}")
                    return None

                # 下載並儲存檔案
                content = await response.read()

                # 使用 aiofiles 非同步寫入檔案
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(content)

                # 更新快取
                self.cache.update_cache(data_type, file_path)

                file_size = len(content)
                logger.info(f"下載完成: {file_path} ({file_size} bytes)")

                return file_path

        except asyncio.TimeoutError:
            logger.error(f"下載超時: {url}")
            return None
        except Exception as e:
            logger.error(f"下載失敗: {e}")
            return None

    async def download_all(self, force: bool = False) -> Dict[str, Optional[Path]]:
        """
        下載所有 CSV 檔案

        Args:
            force: 是否強制重新下載

        Returns:
            資料類型對應檔案路徑的字典
        """
        results = {}
        for data_type in self.cache.DATA_SOURCES.keys():
            results[data_type] = await self.download(data_type, force=force)
            # 短暫延遲避免對伺服器造成壓力
            await asyncio.sleep(0.5)
        return results

    async def download_stops(self, force: bool = False) -> Optional[Path]:
        """下載公車站位資訊"""
        return await self.download('stops', force=force)

    async def download_routes(self, force: bool = False) -> Optional[Path]:
        """下載公車路線清單"""
        return await self.download('routes', force=force)

    async def download_estimations(self, force: bool = False) -> Optional[Path]:
        """下載公車預估到站時間"""
        return await self.download('estimations', force=force)


class CSVReader:
    """
    CSV 檔案讀取器

    提供統一的 CSV 讀取介面，支援編碼自動偵測。
    """

    ENCODINGS = ['utf-8', 'utf-8-sig', 'big5', 'cp950']

    @classmethod
    def read(cls, file_path: Path) -> List[Dict[str, str]]:
        """
        讀取 CSV 檔案

        Args:
            file_path: CSV 檔案路徑

        Returns:
            資料列列表，每列為欄位名稱對應值的字典
        """
        if not file_path.exists():
            logger.error(f"檔案不存在: {file_path}")
            return []

        # 嘗試不同編碼
        for encoding in cls.ENCODINGS:
            try:
                with open(file_path, 'r', encoding=encoding, newline='') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    logger.debug(f"成功使用 {encoding} 編碼讀取 {len(rows)} 筆資料")
                    return rows
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"讀取失敗: {e}")
                return []

        logger.error(f"無法使用任何編碼讀取檔案: {file_path}")
        return []

    @classmethod
    async def read_async(cls, file_path: Path) -> List[Dict[str, str]]:
        """
        非同步讀取 CSV 檔案

        Args:
            file_path: CSV 檔案路徑

        Returns:
            資料列列表
        """
        # 在執行緒池中執行同步讀取
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, cls.read, file_path)


# 便利函數
async def download_ntpc_bus_data(
    data_dir: Optional[Path] = None,
    force: bool = False
) -> Dict[str, Optional[Path]]:
    """
    下載所有新北市公車資料

    Args:
        data_dir: 資料儲存目錄
        force: 是否強制重新下載

    Returns:
        資料類型對應檔案路徑的字典
    """
    cache_manager = CSVCacheManager(data_dir)
    downloader = CSVDownloader(cache_manager)

    try:
        results = await downloader.download_all(force=force)
        return results
    finally:
        await downloader.close()


def get_cache_manager(data_dir: Optional[Path] = None) -> CSVCacheManager:
    """
    取得快取管理器實例

    Args:
        data_dir: 資料儲存目錄

    Returns:
        CSVCacheManager 實例
    """
    return CSVCacheManager(data_dir)
