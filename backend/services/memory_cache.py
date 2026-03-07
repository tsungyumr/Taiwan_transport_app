"""
記憶體快取服務
提供高效的記憶體資料快取
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Generic, Optional, TypeVar, Callable, Any
from dataclasses import dataclass
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """快取項目"""
    value: T
    created_at: datetime
    ttl_seconds: int
    access_count: int = 0
    last_accessed: Optional[datetime] = None

    def is_expired(self) -> bool:
        """檢查是否過期"""
        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed > self.ttl_seconds

    def touch(self):
        """更新存取時間"""
        self.access_count += 1
        self.last_accessed = datetime.now()


class MemoryCache(Generic[T]):
    """
    記憶體快取

    提供 TTL 與 LRU 策略的快取機制
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 300,
        cleanup_interval: int = 60
    ):
        """
        初始化快取

        Args:
            max_size: 最大快取項目數
            default_ttl: 預設 TTL（秒）
            cleanup_interval: 清理間隔（秒）
        """
        self._cache: Dict[str, CacheEntry[T]] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cleanup_interval = cleanup_interval
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }

    async def start(self) -> None:
        """啟動背景清理任務"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("記憶體快取已啟動")

    async def stop(self) -> None:
        """停止背景清理任務"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("記憶體快取已停止")

    async def get(self, key: str) -> Optional[T]:
        """
        取得快取值

        Args:
            key: 快取鍵

        Returns:
            快取值，若不存在或過期則回傳 None
        """
        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._stats["misses"] += 1
                return None

            if entry.is_expired():
                del self._cache[key]
                self._stats["misses"] += 1
                return None

            entry.touch()
            self._stats["hits"] += 1
            return entry.value

    async def set(
        self,
        key: str,
        value: T,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """
        設定快取值

        Args:
            key: 快取鍵
            value: 快取值
            ttl_seconds: TTL（秒），預設使用初始化設定
        """
        async with self._lock:
            # 檢查是否需要淘汰
            if len(self._cache) >= self._max_size and key not in self._cache:
                await self._evict_lru()

            self._cache[key] = CacheEntry(
                value=value,
                created_at=datetime.now(),
                ttl_seconds=ttl_seconds or self._default_ttl
            )

    async def delete(self, key: str) -> bool:
        """
        刪除快取項目

        Returns:
            是否成功刪除
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def clear(self) -> None:
        """清除所有快取"""
        async with self._lock:
            self._cache.clear()
            logger.info("快取已清除")

    async def _evict_lru(self) -> None:
        """淘汰最少使用的項目"""
        if not self._cache:
            return

        # 找出最少使用的項目
        lru_key = min(
            self._cache.keys(),
            key=lambda k: (
                self._cache[k].access_count,
                self._cache[k].last_accessed or self._cache[k].created_at
            )
        )

        del self._cache[lru_key]
        self._stats["evictions"] += 1
        logger.debug(f"淘汰快取項目: {lru_key}")

    async def _cleanup_loop(self) -> None:
        """背景清理迴圈"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理快取時發生錯誤: {e}")

    async def _cleanup_expired(self) -> None:
        """清理過期項目"""
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.debug(f"清理 {len(expired_keys)} 個過期快取項目")

    def get_stats(self) -> Dict[str, Any]:
        """取得快取統計"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": f"{hit_rate:.2%}",
            "evictions": self._stats["evictions"]
        }


def cached(
    ttl_seconds: int = 300,
    max_size: int = 1000,
    key_prefix: str = ""
):
    """
    快取裝飾器

    自動快取函數回傳值

    Example:
        @cached(ttl_seconds=60)
        async def get_data(id: str):
            return await fetch_data(id)
    """
    cache = MemoryCache(max_size=max_size, default_ttl=ttl_seconds)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 建立快取鍵
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # 嘗試從快取取得
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 執行函數
            result = await func(*args, **kwargs)

            # 存入快取
            await cache.set(cache_key, result)

            return result

        # 附加快取操作方法
        wrapper.cache = cache
        wrapper.clear_cache = cache.clear
        wrapper.get_stats = cache.get_stats

        return wrapper
    return decorator
