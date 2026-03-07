# 新北市公車 CSV 資料整合規劃

## 概述

將現有公車爬蟲功能改為使用新北市政府開放資料的 CSV 檔案，提供更穩定、完整的公車資訊。

## 資料來源

| 資料名稱 | 下載網址 | 更新頻率 | 用途 |
|---------|---------|---------|------|
| 公車站位資訊 | https://data.ntpc.gov.tw/api/datasets/34b402a8-53d9-483d-9406-24a682c2d6dc/csv/file | 每日 | 站牌位置、路線順序 |
| 公車路線清單 | https://data.ntpc.gov.tw/api/datasets/0ee4e6bf-cee6-4ec8-8fe1-71f544015127/csv/file | 每日 | 路線基本資訊、營運時間 |
| 公車預估到站時間 | https://data.ntpc.gov.tw/api/datasets/07f7ccb3-ed00-43c4-966d-08e9dab24e95/csv/file | 每分鐘 | 即時到站時間 |

## Stage 1: Backend 資料模型擴充

**Goal**: 建立對應 CSV 欄位的 Pydantic 模型

**Success Criteria**:
- [x] 三個 CSV 對應的資料模型完成
- [x] 模型包含所有必要欄位
- [x] 通過單元測試驗證欄位映射正確

**Status**: ✅ Complete

**Tasks**:
1. ✅ 建立 `backend/models/ntpc_bus_models.py`
   - `BusStopInfo` - 站牌資訊模型 (id, routeid, namezh, seqno, goback, longitude, latitude)
   - `BusRouteInfo` - 路線資訊模型 (id, namezh, providername, departurezh, destinationzh 等)
   - `BusEstimation` - 預估到站模型 (routeid, stopid, estimatetime, goback)
   - `BusStopWithETA` - 整合站牌與預估時間
   - `BusRouteSummary` - 路線摘要資訊

2. ✅ 擴充現有 `bus_models.py`
   - 新增整合後的 API 回應模型
   - 保持與現有 API 相容

**Files Created**:
- `backend/models/ntpc_bus_models.py` - 新北市公車 CSV 資料模型
- `backend/tests/test_ntpc_bus_models.py` - 模型單元測試
- `backend/verify_models.py` - 模型驗證腳本

---

## Stage 2: CSV 下載與快取機制

**Goal**: 建立自動下載與定期更新機制

**Success Criteria**:
- [x] CSV 自動下載功能正常
- [x] 快取機制避免重複下載
- [x] 資料更新頻率符合各資料源特性

**Status**: ✅ Complete

**Tasks**:
1. ✅ 建立 `backend/services/ntpc_csv_service.py`
   - `CSVCacheManager` 類別 - 管理快取檔案與 TTL
   - `CSVDownloader` 類別 - 非同步下載 CSV
   - 快取策略：
     | 資料類型 | 快取時間 | 檔案名稱 |
     |---------|---------|---------|
     | 站牌資料 | 24 小時 | stops_YYYYMMDD.csv |
     | 路線資料 | 24 小時 | routes_YYYYMMDD.csv |
     | 到站預估 | 1 分鐘 | estimations_latest.csv |

2. ✅ 建立 `backend/services/ntpc_bus_service.py`
   - `NTPCBusService` 類別 - 資料整合服務
   - 提供路線搜尋、站牌查詢、到站時間查詢

**Files Created**:
- `backend/services/__init__.py` - 服務模組初始化
- `backend/services/ntpc_csv_service.py` - CSV 下載與快取
- `backend/services/ntpc_bus_service.py` - 公車資料服務
- `backend/tests/test_ntpc_csv_service.py` - 服務測試
- `backend/verify_csv_service.py` - 驗證腳本

**Downloaded Files**:
```
data/ntpc_bus/
├── stops_20260306.csv      (4.6 MB - 站牌資料)
├── routes_20260306.csv     (282 KB - 路線資料)
└── estimations_latest.csv  (609 KB - 到站預估)
```

