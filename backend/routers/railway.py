"""
台鐵 API 路由模組
提供台鐵時刻表查詢和車站列表功能
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List
from datetime import datetime

from models.railway_models import TrainStation, TrainTimeEntry
from scrapers.railway_scraper import TaiwanRailwayScraper

router = APIRouter(prefix="/api/railway", tags=["railway"])

# 初始化爬蟲實例
railway_scraper = TaiwanRailwayScraper()


@router.get("/stations", response_model=List[TrainStation])
async def get_railway_stations():
    """
    取得台鐵所有車站列表

    Returns:
        List[TrainStation]: 台鐵車站列表，包含車站代碼、中文名稱和英文名稱
    """
    stations = []
    for code, name in TaiwanRailwayScraper.STATIONS.items():
        stations.append(TrainStation(
            station_code=code,
            station_name=name,
            station_name_en=name
        ))
    return stations


@router.get("/timetable", response_model=List[TrainTimeEntry])
async def get_railway_timetable(
    from_station: str = Query(..., description="出發站代碼或名稱，例如：108（台北）或 212（台中）"),
    to_station: str = Query(..., description="抵達站代碼或名稱，例如：108（台北）或 212（台中）"),
    date: str = Query(None, description="日期格式 YYYY/MM/DD，預設為今天"),
    time: str = Query(None, description="時間格式 HH:MM，預設為現在時間")
):
    """
    查詢台鐵時刻表

    根據起訖站和日期時間查詢火車班次資訊，
    包含車次、車種、出發時間、到達時間、行車時間等。

    Args:
        from_station: 出發站代碼（如 "108"）或站名（如 "台北"）
        to_station: 抵達站代碼（如 "212"）或站名（如 "台中"）
        date: 乘車日期，格式 YYYY/MM/DD，預設為今天
        time: 出發時間，格式 HH:MM，預設為現在時間

    Returns:
        List[TrainTimeEntry]: 符合條件的火車班次列表

    Raises:
        HTTPException: 當查詢失敗時返回 500 錯誤
    """
    try:
        results = await railway_scraper.search_timetable(
            from_station, to_station, date, time
        )
        return results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"台鐵時刻表查詢失敗: {str(e)}"
        )
