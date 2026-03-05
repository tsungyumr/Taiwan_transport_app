# 台灣交通時刻表App - 公車API說明文件

## API端點總覽

### 公車路線相關
- `GET /api/bus/routes` - 取得公車路線列表
- `GET /api/bus/{route_id}` - 取得特定路線詳細資料
- `GET /api/bus/search` - 搜尋公車路線
- `GET /api/bus/operators` - 取得公車業者列表

### 健康檢查
- `GET /api/bus/health` - 公車服務健康檢查

## API詳細說明

### 1. 取得公車路線列表

**端點**: `GET /api/bus/routes`

**功能**: 取得所有公車路線或搜尋特定路線

**參數**:
- `route_name` (optional): 路線名稱關鍵字，用於搜尋特定路線
- `limit` (optional): 回傳數量限制，預設50筆

**回應格式**:
```json
[
  {
    "route_id": "235",
    "route_name": "235",
    "departure_stop": "長春路",
    "arrival_stop": "福港街",
    "operator": "首都客運",
    "direction": 0,
    "stops": ["長春路", "民生社區", "富民生態", "新東街", "吉祥路", "成福路", "福港街"]
  }
]
```

**狀態碼**:
- `200`: 成功
- `503`: 服務暫時無法使用

### 2. 取得特定路線詳細資料

**端點**: `GET /api/bus/{route_id}`

**功能**: 取得特定公車路線的詳細資料，包含車輛位置和站牌資訊

**參數**:
- `route_id`: 路線ID（路線編號）

**回應格式**:
```json
{
  "route": "235",
  "stops": [
    {
      "name": "長春路",
      "sequence": 1,
      "latitude": 25.0516,
      "longitude": 121.5386
    },
    {
      "name": "民生社區",
      "sequence": 2,
      "latitude": 25.0520,
      "longitude": 121.5390
    }
  ],
  "buses": [
    {
      "id": "235-001",
      "plate_number": "XX-1234",
      "at_stop": 1,
      "eta_next": "2分鐘後到站",
      "heading_to": 2,
      "latitude": 25.0518,
      "longitude": 121.5388,
      "speed": 15.5,
      "direction": 0
    }
  ],
  "updated": "2026-03-02T10:30:00",
  "operator": "首都客運",
  "direction": 0,
  "total_stops": 7
}
```

**狀態碼**:
- `200`: 成功
- `503`: 服務暫時無法使用

### 3. 搜尋公車路線

**端點**: `GET /api/bus/search`

**功能**: 使用關鍵字搜尋公車路線

**參數**:
- `query`: 搜尋關鍵字

**回應格式**:
```json
[
  {
    "route_id": "235",
    "route_name": "235",
    "departure_stop": "長春路",
    "arrival_stop": "福港街",
    "operator": "首都客運"
  }
]
```

**狀態碼**:
- `200`: 成功
- `503`: 服務暫時無法使用

### 4. 取得公車業者列表

**端點**: `GET /api/bus/operators`

**功能**: 取得所有已知的公車業者列表

**回應格式**:
```json
[
  "首都客運",
  "三重客運",
  "台北客運",
  "指南客運",
  "桃園客運",
  "新竹客運",
  "台中客運",
  "高雄客運",
  "屏東客運",
  "台鐵局",
  "高鐵局"
]
```

**狀態碼**:
- `200`: 成功
- `503`: 服務暫時無法使用

### 5. 公車服務健康檢查

**端點**: `GET /api/bus/health`

**功能**: 檢查公車服務的可用性

**回應格式**:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-02T10:30:00",
  "version": "1.0.0",
  "features": {
    "bus_routes": true,
    "bus_route_data": true,
    "search": true
  }
}
```

**狀態碼**:
- `200`: 服務健康
- `503`: 服務不健康

## 快取策略

### 快取時間設定
- **路線列表**: 1天 (86400秒)
- **路線詳細資料**: 5分鐘 (300秒)
- **站牌資訊**: 1週 (604800秒)
- **搜尋結果**: 1天 (86400秒)

### 快取失效
- 自動清除過期快取
- 手動清除：呼叫快取清除函數

## 錯誤處理

### 常見錯誤碼
- `503 Service Unavailable`: 爬蟲服務暫時無法使用
- `422 Unprocessable Entity`: 參數驗證錯誤
- `500 Internal Server Error`: 系統內部錯誤

### 錯誤回應格式
```json
{
  "detail": "無法取得公車路線資料",
  "error_code": "SCRAPER_ERROR",
  "timestamp": "2026-03-02T10:30:00"
}
```

## 使用範例

### 使用curl
```bash
# 取得所有路線
curl -X GET "http://localhost:8000/api/bus/routes"

# 搜尋特定路線
curl -X GET "http://localhost:8000/api/bus/routes?route_name=235"

# 取得路線詳細資料
curl -X GET "http://localhost:8000/api/bus/235"

# 搜尋路線
curl -X GET "http://localhost:8000/api/bus/search?query=藍"

# 取得業者列表
curl -X GET "http://localhost:8000/api/bus/operators"

# 健康檢查
curl -X GET "http://localhost:8000/api/bus/health"
```

### 使用Python
```python
import httpx

async def get_bus_routes():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/api/bus/routes")
        return response.json()

async def get_bus_route_data(route_id):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://localhost:8000/api/bus/{route_id}")
        return response.json()
```

## 部署注意事項

### 環境需求
- Python 3.13+
- Playwright (自動安裝)
- 網路連線（連接ebus.gov.taipei）

### 安裝和啟動
```bash
# 安裝依賴
pip install -r requirements.txt

# 安裝Playwright瀏覽器
playwright install

# 啟動服務
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 生產配置
- 建議使用反向代理（如Nginx）
- 設定適當的速率限制
- 啟用HTTPS
- 監控服務健康狀態

## 常見問題

### Q: 為什麼API回傳503錯誤？
**A**: 可能是爬蟲服務暫時無法使用，請稍後重試。也可能是目標網站無法存取。

### Q: 資料更新頻率是多久？
**A**:
- 路線列表：每天更新一次
- 車輛位置：每5分鐘更新一次
- 站牌資訊：每週更新一次

### Q: 如何處理資料不完整？
**A**: API會回傳盡可能完整的資料，缺少的欄位會設為null或預設值。

### Q: 支援哪些瀏覽器？
**A**: API使用Playwright在後端處理，前端不需特定瀏覽器支援。