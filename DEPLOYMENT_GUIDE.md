# 部署指南

## 系統需求

### 後端 (Python/FastAPI)

- Python 3.11+
- 記憶體：至少 2GB RAM
- 硬碟：至少 1GB 可用空間（CSV 資料儲存）

### 前端 (Flutter)

- Flutter 3.16+
- Dart 3.0+
- Android SDK 或 iOS Xcode

## 後端部署

### 1. 環境設定

```bash
# 建立虛擬環境
python -m venv venv

# 啟動虛擬環境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安裝相依套件
pip install -r requirements.txt

# 安裝 Playwright 瀏覽器
playwright install chromium
```

### 2. 環境變數設定

建立 `.env` 檔案：

```env
# API 設定
HOST=0.0.0.0
PORT=8000

# 資料目錄
NTPC_BUS_DATA_DIR=./data/ntpc_bus

# 快取設定
ROUTE_CACHE_SIZE=500
ROUTE_CACHE_TTL=600
ESTIMATION_CACHE_SIZE=1000
ESTIMATION_CACHE_TTL=60

# 日誌設定
LOG_LEVEL=INFO
```

### 3. 啟動服務

#### 開發模式

```bash
python main.py
```

#### 生產模式（使用 uvicorn）

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

或使用 gunicorn：

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 4. Docker 部署

建立 Dockerfile：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安裝系統相依
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# 複製專案檔案
COPY requirements.txt .
RUN pip install -r requirements.txt

# 安裝 Playwright 瀏覽器
RUN playwright install chromium
RUN playwright install-deps chromium

# 複製程式碼
COPY . .

# 建立資料目錄
RUN mkdir -p data/ntpc_bus

# 暴露埠
EXPOSE 8000

# 啟動命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

建立並執行容器：

```bash
# 建立映像檔
docker build -t taiwan-transport-api .

# 執行容器
docker run -d \
  --name transport-api \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  taiwan-transport-api
```

## 前端部署

### 1. 設定 API 位址

編輯 `transport_flutter/lib/services/bus_api_service.dart`：

```dart
// 開發環境
static const String _baseUrl = 'http://10.0.2.2:8000/api';

// 生產環境（請修改為你的伺服器位址）
// static const String _baseUrl = 'https://your-server.com/api';
```

### 2. 建置 APK（Android）

```bash
cd transport_flutter

# 開發版本
flutter build apk

# 生產版本
flutter build apk --release

# 輸出位置：build/app/outputs/flutter-apk/app-release.apk
```

### 3. 建置 IPA（iOS）

```bash
cd transport_flutter

# 建置 iOS 版本
flutter build ios --release

# 使用 Xcode 開啟專案並簽署
cd ios
xcodebuild -workspace Runner.xcworkspace -scheme Runner -configuration Release archive -archivePath Runner.xcarchive
```

## 效能優化

### 後端優化

1. **記憶體快取**
   - 路線資料快取 10 分鐘
   - 到站時間快取 1 分鐘
   - 自動 LRU 淘汰機制

2. **背景更新**
   - 每分鐘自動更新到站時間
   - 每 5 分鐘記錄快取統計

3. **Playwright 最佳實踐**
   - 使用 headless 模式
   - 重複使用瀏覽器實例
   - 適當的 timeout 設定

### 資料庫優化

CSV 資料會自動下載並快取：

```
data/ntpc_bus/
├── stops_YYYYMMDD.csv      # 站牌資料（每日更新）
├── routes_YYYYMMDD.csv     # 路線資料（每日更新）
└── estimations_latest.csv  # 到站時間（每分鐘更新）
```

### 監控與維護

#### 健康檢查

```bash
# 檢查系統健康
curl http://localhost:8000/api/health

# 檢查詳細狀態
curl http://localhost:8000/api/system/status

# 手動重新整理資料
curl -X POST http://localhost:8000/api/system/refresh
```

#### 日誌監控

```bash
# 查看即時日誌
tail -f backend.log

# 或使用 journalctl（systemd）
journalctl -u transport-api -f
```

## 常見問題

### Q1: CSV 資料下載失敗？

檢查網路連接並手動測試：

```bash
curl -o test.csv "https://data.ntpc.gov.tw/api/datasets/34b402a8-53d9-483d-9406-24a682c2d6dc/csv/file"
```

### Q2: 記憶體使用量過高？

調整快取設定：

```env
ROUTE_CACHE_SIZE=200
ESTIMATION_CACHE_SIZE=500
```

### Q3: Playwright 啟動失敗？

重新安裝瀏覽器：

```bash
playwright uninstall chromium
playwright install chromium
```

## 安全建議

1. **使用 HTTPS**
   - 生產環境務必使用 SSL/TLS
   - 可使用 Let's Encrypt 免費憑證

2. **設定防火牆**
   - 僅開放必要的埠（80, 443）
   - 限制後端 API 存取來源

3. **定期更新**
   - 保持作業系統與套件更新
   - 監控安全性公告

## 聯絡支援

如有問題，請檢查：
1. 日誌檔案（backend.log）
2. 健康檢查端點（/api/health）
3. 系統狀態端點（/api/system/status）
