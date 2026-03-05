"""
公車相關資料模型
定義公車路線、時刻表、即時到站等資料結構
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class BusRoute(BaseModel):
    """
    公車路線基本資訊

    Attributes:
        route_id: 路線代碼 (如 "235", "307")
        route_name: 路線名稱
        departure_stop: 起點站名稱
        arrival_stop: 終點站名稱
        operator: 營運業者名稱
    """
    route_id: str = Field(description="路線代碼")
    route_name: str = Field(description="路線名稱")
    departure_stop: str = Field(description="起點站")
    arrival_stop: str = Field(description="終點站")
    operator: str = Field(description="營運業者")


class BusTimeEntry(BaseModel):
    """
    公車時刻表項目

    Attributes:
        stop_name: 站牌名稱
        arrival_time: 到站時間 (HH:MM)
        route_name: 所屬路線名稱
    """
    stop_name: str = Field(description="站牌名稱")
    arrival_time: str = Field(description="到站時間")
    route_name: str = Field(description="路線名稱")


class BusRealTimeArrival(BaseModel):
    """
    公車即時到站資訊回應

    Attributes:
        route_id: 路線代碼
        route_name: 路線名稱
        current_time: 目前時間
        arrivals: 到站資訊列表
    """
    route_id: str = Field(description="路線代碼")
    route_name: str = Field(description="路線名稱")
    current_time: str = Field(description="目前時間")
    arrivals: List[Dict] = Field(description="到站資訊列表")


class BusStop(BaseModel):
    """
    公車站牌資訊

    Attributes:
        name: 站牌名稱
        eta: 預估到站時間文字
    """
    name: str = Field(description="站牌名稱")
    eta: str = Field(description="預估到站時間")


class BusVehicle(BaseModel):
    """
    公車車輛即時資訊

    Attributes:
        id: 車牌號碼
        at_stop: 目前在第幾站
        eta_next: 到下一站預估時間
        heading_to: 前往第幾站
    """
    id: str = Field(description="車牌號碼")
    at_stop: int = Field(description="目前在第幾站")
    eta_next: str = Field(description="到下一站預估時間")
    heading_to: int = Field(description="前往第幾站")


class BusRouteData(BaseModel):
    """
    完整公車路線資料 (站點 + 車輛位置)

    Attributes:
        route: 路線代碼
        stops: 站點列表
        buses: 行駛中車輛列表
        updated: 資料更新時間
    """
    route: str = Field(description="路線代碼")
    stops: List[BusStop] = Field(description="站點列表")
    buses: List[BusVehicle] = Field(description="車輛列表")
    updated: str = Field(description="更新時間")
