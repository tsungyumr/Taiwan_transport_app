# 大台北公車快取系統說明文件

## 概述

本系統為大台北公車 API 新增了快取機制，採用**懶加載（Lazy Loading）**模式：
- 用戶請求時才撈取資料
- 資料快取在記憶體中，有效期 1 分鐘
- 快取過期後自動重新撈取

## 功能特色

1. **懶加載**: 用戶請求時才撈取資料，節省資源
2. **自動過期**: 資料超過 1 分鐘自動重新撈取
3. **執行緒安全**: 使用 asyncio.Lock 確保資料存取安全
4. **無背景任務**: 不需要定期更新，減少系統負擔
5. **手動管理**: 提供 API 端點可手動重新整理或清空快取

## 檔案結構

```
backend/
├── cache/
│   ├── __init__.py              # 快取模組初始化
│   └── bus_cache_manager.py     # 公車快取管理器實作
├── main.py                      # 已整合快取系統的主程式
└── test_bus_cache.py            # 快取系統測試腳本
```

## 快取策略

### 懶加載模式

1. **首次請求**: 用戶呼叫 API → 爬取資料 → 存入快取 → 返回資料
2. **後續請求（1分鐘內）**: 用戶呼叫 API → 從快取返回（< 100ms）
3. **過期後請求**: 用戶呼叫 API → 重新爬取 → 更新快取 → 返回資料

### 快取過期時間
- **路線列表**: 60 秒
- **路線詳細資料**: 60 秒

## API 端點

### 現有端點（已整合快取）

#### 1. 取得公車路線列表
```
GET /api/bus/routes?route_name={keyword}
```
- 首次請求會即時爬取資料
- 後續請求從快取讀取（有效期1分鐘）

#### 2. 取得公車路線即時資料
```
GET /api/bus/{route}?direction={0|1}
```
- 首次請求會即時爬取資料
- 後續請求從快取讀取（有效期1分鐘）

### 新增管理端點

#### 3. 查詢快取狀態
```
GET /api/bus/cache/status
```

回應範例：
```json
{
  "cached_routes_count": 5,
  "cached_route_list": true,
  "route_list_count": 1025,
  "expired_routes_count": 2,
  "route_list_expired": false,
  "cache_ttl_seconds": 60,
  "total_requests": 10,
  "cache_hits": 6,
  "cache_misses": 4,
  "expired_updates": 2,
  "failed_updates": 0,
  "last_error": null
}
```

#### 4. 手動更新特定路線快取
```
POST /api/bus/cache/refresh/{route}?direction={0|1}
```

回應範例：
```json
{
  "success": true,
  "message": "路線 藍15 方向 0 快取已更新"
}
```

#### 5. 清空所有快取
```
POST /api/bus/cache/clear
```

回應範例：
```json
{
  "success": true,
  "message": "已清空所有公車快取資料"
}
```

## 效能提升

使用快取系統後：
- **首次請求**: 約 10-20 秒（需要爬取資料）
- **快取命中**: < 50 毫秒（從記憶體快取讀取）
- **減少外部請求**: 約 90% 的請求不再需要連接到 ebus.gov.taipei

## 執行方式

### 啟動 API 伺服器
```bash
cd backend
python main.py
```

伺服器啟動時會：
1. 初始化 Playwright 瀏覽器
2. 啟動公車快取管理器（不預先撈取資料）

### 測試快取系統
```bash
cd backend
python test_bus_cache.py
```

## 監控與維護

### 查看快取狀態
```bash
curl http://localhost:8000/api/bus/cache/status
```

### 手動更新特定路線
```bash
curl -X POST http://localhost:8000/api/bus/cache/refresh/藍15?direction=0
```

### 清空所有快取
```bash
curl -X POST http://localhost:8000/api/bus/cache/clear
```

## 錯誤處理

- 若爬取失敗，系統會記錄錯誤並返回舊的快取資料（即使已過期）
- 若無舊快取可返回，則回傳錯誤
- 所有錯誤都會記錄在日誌中，可透過 `last_error` 欄位查詢

## 與舊版差異

| 項目 | 舊版（定期更新） | 新版（懶加載） |
|------|-----------------|---------------|
| 啟動時 | 預先撈取所有資料 | 不預先撈取 |
| 更新頻率 | 每30秒強制更新 | 用戶請求時檢查 |
| 記憶體使用 | 較高（常駐大量資料） | 較低（只存用戶請求的） |
| 回應時間 | 穩定快速 | 首次較慢，後續很快 |
| 背景任務 | 有 | 無 |

## 未來擴充建議

1. **持久化儲存**: 可將快取資料儲存到 Redis 或 SQLite
2. **預熱機制**: 系統啟動時預先載入熱門路線
3. **分散式快取**: 支援多執行個體共享快取
4. **智慧過期**: 根據路線活躍度調整過期時間
