"""
高鐵相關資料模型
定義高鐵車站、時刻表等資料結構
"""

from pydantic import BaseModel, Field


class THSRStation(BaseModel):
    """
    高鐵站點資訊

    Attributes:
        name: 站點中文名稱
        code: 站點代碼 (如 "TPE" 代表台北)
        info: 站點詳細資訊
        timestamp: 資料抓取時間
    """
    name: str = Field(description="站點名稱")
    code: str = Field(description="站點代碼")
    info: str = Field(description="詳細資訊")
    timestamp: str = Field(description="抓取時間")


class THSRTrainEntry(BaseModel):
    """
    高鐵時刻表項目

    Attributes:
        train_no: 車次號碼
        departure_station: 出發站名稱
        arrival_station: 抵達站名稱
        departure_time: 出發時間 (HH:MM)
        arrival_time: 抵達時間 (HH:MM)
        duration: 行車時間
        business_seat_available: 商務艙是否有座
        standard_seat_available: 標準艙是否有座
        free_seat_available: 自由座是否有座
    """
    train_no: str = Field(description="車次號碼")
    departure_station: str = Field(description="出發站")
    arrival_station: str = Field(description="抵達站")
    departure_time: str = Field(description="出發時間")
    arrival_time: str = Field(description="抵達時間")
    duration: str = Field(description="行車時間")
    business_seat_available: bool = Field(description="商務艙座位")
    standard_seat_available: bool = Field(description="標準艙座位")
    free_seat_available: bool = Field(description="自由座座位")
