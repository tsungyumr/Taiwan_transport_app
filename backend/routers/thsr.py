"""
高鐵 API 路由模組
提供高鐵時刻表查詢和車站列表功能
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List

from models.thsr_models import THSRStation, THSRTrainEntry
from scrapers.thsr_scraper import THSRScraper

router = APIRouter(prefix="/api/thsr", tags=["thsr"])

# 初始化爬蟲實例
thsr_scraper = THSRScraper()


@router.get("/stations", response_model=List[THSRStation])
async def get_thsr_stations():
    """
    取得高鐵所有車站列表

    Returns:
        List[THSRStation]: 高鐵車站列表，包含車站代碼和名稱
    """
    stations = []
    for code, name in THSRScraper.STATIONS.items():
        stations.append(THSRStation(code=code, name=name))
    return stations


@router.get("/timetable", response_model=List[THSRTrainEntry])
async def get_thsr_timetable(
    from_station: str = Query(..., description="出發站代碼，例如：TPE（台北）、TCH（台中）、ZUY（左營）"),
    to_station: str = Query(..., description="抵達站代碼，例如：TPE（台北）、TCH（台中）、ZUY（左營）"),
    date: str = Query(None, description="日期格式 YYYY-MM-DD，預設為今天")
):
    """
    查詢高鐵時刻表

    根據起訖站和日期查詢高鐵班次資訊，
    包含車次、出發時間、到達時間、座位 availability 等。

    Args:
        from_station: 出發站代碼（如 "TPE"）
        to_station: 抵達站代碼（如 "ZUY"）
        date: 乘車日期，格式 YYYY-MM-DD，預設為今天

    Returns:
        List[THSRTrainEntry]: 符合條件的高鐵班次列表

    Raises:
        HTTPException: 當查詢失敗時返回 500 錯誤
    """
    try:
        results = await thsr_scraper.search_timetable(
            from_station, to_station, date
        )
        return results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"高鐵時刻表查詢失敗: {str(e)}"
        )
