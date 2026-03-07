"""
背景任務排程器
定期執行資料更新任務
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ScheduledTask:
    """排程任務"""
    name: str
    coroutine: Callable
    interval_seconds: int
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    is_running: bool = False
    error_count: int = 0
    max_errors: int = 3


class BackgroundScheduler:
    """
    背景任務排程器

    管理所有背景更新任務：
    - 定期更新 CSV 資料
    - 清理過期快取
    - 監控系統健康
    """

    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._task_handle: Optional[asyncio.Task] = None

    def add_task(
        self,
        name: str,
        coroutine: Callable,
        interval_seconds: int,
        max_errors: int = 3
    ) -> None:
        """
        新增排程任務

        Args:
            name: 任務名稱
            coroutine: 異步函數
            interval_seconds: 執行間隔（秒）
            max_errors: 最大連續錯誤次數
        """
        self.tasks[name] = ScheduledTask(
            name=name,
            coroutine=coroutine,
            interval_seconds=interval_seconds,
            max_errors=max_errors
        )
        logger.info(f"新增排程任務: {name} (每 {interval_seconds} 秒)")

    def remove_task(self, name: str) -> None:
        """移除排程任務"""
        if name in self.tasks:
            del self.tasks[name]
            logger.info(f"移除排程任務: {name}")

    async def start(self) -> None:
        """啟動排程器"""
        if self._running:
            return

        self._running = True
        self._task_handle = asyncio.create_task(self._run_loop())
        logger.info("背景排程器已啟動")

    async def stop(self) -> None:
        """停止排程器"""
        self._running = False

        if self._task_handle:
            self._task_handle.cancel()
            try:
                await self._task_handle
            except asyncio.CancelledError:
                pass

        logger.info("背景排程器已停止")

    async def _run_loop(self) -> None:
        """主執行迴圈"""
        while self._running:
            now = datetime.now()

            for task in self.tasks.values():
                # 檢查是否需要執行
                if task.is_running:
                    continue

                if task.next_run and now < task.next_run:
                    continue

                # 檢查錯誤次數
                if task.error_count >= task.max_errors:
                    logger.error(f"任務 {task.name} 錯誤次數過多，已停用")
                    continue

                # 執行任務
                asyncio.create_task(self._execute_task(task))

            # 每秒檢查一次
            await asyncio.sleep(1)

    async def _execute_task(self, task: ScheduledTask) -> None:
        """執行單個任務"""
        task.is_running = True
        task.last_run = datetime.now()

        try:
            logger.debug(f"執行任務: {task.name}")
            await task.coroutine()
            task.error_count = 0
            logger.debug(f"任務完成: {task.name}")
        except Exception as e:
            task.error_count += 1
            logger.error(f"任務 {task.name} 執行失敗 ({task.error_count}/{task.max_errors}): {e}")
        finally:
            task.is_running = False
            task.next_run = datetime.now() + timedelta(seconds=task.interval_seconds)

    def get_status(self) -> Dict:
        """取得排程器狀態"""
        return {
            "running": self._running,
            "tasks": [
                {
                    "name": task.name,
                    "interval": task.interval_seconds,
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "next_run": task.next_run.isoformat() if task.next_run else None,
                    "is_running": task.is_running,
                    "error_count": task.error_count
                }
                for task in self.tasks.values()
            ]
        }


# 全域排程器實例
_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> BackgroundScheduler:
    """取得全域排程器實例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler
