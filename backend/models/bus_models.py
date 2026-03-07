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


# ==================== 新北市 CSV 資料整合模型 ====================

class BusRouteNTPC(BaseModel):
    """
    新北市公車路線 API 回應模型
    與現有 Flutter App 相容的格式

    Attributes:
        route_id: 路線代碼
        route_name: 路線名稱
        departure_stop: 起點站名稱
        arrival_stop: 終點站名稱
        operator: 營運業者名稱
        first_bus_time: 首班車時間
        last_bus_time: 末班車時間
        headway_desc: 發車間距描述
    """
    route_id: str = Field(description="路線代碼")
    route_name: str = Field(description="路線名稱")
    departure_stop: str = Field(description="起點站")
    arrival_stop: str = Field(description="終點站")
    operator: str = Field(description="營運業者")
    first_bus_time: Optional[str] = Field(None, description="首班車時間")
    last_bus_time: Optional[str] = Field(None, description="末班車時間")
    headway_desc: Optional[str] = Field(None, description="發車間距描述")

    @classmethod
    def from_ntpc_route_info(cls, route_info) -> "BusRouteNTPC":
        """從 NTPC BusRouteInfo 轉換"""
        return cls(
            route_id=route_info.route_id,
            route_name=route_info.name_zh,
            departure_stop=route_info.departure_zh,
            arrival_stop=route_info.destination_zh,
            operator=route_info.provider_name,
            first_bus_time=route_info.go_first_bus_time,
            last_bus_time=route_info.go_last_bus_time,
            headway_desc=route_info.headway_desc
        )


class BusStopNTPC(BaseModel):
    """
    新北市公車站牌 API 回應模型
    擴展現有 BusStop 格式

    Attributes:
        stop_id: 站牌代碼
        sequence: 站序
        name: 站牌名稱
        eta: 預估到站時間文字
        status: 車輛狀態 (not_started/arriving/near/normal)
        longitude: 經度
        latitude: 緯度
    """
    stop_id: str = Field(description="站牌代碼")
    sequence: int = Field(description="站序")
    name: str = Field(description="站牌名稱")
    eta: str = Field(description="預估到站時間")
    status: str = Field(default="normal", description="車輛狀態")
    longitude: Optional[float] = Field(None, description="經度")
    latitude: Optional[float] = Field(None, description="緯度")


class BusRouteDetailNTPC(BaseModel):
    """
    新北市公車路線詳細資料 API 回應
    與現有 BusRouteData 相容並擴充

    Attributes:
        route: 路線代碼
        route_name: 路線名稱
        direction: 方向 (0=去程, 1=返程)
        direction_name: 方向名稱
        departure: 起點站
        destination: 終點站
        stops: 站點列表
        buses: 行駛中車輛列表（目前 CSV 無此資料，保留相容性）
        updated: 資料更新時間
    """
    route: str = Field(description="路線代碼")
    route_name: str = Field(description="路線名稱")
    direction: int = Field(default=0, description="方向 (0=去程, 1=返程)")
    direction_name: str = Field(description="方向名稱")
    departure: str = Field(description="起點站")
    destination: str = Field(description="終點站")
    stops: List[BusStopNTPC] = Field(description="站點列表")
    buses: List[BusVehicle] = Field(default=[], description="車輛列表")
    updated: str = Field(description="更新時間")


class BusEstimationResponse(BaseModel):
    """
    公車預估到站時間 API 回應

    Attributes:
        route_id: 路線代碼
        stop_id: 站牌代碼
        stop_name: 站牌名稱
        direction: 方向
        estimate_seconds: 預估到站秒數
        estimate_text: 預估到站文字
        status: 車輛狀態
        updated: 資料更新時間
    """
    route_id: str = Field(description="路線代碼")
    stop_id: str = Field(description="站牌代碼")
    stop_name: Optional[str] = Field(None, description="站牌名稱")
    direction: int = Field(description="方向")
    estimate_seconds: int = Field(description="預估到站秒數")
    estimate_text: str = Field(description="預估到站文字")
    status: str = Field(description="車輛狀態")
    updated: str = Field(description="更新時間")