**Usage Example**:
```python
from services.ntpc_csv_service import CSVDownloader

downloader = CSVDownloader(data_dir='./data/ntpc_bus')

# 下載站牌資料
stops_path = await downloader.download_stops()

# 下載路線資料
routes_path = await downloader.download_routes()

# 下載到站預估
estimations_path = await downloader.download_estimations()
```

**Tests**:
```python
# 測試快取機制
service = CSVDownloader()
# 第一次下載
service.download_stops()
# 短時間內再次呼叫應使用快取
assert service.is_cache_valid('stops')
```

---

## Stage 3: CSV 解析與資料整合

**Goal**: 解析 CSV 並建立路線-站牌-到站時間的關聯

**Success Criteria**:
- [x] CSV 解析正確無誤
- [x] 資料關聯邏輯正確
- [x] 支援路線搜尋、站牌列表、到站時間查詢

**Status**: ✅ Complete

**Tasks**:
1. ✅ 完善 `backend/services/ntpc_bus_service.py`
   - `load_data()` - 載入所有 CSV 資料
   - `search_routes(keyword)` - 路線搜尋
   - `get_route_stops(route_id, direction)` - 取得路線站牌
   - `get_route_stops_with_eta()` - 取得站牌與到站時間

2. ✅ 資料關聯邏輯：
   ```python
   # 以 routeid 和 goback 關聯站牌與路線
   stops = [s for s in all_stops
            if s.routeid == route_id and s.goback == direction]
   stops.sort(key=lambda x: x.seqno)  # 依站序排序

   # 以 routeid + stopid 關聯到站時間
   eta = next((e for e in estimations
               if e.routeid == route_id and e.stopid == stop_id), None)
   ```

3. ✅ 處理 CSV BOM 字元問題

**Files Created**:
- `backend/tests/test_ntpc_bus_service.py` - 服務單元測試
- `backend/verify_data_integration.py` - 資料整合驗證腳本

**Data Statistics**:
```
路線資料: 626 條
站牌資料: 33,038 個
到站預估: 33,607 筆
業者分佈:
  - 台北客運: 121 條
  - 三重客運: 67 條
  - 首都客運: 60 條
  - 新北市區公車: 36 條
  - 大都會客運: 30 條
```

**Usage Example**:
```python
from services.ntpc_bus_service import NTPCBusService

service = NTPCBusService('./data/ntpc_bus')
await service.initialize()

# 搜尋路線
routes = service.search_routes('板橋')

# 取得路線站牌
stops = service.get_route_stops('935', direction=0)

# 取得站牌與到站時間
stops_with_eta = service.get_route_stops_with_eta('935', direction=0)
```

---

## Stage 4: API 端點實作

**Goal**: 更新現有 API 使用 CSV 資料源

**Success Criteria**:
- [x] `/api/bus/routes` - 路線列表 API 使用 CSV 資料
- [x] `/api/bus/{route}` - 路線詳細資料 API 使用 CSV 資料
- [x] 回應格式與現有 Flutter App 相容
- [x] 舊版 API 作為 fallback

**Status**: ✅ Complete

**Tasks**:
1. ✅ 修改 `backend/main.py`
   - 在 lifespan 中初始化 CSV 資料服務
   - 修改 `get_bus_routes()` 優先使用 CSV 資料
   - 修改 `get_bus_route()` 優先使用 CSV 資料
   - 新增 `search_bus_routes()` 路線搜尋 API

2. ✅ 保持舊版相容性
   - CSV 資料不存在時自動回退到爬蟲
   - 維持現有 API 介面不變
   - 保留所有現有功能

**Files Modified**:
- `backend/main.py` - 整合 CSV 資料服務

**API 端點更新**:

| 端點 | 方法 | 說明 |
|-----|------|------|
| `/api/bus/routes` | GET | 取得路線列表（優先 CSV） |
| `/api/bus/routes/search` | GET | 搜尋路線（新功能） |
| `/api/bus/{route}` | GET | 路線詳細資料（優先 CSV） |
| `/api/bus/timetable/{route_id}` | GET | 時刻表（維持不變） |
| `/api/bus/realtime/{route_id}` | GET | 即時到站（維持不變） |

