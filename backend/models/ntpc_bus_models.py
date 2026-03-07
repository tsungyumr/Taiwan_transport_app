"""
新北市公車 CSV 資料模型
對應新北市政府開放資料平台的 CSV 欄位

資料來源：
1. 公車站位資訊：https://data.ntpc.gov.tw/api/datasets/34b402a8-53d9-483d-9406-24a682c2d6dc/csv/file
2. 公車路線清單：https://data.ntpc.gov.tw/api/datasets/0ee4e6bf-cee6-4ec8-8fe1-71f544015127/csv/file
3. 公車預估到站時間：https://data.ntpc.gov.tw/api/datasets/07f7ccb3-ed00-43c4-966d-08e9dab24e95/csv/file
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import time


class BusStopInfo(BaseModel):
    """
    公車站位資訊
    對應 CSV: 公車站位資訊

    Attributes:
        stop_id: 站牌代碼 (id)
        route_id: 所屬路線代碼 (routeid)
        name_zh: 中文名稱 (namezh)
        name_en: 英文名稱 (nameen)
        sequence: 於路線上的順序 (seqno)
        pgp: 上下車站別 (pgp)
        direction: 去返程 (goback: 0=去程, 1=返程)
        longitude: 經度
        latitude: 緯度
        address: 地址
        stop_location_id: 站位代碼 (stoplocationid)
        show_lon: 顯示用經度 (showlon)
        show_lat: 顯示用緯度 (showlat)
        vector: 向量角
    """
    stop_id: str = Field(..., description="站牌代碼")
    route_id: str = Field(..., description="所屬路線代碼")
    name_zh: str = Field(..., description="中文名稱")
    name_en: Optional[str] = Field(None, description="英文名稱")
    sequence: int = Field(..., description="於路線上的順序", ge=0)
    pgp: Optional[str] = Field(None, description="上下車站別")
    direction: int = Field(..., description="去返程 (0=去程, 1=返程)")
    longitude: Optional[float] = Field(None, description="經度")
    latitude: Optional[float] = Field(None, description="緯度")
    address: Optional[str] = Field(None, description="地址")
    stop_location_id: Optional[str] = Field(None, description="站位代碼")
    show_lon: Optional[float] = Field(None, description="顯示用經度")
    show_lat: Optional[float] = Field(None, description="顯示用緯度")
    vector: Optional[int] = Field(None, description="向量角")

    @classmethod
    def from_csv_row(cls, row: dict) -> "BusStopInfo":
        """從 CSV 行資料建立模型實例（處理 BOM 字元）"""
        # 處理可能包含 BOM 的欄位名稱
        def get_field(field_names):
            for name in field_names:
                if name in row:
                    return row.get(name, '')
                # 嘗試帶 BOM 的版本
                bom_name = '\ufeff' + name
                if bom_name in row:
                    return row.get(bom_name, '')
            return ''

        return cls(
            stop_id=get_field(['id']),
            route_id=get_field(['routeid']),
            name_zh=get_field(['namezh']),
            name_en=get_field(['nameen']) or None,
            sequence=int(get_field(['seqno'])) if get_field(['seqno']) else 0,
            pgp=get_field(['pgp']) or None,
            direction=int(get_field(['goback'])) if get_field(['goback']) else 0,
            longitude=float(get_field(['longitude'])) if get_field(['longitude']) else None,
            latitude=float(get_field(['latitude'])) if get_field(['latitude']) else None,
            address=get_field(['address']) or None,
            stop_location_id=get_field(['stoplocationid']) or None,
            show_lon=float(get_field(['showlon'])) if get_field(['showlon']) else None,
            show_lat=float(get_field(['showlat'])) if get_field(['showlat']) else None,
            vector=int(get_field(['vector'])) if get_field(['vector']) else None
        )

    class Config:
        json_schema_extra = {
            "example": {
                "stop_id": "2347",
                "route_id": "935",
                "name_zh": "捷運新埔站",
                "name_en": "MRT Xinpu Station",
                "sequence": 1,
                "pgp": "0",
                "direction": 0,
                "longitude": 121.4665,
                "latitude": 25.0228,
                "address": "民生路3段",
                "stop_location_id": "2347",
                "show_lon": 121.4665,
                "show_lat": 25.0228,
                "vector": 90
            }
        }


class BusRouteInfo(BaseModel):
    """
    公車路線清單資訊
    對應 CSV: 公車路線清單

    Attributes:
        route_id: 路線代碼 (id)
        provider_id: 業者代碼 (providerid)
        provider_name: 業者中文名稱 (providername)
        name_zh: 中文名稱 (namezh)
        name_en: 英文名稱 (nameen)
        path_attribute_id: 所屬附屬路線代碼 (pathattributeid)
        path_attribute_name: 所屬附屬路線中文名稱 (pathattributename)
        departure_zh: 去程第1站起站中文名稱
        departure_en: 去程第1站起站英文名稱
        destination_zh: 回程第1站訖站中文名稱
        destination_en: 回程第1站訖站英文名稱
        go_first_bus_time: 去程第一班發車時間
        back_first_bus_time: 回程第一班發車時間
        go_last_bus_time: 去程最後一班發車時間
        back_last_bus_time: 回程最後一班發車時間
        peak_headway: 尖峰時段發車間隔
        off_peak_headway: 離峰時段發車間隔
        bus_time_desc: 平日頭末班描述
        headway_desc: 平日發車間距描述
        ticket_price_desc_zh: 票價描述-中文
    """
    route_id: str = Field(..., description="路線代碼")
    provider_id: Optional[str] = Field(None, description="業者代碼")
    provider_name: str = Field(..., description="業者中文名稱")
    name_zh: str = Field(..., description="中文名稱")
    name_en: Optional[str] = Field(None, description="英文名稱")
    path_attribute_id: Optional[str] = Field(None, description="所屬附屬路線代碼")
    path_attribute_name: Optional[str] = Field(None, description="所屬附屬路線中文名稱")
    path_attribute_name_en: Optional[str] = Field(None, description="所屬附屬路線英文名稱")
    departure_zh: str = Field(..., description="去程起站中文名稱")
    departure_en: Optional[str] = Field(None, description="去程起站英文名稱")
    destination_zh: str = Field(..., description="回程終站中文名稱")
    destination_en: Optional[str] = Field(None, description="回程終站英文名稱")
    real_sequence: Optional[int] = Field(None, description="核定總班次")
    distance: Optional[float] = Field(None, description="總往返里程")
    go_first_bus_time: Optional[str] = Field(None, description="去程第一班發車時間")
    back_first_bus_time: Optional[str] = Field(None, description="回程第一班發車時間")
    go_last_bus_time: Optional[str] = Field(None, description="去程最後一班發車時間")
    back_last_bus_time: Optional[str] = Field(None, description="回程最後一班發車時間")
    peak_headway: Optional[str] = Field(None, description="尖峰時段發車間隔")
    off_peak_headway: Optional[str] = Field(None, description="離峰時段發車間隔")
    bus_time_desc: Optional[str] = Field(None, description="平日頭末班描述")
    headway_desc: Optional[str] = Field(None, description="平日發車間距描述")
    holiday_go_first_bus_time: Optional[str] = Field(None, description="假日去程第一班發車時間")
    holiday_back_first_bus_time: Optional[str] = Field(None, description="假日回程第一班發車時間")
    holiday_go_last_bus_time: Optional[str] = Field(None, description="假日去程最後一班發車時間")
    holiday_back_last_bus_time: Optional[str] = Field(None, description="假日回程最後一班發車時間")
    holiday_bus_time_desc: Optional[str] = Field(None, description="假日頭末班描述")
    holiday_peak_headway: Optional[str] = Field(None, description="假日尖峰時段發車間隔")
    holiday_off_peak_headway: Optional[str] = Field(None, description="假日離峰時段發車間隔")
    holiday_headway_desc: Optional[str] = Field(None, description="假日發車間距描述")
    segment_buffer_zh: Optional[str] = Field(None, description="分段緩衝區-中文")
    segment_buffer_en: Optional[str] = Field(None, description="分段緩衝區-英文")
    ticket_price_desc_zh: Optional[str] = Field(None, description="票價描述-中文")
    ticket_price_desc_en: Optional[str] = Field(None, description="票價描述-英文")

    @classmethod
    def from_csv_row(cls, row: dict) -> "BusRouteInfo":
        """從 CSV 行資料建立模型實例（處理 BOM 字元）"""
        def get_field(field_names):
            for name in field_names:
                if name in row:
                    return row.get(name, '')
                bom_name = '\ufeff' + name
                if bom_name in row:
                    return row.get(bom_name, '')
            return ''

        def get_int_field(field_names):
            val = get_field(field_names)
            return int(val) if val else None

        def get_float_field(field_names):
            val = get_field(field_names)
            return float(val) if val else None

        return cls(
            route_id=get_field(['id']),
            provider_id=get_field(['providerid']) or None,
            provider_name=get_field(['providername']),
            name_zh=get_field(['namezh']),
            name_en=get_field(['nameen']) or None,
            path_attribute_id=get_field(['pathattributeid']) or None,
            path_attribute_name=get_field(['pathattributename']) or None,
            path_attribute_name_en=get_field(['pathattributeename']) or None,
            departure_zh=get_field(['departurezh']),
            departure_en=get_field(['departureen']) or None,
            destination_zh=get_field(['destinationzh']),
            destination_en=get_field(['destinationen']) or None,
            real_sequence=get_int_field(['realsequence']),
            distance=get_float_field(['distance']),
            go_first_bus_time=get_field(['gofirstbustime']) or None,
            back_first_bus_time=get_field(['backfirstbustime']) or None,
            go_last_bus_time=get_field(['golastbustime']) or None,
            back_last_bus_time=get_field(['backlastbustime']) or None,
            peak_headway=get_field(['peakheadway']) or None,
            off_peak_headway=get_field(['offpeakheadway']) or None,
            bus_time_desc=get_field(['bustimedesc']) or None,
            headway_desc=get_field(['headwaydesc']) or None,
            holiday_go_first_bus_time=get_field(['holidaygofirstbustime']) or None,
            holiday_back_first_bus_time=get_field(['holidaybackfirstbustime']) or None,
            holiday_go_last_bus_time=get_field(['holidaygolastbustime']) or None,
            holiday_back_last_bus_time=get_field(['holidaybacklastbustime']) or None,
            holiday_bus_time_desc=get_field(['holidaybustimedesc']) or None,
            holiday_peak_headway=get_field(['holidaypeakheadway']) or None,
            holiday_off_peak_headway=get_field(['holidayoffpeakheadway']) or None,
            holiday_headway_desc=get_field(['holidayheadwaydesc']) or None,
            segment_buffer_zh=get_field(['segmentbufferzh']) or None,
            segment_buffer_en=get_field(['segmentbufferen']) or None,
            ticket_price_desc_zh=get_field(['ticketpricedescriptionzh']) or None,
            ticket_price_desc_en=get_field(['ticketpricedescriptionen']) or None
        )

    def get_display_name(self) -> str:
        """取得顯示用路線名稱"""
        return f"{self.name_zh}"

    def get_direction_name(self, direction: int) -> str:
        """取得方向名稱"""
        if direction == 0:
            return f"往{self.destination_zh}"
        else:
            return f"往{self.departure_zh}"

    class Config:
        json_schema_extra = {
            "example": {
                "route_id": "935",
                "provider_id": "1001",
                "provider_name": "台北客運",
                "name_zh": "935",
                "name_en": "935",
                "departure_zh": "林口",
                "destination_zh": "捷運新埔站",
                "go_first_bus_time": "05:30",
                "go_last_bus_time": "22:30",
                "peak_headway": "10-15",
                "off_peak_headway": "15-20"
            }
        }


class BusEstimation(BaseModel):
    """
    公車預估到站時間
    對應 CSV: 公車預估到站時間

    Attributes:
        route_id: 路線代碼
        stop_id: 站牌代碼
        estimate_seconds: 預估到站剩餘時間（秒）
        direction: 去返程 (0=去程, 1=返程)
    """
    route_id: str = Field(..., description="路線代碼")
    stop_id: str = Field(..., description="站牌代碼")
    estimate_seconds: int = Field(..., description="預估到站剩餘時間（秒，負值表示已離站）")
    direction: int = Field(..., description="去返程 (0=去程, 1=返程)")

    @classmethod
    def from_csv_row(cls, row: dict) -> "BusEstimation":
        """從 CSV 行資料建立模型實例（處理 BOM 字元）"""
        def get_field(field_names):
            for name in field_names:
                if name in row:
                    return row.get(name, '')
                bom_name = '\ufeff' + name
                if bom_name in row:
                    return row.get(bom_name, '')
            return ''

        return cls(
            route_id=get_field(['routeid']),
            stop_id=get_field(['stopid']),
            estimate_seconds=int(get_field(['estimatetime'])) if get_field(['estimatetime']) else 0,
            direction=int(get_field(['goback'])) if get_field(['goback']) else 0
        )

    def get_estimate_text(self) -> str:
        """
        取得人類可讀的預估時間文字

        Returns:
            如 "即將進站"、"3 分鐘"、"尚未發車"、"已離站"
        """
        if self.estimate_seconds == 0:
            return "尚未發車"
        elif self.estimate_seconds < 0:
            return "已離站"
        elif self.estimate_seconds <= 60:
            return "即將進站"
        elif self.estimate_seconds < 3600:
            minutes = self.estimate_seconds // 60
            return f"{minutes} 分鐘"
        else:
            hours = self.estimate_seconds // 3600
            minutes = (self.estimate_seconds % 3600) // 60
            return f"{hours} 小時 {minutes} 分鐘"

    def get_status(self) -> str:
        """
        取得車輛狀態

        Returns:
            not_started: 尚未發車
            departed: 已離站
            arriving: 即將進站 (< 1分鐘)
            near: 接近中 (< 3分鐘)
            normal: 正常行駛中
        """
        if self.estimate_seconds == 0:
            return "not_started"
        elif self.estimate_seconds < 0:
            return "departed"
        elif self.estimate_seconds <= 60:
            return "arriving"
        elif self.estimate_seconds <= 180:
            return "near"
        else:
            return "normal"

    class Config:
        json_schema_extra = {
            "example": {
                "route_id": "935",
                "stop_id": "2347",
                "estimate_seconds": 180,
                "direction": 0
            }
        }


class BusStopWithETA(BaseModel):
    """
    帶有到站時間的站牌資訊
    整合 BusStopInfo 與 BusEstimation

    Attributes:
        stop_id: 站牌代碼
        name_zh: 中文名稱
        sequence: 站序
        direction: 去返程
        longitude: 經度
        latitude: 緯度
        estimate_seconds: 預估到站秒數
        estimate_text: 預估到站文字
        status: 車輛狀態
    """
    stop_id: str = Field(..., description="站牌代碼")
    name_zh: str = Field(..., description="中文名稱")
    sequence: int = Field(..., description="站序")
    direction: int = Field(..., description="去返程")
    longitude: Optional[float] = Field(None, description="經度")
    latitude: Optional[float] = Field(None, description="緯度")
    estimate_seconds: Optional[int] = Field(None, description="預估到站秒數")
    estimate_text: str = Field("無資料", description="預估到站文字")
    status: str = Field("normal", description="車輛狀態")

    @classmethod
    def from_stop_and_estimation(
        cls,
        stop: BusStopInfo,
        estimation: Optional[BusEstimation] = None
    ) -> "BusStopWithETA":
        """從站牌資訊和預估資料建立"""
        if estimation:
            return cls(
                stop_id=stop.stop_id,
                name_zh=stop.name_zh,
                sequence=stop.sequence,
                direction=stop.direction,
                longitude=stop.longitude,
                latitude=stop.latitude,
                estimate_seconds=estimation.estimate_seconds,
                estimate_text=estimation.get_estimate_text(),
                status=estimation.get_status()
            )
        else:
            return cls(
                stop_id=stop.stop_id,
                name_zh=stop.name_zh,
                sequence=stop.sequence,
                direction=stop.direction,
                longitude=stop.longitude,
                latitude=stop.latitude,
                estimate_seconds=None,
                estimate_text="無資料",
                status="normal"
            )


class BusRouteSummary(BaseModel):
    """
    公車路線摘要資訊
    用於路線列表顯示

    Attributes:
        route_id: 路線代碼
        name_zh: 中文名稱
        provider_name: 業者名稱
        departure_zh: 起點站
        destination_zh: 終點站
        first_bus_time: 首班車時間
        last_bus_time: 末班車時間
        headway_desc: 發車間距描述
    """
    route_id: str = Field(..., description="路線代碼")
    name_zh: str = Field(..., description="中文名稱")
    provider_name: str = Field(..., description="業者名稱")
    departure_zh: str = Field(..., description="起點站")
    destination_zh: str = Field(..., description="終點站")
    first_bus_time: Optional[str] = Field(None, description="首班車時間")
    last_bus_time: Optional[str] = Field(None, description="末班車時間")
    headway_desc: Optional[str] = Field(None, description="發車間距描述")

    @classmethod
    def from_route_info(cls, route: BusRouteInfo) -> "BusRouteSummary":
        """從路線詳細資訊建立摘要"""
        return cls(
            route_id=route.route_id,
            name_zh=route.name_zh,
            provider_name=route.provider_name,
            departure_zh=route.departure_zh,
            destination_zh=route.destination_zh,
            first_bus_time=route.go_first_bus_time,
            last_bus_time=route.go_last_bus_time,
            headway_desc=route.headway_desc
        )
