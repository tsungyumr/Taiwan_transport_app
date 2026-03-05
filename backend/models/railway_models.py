"""
台鐵相關資料模型
定義台鐵車站、時刻表等資料結構
"""

from pydantic import BaseModel, Field
from typing import Optional


class TrainStation(BaseModel):
    """
    台鐵車站資訊

    Attributes:
        station_code: 車站代碼 (如 "108" 代表台北)
        station_name: 車站中文名稱
        station_name_en: 車站英文名稱
    """
    station_code: str = Field(description="車站代碼")
    station_name: str = Field(description="車站名稱")
    station_name_en: str = Field(description="英文名稱")


class TrainTimeEntry(BaseModel):
    """
    台鐵時刻表項目

    Attributes:
        train_no: 車次號碼
        train_type: 列車種類 (自強、莒光、區間車等)
        departure_station: 出發站名稱
        arrival_station: 抵達站名稱
        departure_time: 出發時間 (HH:MM)
        arrival_time: 抵達時間 (HH:MM)
        duration: 行車時間 (如 "1:45")
        transferable: 是否可轉乘
    """
    train_no: str = Field(description="車次號碼")
    train_type: str = Field(description="列車種類")
    departure_station: str = Field(description="出發站")
    arrival_station: str = Field(description="抵達站")
    departure_time: str = Field(description="出發時間")
    arrival_time: str = Field(description="抵達時間")
    duration: Optional[str] = Field(default=None, description="行車時間")
    transferable: bool = Field(default=True, description="是否可轉乘")


class RailwayTimetableQuery(BaseModel):
    """
    台鐵時刻表查詢參數

    Attributes:
        from_station: 出發站名稱或代碼
        to_station: 抵達站名稱或代碼
        date: 日期 (YYYY/MM/DD)，預設為今天
        time: 時間 (HH:MM)，預設為現在
    """
    from_station: str = Field(description="出發站")
    to_station: str = Field(description="抵達站")
    date: Optional[str] = Field(default=None, description="日期")
    time: Optional[str] = Field(default=None, description="時間")