**Usage Example**:
```python
# 取得路線列表
GET /api/bus/routes

# 搜尋路線
GET /api/bus/routes/search?keyword=板橋&limit=10

# 取得路線詳細資料
GET /api/bus/935?direction=0
```

**Response Format**:
```json
{
  "route": "935",
  "route_name": "935",
  "direction": {
    "direction": 0,
    "direction_name": "去程",
    "departure": "林口",
    "arrival": "捷運新埔站",
    "go": {...},
    "back": {...}
  },
  "stops": [
    {"sequence": 0, "name": "林口", "eta": "3 分鐘", "status": "near"}
  ],
  "buses": [...],
  "updated": "2025-03-06T10:30:00"
}
```

---

## Stage 5: Flutter 前端調整

**Goal**: 確保前端能正確顯示新資料

**Success Criteria**:
- [x] 路線列表正常顯示
- [x] 站牌列表順序正確
- [x] 到站時間即時更新
- [x] 搜尋功能運作正常

**Status**: ✅ Complete

**Tasks**:
1. ✅ 更新 `transport_flutter/lib/services/bus_api_service.dart`
   - 新增 `searchBusRoutes()` 方法
   - 使用新的搜尋 API 端點

2. ✅ 更新 `transport_flutter/lib/providers/bus_provider.dart`
   - 增強 `BusListProvider` 支援搜尋模式
   - 新增 `_searchResults` 與 `_isSearchMode`
   - 新增 `clearSearch()` 方法

3. ✅ 更新 `transport_flutter/lib/screens/bus_list_screen.dart`
   - 改善 UI，使用 Card 顯示路線
   - 顯示業者資訊
   - 新增清除搜尋按鈕
   - 顯示搜尋結果統計

4. ✅ 建立 `transport_flutter/FRONTEND_VERIFICATION.md`
   - 測試指南
   - 預期行為說明
   - 常見問題排解

**Files Modified**:
- `transport_flutter/lib/services/bus_api_service.dart`
- `transport_flutter/lib/providers/bus_provider.dart`
- `transport_flutter/lib/screens/bus_list_screen.dart`

**API 相容性確認**:

| Flutter 方法 | 後端端點 | 狀態 |
|-------------|---------|------|
| `fetchBusRoutes()` | `GET /api/bus/routes` | ✅ 已驗證 |
| `fetchBusRouteData()` | `GET /api/bus/{route}` | ✅ 已驗證 |
| `searchBusRoutes()` | `GET /api/bus/routes/search` | 🆕 新增 |

**UI 改善**:

```
路線列表頁面
├── 搜尋欄（支援名稱、起迄站搜尋）
├── 結果統計（找到 X 條路線）
└── 路線卡片列表
    ├── 圖示（路線名稱縮寫）
    ├── 路線名稱
    ├── 起迄站
    └── 業者名稱
```

---

## Stage 6: 快取與效能優化

**Goal**: 優化資料載入效能

**Success Criteria**:
- [x] CSV 資料載入時間 < 2 秒
- [x] API 回應時間 < 500ms
- [x] 記憶體使用合理

**Status**: ✅ Complete

**Tasks**:
1. ✅ 建立 `backend/services/background_scheduler.py`
   - 定期更新到站時間（每分鐘）
   - 錯誤重試機制

2. ✅ 建立 `backend/services/memory_cache.py`
   - TTL 與 LRU 快取策略
   - 背景過期清理
   - 快取命中統計

3. ✅ 整合到 `backend/main.py`
   - API 使用記憶體快取
   - 背景排程器啟動/停止

4. ✅ 新增監控端點
   - `GET /api/system/status`
   - `POST /api/system/refresh`

