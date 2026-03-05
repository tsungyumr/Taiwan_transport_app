# 台灣交通時刻表App - 公車API模組

## 簡介

這個模組提供台北市公車eBus的爬蟲功能，用於取得真實的公車路線、車輛位置和到站時間資料。整合到台灣交通時刻表App的FastAPI後端，替換原本的mock data。

## 功能特性

### ✅ 支援的功能
- **公車路線列表**: 取得所有公車路線或搜尋特定路線
- **路線詳細資料**: 取得特定路線的車輛位置、站牌資訊、業者資料
- **即時車輛追蹤**: 顯示公車的即時位置和到站時間預測
- **路線搜尋**: 使用關鍵字搜尋公車路線
- **業者資訊**: 取得公車業者列表
- **健康檢查**: 檢查API服務的可用性

### ✅ 技術特色
- **Playwright爬蟲**: 使用Playwright進行網頁爬蟲，支援JavaScript渲染
- **快取機制**: 內建快取系統，提升效能並減少對目標網站的負擔
- **錯誤處理**: 完善的錯誤處理和重試機制
- **防爬蟲策略**: 實作多種防爬蟲措施
- **非同步處理**: 使用async/await模式提升效能

## 安裝說明

### 1. 安裝Python依賴
```bash
pip install -r requirements.txt
```

### 2. 安裝Playwright瀏覽器
```bash
playwright install
```

### 3. 設定環境變數（可選）
```bash
# 設定快取目錄
export BUS_SCRAPER_CACHE_DIR="/path/to/cache"

# 設定快取時間（秒）
export BUS_SCRAPER_CACHE_TTL_ROUTES=86400
export BUS_SCRAPER_CACHE_TTL_VEHICLES=300
export BUS_SCRAPER_CACHE_TTL_STOPS=604800

# 設定Playwright headless模式
export BUS_SCRAPER_HEADLESS=True
```

## 使用方式

### 1. 作為API使用
```bash
# 啟動API服務
uvicorn main:app --host 0.0.0.0 --port 8000

# 測試API
curl http://localhost:8000/api/bus/routes
```

### 2. 作為爬蟲模組使用
```python
from scrapers.taipei_bus_scraper import TaipeiBusScraper

async def main():
    # 建立爬蟲實例
    async with TaipeiBusScraper(headless=True) as scraper:

        # 取得所有公車路線
        routes = await scraper.get_bus_routes(limit=10)
        print(f"Found {len(routes)} routes")

        # 搜尋特定路線
        search_results = await scraper.search_routes("藍")
        print(f"Found {len(search_results)} search results")

        # 取得特定路線詳細資料
        if routes:
            route_data = await scraper.get_bus_route_data(routes[0].route_id)
            print(f"Route: {route_data.route}")
            print(f"Stops: {len(route_data.stops)}")
            print(f"Vehicles: {len(route_data.buses)}")

import asyncio
asyncio.run(main())
```

## API端點說明

### 公車路線相關
- `GET /api/bus/routes` - 取得公車路線列表
- `GET /api/bus/{route_id}` - 取得特定路線詳細資料
- `GET /api/bus/search` - 搜尋公車路線
- `GET /api/bus/operators` - 取得公車業者列表

### 健康檢查
- `GET /api/bus/health` - 公車服務健康檢查

## 配置選項

### 快取配置
```python
scraper = TaipeiBusScraper(
    headless=True,
    cache_ttl_routes=86400,  # 1 day
    cache_ttl_vehicles=300,   # 5 minutes
    cache_ttl_stops=604800    # 1 week
)
```

### Playwright配置
```python
scraper = TaipeiBusScraper(
    headless=True,
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    viewport_width=1920,
    viewport_height=1080,
    locale="zh-TW",
    timezone="Asia/Taipei"
)
```

## 錯誤處理

### 常見錯誤碼
- `200`: 成功
- `503`: 服務暫時無法使用
- `422`: 參數驗證錯誤
- `500`: 系統內部錯誤

### 錯誤回應格式
```json
{
  "detail": "無法取得公車路線資料",
  "error_code": "SCRAPER_ERROR",
  "timestamp": "2026-03-02T10:30:00"
}
```

## 測試

### 執行單元測試
```bash
python -m pytest tests/test_bus_api.py -v
```

### 測試覆蓋率
```bash
python -m pytest tests/test_bus_api.py -v --cov=scrapers --cov=api --cov-report=html
```

## 貢獻指南

### 1. 提交問題
- 描述清楚問題
- 包含重現步驟
- 提供錯誤訊息

### 2. 提交PR
- 確保所有測試通過
- 更新相關文件
- 遵循程式碼風格

### 3. 開發流程
1. Fork專案
2. 建立分支
3. 實作功能
4. 新增測試
5. 提交PR

## 授權

本專案使用MIT授權條款。詳細內容請參閱LICENSE檔案。

## 聯絡資訊

- **作者**: Claude Code
- **Email**: noreply@anthropic.com
- **專案位置**: D:\source\Taiwan_transport_app\backend

## 參考資源

- [Playwright官方文件](https://playwright.dev/python/)
- [FastAPI官方文件](https://fastapi.tiangolo.com/)
- [eBus政府網站](https://ebus.gov.taipei/ebus)