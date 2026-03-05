"""
基礎爬蟲類別 - 定義所有爬蟲的通用介面

這個模組就像是一個「爬蟲藍圖」，規定了所有交通爬蟲應該要有的基本功能。
就像蓋房子需要藍圖一樣，寫爬蟲也需要統一的規範，這樣不同的交通方式
（公車、台鐵、高鐵）都能有一致的呼叫方式。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

# 設定日誌記錄，方便除錯時追蹤問題
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    基礎爬蟲抽象類別

    這是所有交通爬蟲的爸爸（父類別），定義了共同的方法。
    不管是要查公車、火車還是高鐵，都可以使用相同的介面來操作。

    使用方式：
        class MyScraper(BaseScraper):
            async def search_timetable(self, ...):
                # 實作查詢時刻表的邏輯
                pass
    """

    def __init__(self, name: str):
        """
        初始化爬蟲

        Args:
            name: 爬蟲名稱，用於日誌識別
        """
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self._http_client = None

    @abstractmethod
    async def search_timetable(
        self,
        from_station: str,
        to_station: str,
        date: Optional[str] = None,
        time: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        查詢時刻表 - 所有子類別必須實作這個方法

        Args:
            from_station: 出發站名稱或代碼
            to_station: 抵達站名稱或代碼
            date: 日期 (格式依各爬蟲而定)
            time: 時間 (格式依各爬蟲而定)

        Returns:
            List[Dict]: 時刻表資料列表
        """
        pass

    async def close(self):
        """
        清理資源 - 關閉 HTTP client 等連線

        就像用完電腦要關機一樣，爬蟲用完也要釋放資源，
        避免造成系統負擔或連線數過多。
        """
        if self._http_client:
            try:
                await self._http_client.aclose()
                self.logger.info(f"{self.name} HTTP client 已關閉")
            except Exception as e:
                self.logger.warning(f"關閉 {self.name} HTTP client 時發生錯誤: {e}")
            finally:
                self._http_client = None

    def _format_date(self, date_str: Optional[str]) -> str:
        """
        格式化日期字串

        把各種日期格式統一轉換成標準格式，
        就像把不同語言翻譯成共同語言一樣。

        Args:
            date_str: 原始日期字串，可以是 "2024/03/15" 或 "2024-03-15"

        Returns:
            str: 格式化後的日期字串
        """
        if not date_str:
            return datetime.now().strftime("%Y/%m/%d")

        # 嘗試解析不同格式的日期
        for fmt in ["%Y/%m/%d", "%Y-%m-%d", "%Y%m%d"]:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y/%m/%d")
            except ValueError:
                continue

        # 如果無法解析，直接回傳原始值
        return date_str

    def _calculate_duration(self, dep_time: str, arr_time: str) -> str:
        """
        計算行程時間

        根據出發和抵達時間，算出總共要花多久時間。
        就像你會算從家裡到公司需要幾分鐘一樣。

        Args:
            dep_time: 出發時間 "HH:MM"
            arr_time: 抵達時間 "HH:MM"

        Returns:
            str: 行程時間 "H:MM"
        """
        try:
            dep_h, dep_m = map(int, dep_time.split(':'))
            arr_h, arr_m = map(int, arr_time.split(':'))

            diff_m = (arr_h * 60 + arr_m) - (dep_h * 60 + dep_m)

            # 處理跨日的情況（例如晚上11點出發，凌晨1點抵達）
            if diff_m < 0:
                diff_m += 24 * 60

            return f"{diff_m // 60}:{diff_m % 60:02d}"
        except Exception as e:
            self.logger.warning(f"計算行程時間失敗: {e}")
            return "N/A"
