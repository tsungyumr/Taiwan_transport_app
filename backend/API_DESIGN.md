# UBike API 設計文件

## 概述

本文檔定義 UBike 腳踏車租借站 API 的設計規格，包含 TDX API 對接、內部 API 端點、資料模型與快取策略。

## TDX API 參考

### 端點資訊

| 端點 | 說明 | 文件連結 |
|------|------|----------|
| `GET /Bike/Station/City/{City}` | 取得縣市腳踏車租借站資訊 | [Swagger](https://tdx.transportdata.tw/api-service/swagger/basic/2998e851-81d0-40f5-b26d-77e2f5ac4118#/Bike/BikeApi_Station_2150) |
| `GET /Bike/Availability/City/{City}` | 取得即時車位資訊 | [Swagger](https://tdx.transportdata.tw/api-service/swagger/basic/2998e851-81d0-40f5-b26d-77e2f5ac4118#/Bike/BikeApi_Availability_2151) |

### 支援縣市代碼

| 縣市名稱 | TDX 代碼 |
|---------|---------|
| 台北市 | Taipei |
| 新北市 | NewTaipei |
| 桃園市 | Taoyuan |
| 台中市 | Taichung |
| 台南市 | Tainan |
| 高雄市 | Kaohsiung |
| 新竹市 | Hsinchu |
| 新竹縣 | HsinchuCounty |
| 苗栗縣 | MiaoliCounty |
| 彰化縣 | ChanghuaCounty |
| 屏東縣 | PingtungCounty |

### TDX 回傳格式

#### Station 回傳範例
```json
{
  "StationUID": "TPE0001",
  "StationID": "0001",
  "ServiceType": 1,
  "ServiceStatus": 1,
  "StationName": {
    "Zh_tw": "捷運市政府站(3號出口)",
    "En": "MRT Taipei City Hall Stn.(Exit 3)"
  },
  "StationPosition": {
    "PositionLon": 121.564812,
    "PositionLat": 25.040857,
    "GeoHash": "wsqqmjb8h"
  },
  "StationAddress": {
    "Zh_tw": "忠孝東路/松仁路(東南側)",
    "En": "Sec. 5, Zhongxiao E. Rd./Songren Rd."
  },
  "BikesCapacity": 60,
  "SrcUpdateTime": "2024-01-15T08:30:00+08:00",
  "UpdateTime": "2024-01-15T08:32:15+08:00"
}
```

#### Availability 回傳範例
```json
{
  "StationUID": "TPE0001",
  "StationID": "0001",
  "ServiceType": 1,
  "ServiceStatus": 1,
  "AvailableRentBikes": 15,
  "AvailableReturnBikes": 45,
  "SrcUpdateTime": "2024-01-15T08:30:05+08:00",
  "UpdateTime": "2024-01-15T08:32:15+08:00",
  "AvailableRentBikesDetail": {
    "GeneralBikes": 10,
    "ElectricBikes": 5
  }
}
```

## 內部 API 設計

### 基礎資訊

- **基礎路徑**: `/api/bike`
- **認證**: 無需額外認證（後端處理 TDX OAuth）
- **格式**: JSON

### API 端點

#### 1. 取得縣市所有租借站

```
GET /api/bike/stations
```

**參數**:

| 參數名 | 型別 | 必填 | 說明 |
|--------|------|------|------|
| city | string | 是 | 縣市代碼（Taipei, NewTaipei, Taichung 等） |

**回傳範例**:
```json
{
  "success": true,
  "data": [
    {
      "station_uid": "TPE0001",
      "station_id": "0001",
      "name": "捷運市政府站(3號出口)",
      "name_en": "MRT Taipei City Hall Stn.(Exit 3)",
      "address": "忠孝東路/松仁路(東南側)",
      "address_en": "Sec. 5, Zhongxiao E. Rd./Songren Rd.",
      "latitude": 25.040857,
      "longitude": 121.564812,
      "capacity": 60,
      "service_type": 1,
      "service_status": 1,
      "update_time": "2024-01-15T08:32:15+08:00"
    }
  ],
  "total": 400,
  "city": "Taipei"
}
```

#### 2. 取得附近租借站

```
GET /api/bike/stations/nearby
```

**參數**:

| 參數名 | 型別 | 必填 | 預設值 | 說明 |
|--------|------|------|--------|------|
| lat | float | 是 | - | 緯度（-90 ~ 90） |
| lon | float | 是 | - | 經度（-180 ~ 180） |
| radius | int | 否 | 1000 | 搜尋半徑（公尺，最大 5000） |
| limit | int | 否 | 20 | 回傳數量上限 |

**回傳範例**:
```json
{
  "success": true,
  "data": [
    {
      "station_uid": "TPE0001",
      "station_id": "0001",
      "name": "捷運市政府站(3號出口)",
      "address": "忠孝東路/松仁路(東南側)",
      "latitude": 25.040857,
      "longitude": 121.564812,
      "capacity": 60,
      "distance": 150,
      "service_type": 1,
      "service_status": 1
    }
  ],
  "center": {
    "lat": 25.040000,
    "lon": 121.565000
  },
  "radius": 1000,
  "total": 5
}
```

#### 3. 取得即時車位資訊

```
GET /api/bike/availability
```

**參數**:

| 參數名 | 型別 | 必填 | 說明 |
|--------|------|------|------|
| city | string | 是 | 縣市代碼 |
| station_uid | string | 否 | 特定站點 UID（未提供則回傳全部） |

**回傳範例**:
```json
{
  "success": true,
  "data": [
    {
      "station_uid": "TPE0001",
      "station_id": "0001",
      "available_rent_bikes": 15,
      "available_return_bikes": 45,
      "general_bikes": 10,
      "electric_bikes": 5,
      "service_status": 1,
      "update_time": "2024-01-15T08:32:15+08:00"
    }
  ],
  "city": "Taipei",
  "total": 400,
  "update_time": "2024-01-15T08:32:15+08:00"
}
```

#### 4. 搜尋站點

```
GET /api/bike/search
```

**參數**:

| 參數名 | 型別 | 必填 | 預設值 | 說明 |
|--------|------|------|--------|------|
| keyword | string | 是 | - | 搜尋關鍵字 |
| city | string | 否 | - | 指定縣市（未提供則搜尋所有縣市） |
| limit | int | 否 | 20 | 回傳數量上限 |

**回傳範例**:
```json
{
  "success": true,
  "data": [
    {
      "station_uid": "TPE0001",
      "station_id": "0001",
      "name": "捷運市政府站(3號出口)",
      "name_en": "MRT Taipei City Hall Stn.(Exit 3)",
      "address": "忠孝東路/松仁路(東南側)",
      "city": "Taipei",
      "latitude": 25.040857,
      "longitude": 121.564812,
      "capacity": 60
    }
  ],
  "keyword": "市政府",
  "total": 3
}
```

#### 5. 取得站點完整資訊（含即時車位）

```
GET /api/bike/stations/{station_uid}
```

**參數**:

| 參數名 | 型別 | 必填 | 說明 |
|--------|------|------|------|
| station_uid | string | 是 | 站點唯一識別碼（路徑參數） |
| city | string | 是 | 縣市代碼（用於快取查詢） |

**回傳範例**:
```json
{
  "success": true,
  "data": {
    "station_uid": "TPE0001",
    "station_id": "0001",
    "name": "捷運市政府站(3號出口)",
    "name_en": "MRT Taipei City Hall Stn.(Exit 3)",
    "address": "忠孝東路/松仁路(東南側)",
    "address_en": "Sec. 5, Zhongxiao E. Rd./Songren Rd.",
    "latitude": 25.040857,
    "longitude": 121.564812,
    "capacity": 60,
    "service_type": 1,
    "service_status": 1,
    "available_rent_bikes": 15,
    "available_return_bikes": 45,
    "general_bikes": 10,
    "electric_bikes": 5,
    "station_update_time": "2024-01-15T08:30:00+08:00",
    "availability_update_time": "2024-01-15T08:32:15+08:00"
  }
}
```

## Pydantic 資料模型

### 基礎模型

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import IntEnum


class ServiceType(IntEnum):
    """服務類型"""
    ORIGINAL = 0          # 原營運商系統
    YOUBIKE_1_0 = 1       # YouBike1.0
    YOUBIKE_2_0 = 2       # YouBike2.0
    TBIKE = 3             # T-Bike
    PBike = 4             # P-Bike
    KBIKE = 5             # K-Bike
    NBike = 6             # N-Bike
    TBike_2 = 7           # T-Bike2.0
    YOUBIKE_2_0_E = 8     # YouBike2.0E (電輔車)


class ServiceStatus(IntEnum):
    """服務狀態"""
    NORMAL = 0            # 正常營運
    SUSPENDED = 1         # 暫停營運
    TERMINATED = 2        # 終止營運


class BikeStation(BaseModel):
    """腳踏車租借站資訊"""
    station_uid: str = Field(description="站點唯一識別碼")
    station_id: str = Field(description="站點代碼")
    name: str = Field(description="站點中文名稱")
    name_en: Optional[str] = Field(None, description="站點英文名稱")
    address: Optional[str] = Field(None, description="中文地址")
    address_en: Optional[str] = Field(None, description="英文地址")
    latitude: float = Field(description="緯度")
    longitude: float = Field(description="經度")
    capacity: int = Field(description="總車位數")
    service_type: ServiceType = Field(description="服務類型")
    service_status: ServiceStatus = Field(description="服務狀態")
    update_time: datetime = Field(description="資料更新時間")

    class Config:
        json_schema_extra = {
            "example": {
                "station_uid": "TPE0001",
                "station_id": "0001",
                "name": "捷運市政府站(3號出口)",
                "name_en": "MRT Taipei City Hall Stn.(Exit 3)",
                "address": "忠孝東路/松仁路(東南側)",
                "address_en": "Sec. 5, Zhongxiao E. Rd./Songren Rd.",
                "latitude": 25.040857,
                "longitude": 121.564812,
                "capacity": 60,
                "service_type": 1,
                "service_status": 0,
                "update_time": "2024-01-15T08:32:15+08:00"
            }
        }


class BikeAvailability(BaseModel):
    """即時車位資訊"""
    station_uid: str = Field(description="站點唯一識別碼")
    station_id: str = Field(description="站點代碼")
    available_rent_bikes: int = Field(description="可租借車輛數")
    available_return_bikes: int = Field(description="可歸還車位數")
    general_bikes: Optional[int] = Field(None, description="一般車輛數")
    electric_bikes: Optional[int] = Field(None, description="電輔車輛數")
    service_status: ServiceStatus = Field(description="服務狀態")
    update_time: datetime = Field(description="資料更新時間")

    class Config:
        json_schema_extra = {
            "example": {
                "station_uid": "TPE0001",
                "station_id": "0001",
                "available_rent_bikes": 15,
                "available_return_bikes": 45,
                "general_bikes": 10,
                "electric_bikes": 5,
                "service_status": 0,
                "update_time": "2024-01-15T08:32:15+08:00"
            }
        }


class BikeStationWithAvailability(BaseModel):
    """站點資訊含即時車位"""
    station_uid: str = Field(description="站點唯一識別碼")
    station_id: str = Field(description="站點代碼")
    name: str = Field(description="站點中文名稱")
    name_en: Optional[str] = Field(None, description="站點英文名稱")
    address: Optional[str] = Field(None, description="中文地址")
    address_en: Optional[str] = Field(None, description="英文地址")
    latitude: float = Field(description="緯度")
    longitude: float = Field(description="經度")
    capacity: int = Field(description="總車位數")
    service_type: ServiceType = Field(description="服務類型")
    service_status: ServiceStatus = Field(description="服務狀態")
    available_rent_bikes: int = Field(description="可租借車輛數")
    available_return_bikes: int = Field(description="可歸還車位數")
    general_bikes: Optional[int] = Field(None, description="一般車輛數")
    electric_bikes: Optional[int] = Field(None, description="電輔車輛數")
    station_update_time: datetime = Field(description="站點資料更新時間")
    availability_update_time: datetime = Field(description="車位資料更新時間")


class NearbyStation(BikeStation):
    """附近站點（含距離）"""
    distance: float = Field(description="與中心點距離（公尺）")


class BikeStationsResponse(BaseModel):
    """站點列表回應"""
    success: bool = Field(default=True)
    data: List[BikeStation]
    total: int = Field(description="總數量")
    city: str = Field(description="縣市代碼")


class NearbyStationsResponse(BaseModel):
    """附近站點回應"""
    success: bool = Field(default=True)
    data: List[NearbyStation]
    center: dict = Field(description="中心座標")
    radius: int = Field(description="搜尋半徑（公尺）")
    total: int = Field(description="總數量")


class BikeAvailabilityResponse(BaseModel):
    """車位資訊回應"""
    success: bool = Field(default=True)
    data: List[BikeAvailability]
    city: str = Field(description="縣市代碼")
    total: int = Field(description="總數量")
    update_time: datetime = Field(description="資料更新時間")


class BikeStationDetailResponse(BaseModel):
    """站點詳細資訊回應"""
    success: bool = Field(default=True)
    data: BikeStationWithAvailability


class BikeSearchResponse(BaseModel):
    """搜尋結果回應"""
    success: bool = Field(default=True)
    data: List[BikeStation]
    keyword: str = Field(description="搜尋關鍵字")
    total: int = Field(description="總數量")
```

## 快取策略

### 快取時間設定

```python
# 快取設定（秒）
CACHE_TTL_STATIONS = 3600           # 站點資料快取 1 小時（站點資訊變動少）
CACHE_TTL_AVAILABILITY = 60         # 車位資訊快取 60 秒（需即時性）
CACHE_TTL_NEARBY_SEARCH = 60        # 附近搜尋結果快取 60 秒
CACHE_TTL_SEARCH_RESULTS = 300      # 關鍵字搜尋結果快取 5 分鐘
```

### 快取策略說明

| 資料類型 | 快取時間 | 說明 |
|---------|---------|------|
| 站點基本資訊 | 1 小時 | 站點名稱、位置、容量等資訊變動頻率低 |
| 即時車位資訊 | 60 秒 | 需要即時性，避免過度請求 TDX API |
| 附近站點搜尋 | 60 秒 | 基於位置，短時間內結果相同 |
| 關鍵字搜尋 | 5 分鐘 | 搜尋結果變動少，可適度快取 |
| TDX Access Token | 依回應 | TDX 回傳的 expires_in，通常 1 小時 |

### 記憶體快取實作

採用與現有服務相同的記憶體快取模式：

```python
class BikeTDXService:
    def __init__(self, auth: Optional[TDXAuth] = None):
        self.auth = auth or get_tdx_auth()
        self.base_url = TDX_API_BASE_URL
        # 記憶體快取：{cache_key: (timestamp, data)}
        self._cache: Dict[str, Tuple[float, Any]] = {}
        # 站點位置索引（用於附近搜尋）
        self._station_positions: Dict[str, Dict[str, float]] = {}
        self._positions_last_update: Optional[datetime] = None

    def _get_cached(self, key: str, ttl: int) -> Optional[Any]:
        """取得快取資料，若過期則回傳 None"""
        if key not in self._cache:
            return None
        timestamp, data = self._cache[key]
        if time.time() - timestamp > ttl:
            del self._cache[key]
            return None
        return data

    def _set_cached(self, key: str, data: Any) -> None:
        """設定快取資料"""
        self._cache[key] = (time.time(), data)
```

### 地理位置快取

為了加速附近站點搜尋，建立站點位置索引：

```python
class StationPositionCache:
    """站點位置快取管理器"""

    def __init__(self, bike_service: 'BikeTDXService'):
        self.bike_service = bike_service
        self._positions: Dict[str, Dict[str, Any]] = {}
        self._last_update: Optional[datetime] = None
        self._update_interval = 3600  # 1 小時
        self._lock = asyncio.Lock()

    async def get_positions_for_city(self, city: str) -> Dict[str, Dict[str, float]]:
        """取得指定縣市的所有站點位置"""
        if self._needs_update():
            await self._refresh_cache()
        return {
            uid: pos for uid, pos in self._positions.items()
            if uid.startswith(city.upper()[:3])
        }

    def _calculate_distance(self, lat1: float, lon1: float,
                           lat2: float, lon2: float) -> float:
        """計算兩點間距離（公尺），使用 Haversine 公式"""
        from math import radians, sin, cos, sqrt, atan2

        R = 6371000  # 地球半徑（公尺）
        phi1, phi2 = radians(lat1), radians(lat2)
        dphi = radians(lat2 - lat1)
        dlambda = radians(lon2 - lon1)

        a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
        return 2 * R * atan2(sqrt(a), sqrt(1 - a))
```

## TDX API 對應關係

### 欄位對照表

#### Station 欄位對照

| TDX 欄位 | 內部欄位 | 說明 |
|---------|---------|------|
| StationUID | station_uid | 唯一識別碼 |
| StationID | station_id | 站點代碼 |
| StationName.Zh_tw | name | 中文名稱 |
| StationName.En | name_en | 英文名稱 |
| StationPosition.PositionLat | latitude | 緯度 |
| StationPosition.PositionLon | longitude | 經度 |
| StationAddress.Zh_tw | address | 中文地址 |
| StationAddress.En | address_en | 英文地址 |
| BikesCapacity | capacity | 總車位數 |
| ServiceType | service_type | 服務類型 |
| ServiceStatus | service_status | 服務狀態 |
| UpdateTime | update_time | 更新時間 |

#### Availability 欄位對照

| TDX 欄位 | 內部欄位 | 說明 |
|---------|---------|------|
| StationUID | station_uid | 唯一識別碼 |
| StationID | station_id | 站點代碼 |
| AvailableRentBikes | available_rent_bikes | 可租借車數 |
| AvailableReturnBikes | available_return_bikes | 可歸還車位 |
| AvailableRentBikesDetail.GeneralBikes | general_bikes | 一般車數 |
| AvailableRentBikesDetail.ElectricBikes | electric_bikes | 電輔車數 |
| ServiceStatus | service_status | 服務狀態 |
| UpdateTime | update_time | 更新時間 |

## 實作檔案結構

```
backend/
├── bike_tdx_service.py      # Bike TDX API 服務
├── main.py                  # 主要 API 端點整合
└── API_DESIGN.md           # 本文件
```

## 錯誤處理

### HTTP 狀態碼

| 狀態碼 | 說明 | 使用情境 |
|--------|------|----------|
| 200 | 成功 | 正常回應 |
| 400 | 錯誤請求 | 缺少必填參數或格式錯誤 |
| 404 | 找不到 | 站點不存在 |
| 429 | 請求過多 | TDX API 速率限制 |
| 500 | 伺服器錯誤 | 內部處理錯誤 |

### 錯誤回應格式

```json
{
  "success": false,
  "error": {
    "code": "INVALID_CITY",
    "message": "不支援的縣市代碼: FooBar"
  }
}
```

## 速率限制

- **TDX API**: 依據 TDX 平台限制（目前無明確文件，建議每秒不超過 10 請求）
- **內部 API**: 無特別限制，由後端快取保護

## 後續擴充建議

1. **多縣市支援**: 目前列出 11 個支援 YouBike 的縣市
2. **歷史資料**: 可擴充儲存車位歷史趨勢
3. **預測功能**: 基於歷史資料預測尖峰時段車位狀況
4. **地圖整合**: 提供地圖圖資或 GeoJSON 格式