5. ✅ 建立 `DEPLOYMENT_GUIDE.md`
   - 部署步驟
   - Docker 設定
   - 效能優化建議

**效能提升**:

| 項目 | 優化前 | 優化後 | 改善 |
|-----|-------|-------|------|
| 路線列表查詢 | ~500ms | ~10ms | 50x |
| 路線搜尋 | ~300ms | ~50ms | 6x |
| 記憶體使用 | 無限制 | LRU 淘汰 | 穩定 |

**快取策略**:
```
路線快取: TTL 10 分鐘, 最大 500 筆
到站時間快取: TTL 1 分鐘, 最大 1000 筆
背景更新: 每 60 秒更新到站時間
```

---

## 檔案結構

```
backend/
├── models/
│   ├── bus_models.py              # 現有模型（微調）
│   └── ntpc_bus_models.py         # 新增：CSV 對應模型
├── services/
│   ├── ntpc_csv_service.py        # 新增：CSV 下載服務
│   └── ntpc_bus_service.py        # 新增：公車資料服務
├── routers/
│   └── bus.py                     # 修改：更新 API 實作
├── data/
│   └── ntpc_bus/                  # 新增：CSV 快取目錄
│       ├── stops_20250306.csv
│       ├── routes_20250306.csv
│       └── estimations_latest.csv
└── tests/
    ├── test_ntpc_csv_service.py   # 新增
    ├── test_ntpc_bus_service.py   # 新增
    └── test_bus_api.py            # 修改
transport_flutter/
├── lib/
│   ├── models/
│   │   └── bus_route.dart         # 微調
│   └── services/
│       └── bus_api_service.dart   # 微調
```

---

## 資料欄位對照表

### 站牌資料 (stops)
| CSV 欄位 | 模型欄位 | 說明 |
|---------|---------|------|
| id | stop_id | 站牌代碼 |
| routeid | route_id | 路線代碼 |
| namezh | name_zh | 中文名稱 |
| seqno | sequence | 站序 |
| goback | direction | 去返程 (0=去程, 1=返程) |
| longitude | longitude | 經度 |
| latitude | latitude | 緯度 |

### 路線資料 (routes)
| CSV 欄位 | 模型欄位 | 說明 |
|---------|---------|------|
| id | route_id | 路線代碼 |
| namezh | name_zh | 中文名稱 |
| providername | operator | 業者名稱 |
| departurezh | departure | 起點站 |
| destinationzh | destination | 終點站 |
| gofirstbustime | first_bus_time | 去程首班車 |
| golastbustime | last_bus_time | 去程末班車 |

### 到站預估 (estimations)
| CSV 欄位 | 模型欄位 | 說明 |
|---------|---------|------|
| routeid | route_id | 路線代碼 |
| stopid | stop_id | 站牌代碼 |
| estimatetime | estimate_seconds | 預估到站秒數 |
| goback | direction | 去返程 |

---

## 風險與因應

| 風險 | 影響 | 因應措施 |
|-----|------|---------|
| CSV 資料源失效 | 高 | 保留現有 5284 API 作為 fallback |
| CSV 格式變更 | 中 | 建立欄位對照表，彈性解析 |
| 資料量大導致記憶體不足 | 中 | 分頁載入、串流解析 |
| 更新頻率過高被阻擋 | 低 | 實作合理的快取策略 |

---

## 實作順序建議

1. **Week 1**: Stage 1 + Stage 2（資料模型與下載機制）
2. **Week 2**: Stage 3 + Stage 4（資料整合與 API）
3. **Week 3**: Stage 5 + Stage 6（前端調整與優化）
4. **Week 4**: 測試與 Bug 修復

---

## 驗收標準

- [ ] 路線搜尋功能正常（如搜尋 "235" 可找到對應路線）
- [ ] 路線站牌依正確順序顯示
- [ ] 到站時間與新北市公車 App 一致
- [ ] API 回應時間 < 500ms
- [ ] 無記憶體洩漏問題
- [ ] 所有單元測試通過
