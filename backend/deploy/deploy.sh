# 台灣交通時刻表App - 公車API部署腳本

## 部署前準備

### 1. 安裝Docker
```bash
# Windows
# 安裝Docker Desktop for Windows

# Linux
# 根據您的發行版安裝Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### 2. 安裝Docker Compose
```bash
# Linux
# 通常與Docker一起安裝
# Windows
# 通常與Docker Desktop一起安裝
```

## 部署選項

### 選項1: Docker Compose（推薦）

#### 1.1 建立目錄結構
```bash
mkdir -p backend/deploy
cd backend/deploy
```

#### 1.2 建立Dockerfile
```dockerfile
# 使用Python 3.13的輕量級映像
FROM python:3.13-slim

# 設定工作目錄
WORKDIR /app

# 複製需求檔案
COPY requirements.txt .

# 安裝Python依賴
RUN pip install --no-cache-dir -r requirements.txt

# 安裝Playwright瀏覽器
RUN pip install playwright
RUN playwright install --with-deps

# 複製應用程式程式碼
COPY . .

# 暴露8000端口
EXPOSE 8000

# 設定環境變數
ENV PYTHONPATH=/app
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# 啟動指令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 1.3 建立docker-compose.yml
```yaml
version: '3.8'

services:
  taiwan-bus-api:
    build: .
    container_name: taiwan-bus-api
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app
      - PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
      - BUS_SCRAPER_HEADLESS=True
      - BUS_SCRAPER_CACHE_TTL_ROUTES=86400
      - BUS_SCRAPER_CACHE_TTL_VEHICLES=300
      - BUS_SCRAPER_CACHE_TTL_STOPS=604800
    volumes:
      - ./logs:/app/logs
      - ./cache:/app/cache
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/bus/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # 選用：Redis快取（如果需要）
  redis:
    image: redis:7-alpine
    container_name: taiwan-bus-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

#### 1.4 建立.env範本
```bash
# 應用程式配置
APP_NAME="Taiwan Bus API"
APP_VERSION="1.0.0"
APP_HOST="0.0.0.0"
APP_PORT="8000"

# 爬蟲配置
BUS_SCRAPER_HEADLESS=True
BUS_SCRAPER_USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
BUS_SCRAPER_TIMEOUT=30
BUS_SCRAPER_RETRIES=3

# 快取配置
BUS_SCRAPER_CACHE_TTL_ROUTES=86400
BUS_SCRAPER_CACHE_TTL_VEHICLES=300
BUS_SCRAPER_CACHE_TTL_STOPS=604800
BUS_SCRAPER_CACHE_DIR="/app/cache"

# Redis配置（如果使用Redis）
REDIS_HOST="redis"
REDIS_PORT="6379"
REDIS_DB=0
REDIS_PASSWORD=""

# 日誌配置
LOG_LEVEL="INFO"
LOG_DIR="/app/logs"
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5

# 健康檢查
HEALTH_CHECK_INTERVAL=30
HEALTH_CHECK_TIMEOUT=10
HEALTH_CHECK_RETRIES=3
```

#### 1.5 建立部署腳本
```bash
#!/bin/bash

# 台灣交通時刻表App - 公車API部署腳本

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 顯示標題
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}=  台灣交通時刻表App - 公車API部署 =
${BLUE}=========================================${NC}"

# 檢查Docker是否安裝
if ! command -v docker &> /dev/null; then
    echo -e "${RED}錯誤: Docker未安裝${NC}"
    echo "請先安裝Docker: https://www.docker.com/get-started"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}錯誤: Docker Compose未安裝${NC}"
    echo "請先安裝Docker Compose"
    exit 1
fi

# 建立目錄
mkdir -p logs cache

# 建立.env檔案
if [ ! -f .env ]; then
    echo -e "${YELLOW}建立.env檔案...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env檔案建立完成${NC}"
else
    echo -e "${YELLOW}.env檔案已存在，跳過建立${NC}"
fi

# 建立日誌目錄
mkdir -p logs

# 建立快取目錄
mkdir -p cache

# 建立部署目錄
mkdir -p deploy

# 顯示選項
echo ""
echo -e "${BLUE}部署選項:${NC}"
echo "1. 使用Docker Compose部署"
echo "2. 僅建立Docker映像"
echo "3. 離開"
echo ""
read -p "請選擇選項 (1-3): " option

case $option in
    1)
        echo -e "${YELLOW}開始使用Docker Compose部署...${NC}"

        # 檢查現有容器
        if docker-compose ps -q &> /dev/null; then
            echo -e "${YELLOW}停止現有容器...${NC}"
            docker-compose down
        fi

        # 建立並啟動容器
        echo -e "${YELLOW}建立並啟動容器...${NC}"
        docker-compose up -d --build

        echo -e "${GREEN}✓ 部署完成!${NC}"
        echo ""
        echo -e "${BLUE}服務資訊:${NC}"
        echo "API位址: http://localhost:8000"
        echo "API文件: http://localhost:8000/docs"
        echo "健康檢查: http://localhost:8000/api/bus/health"
        ;;
    2)
        echo -e "${YELLOW}建立Docker映像...${NC}"

        # 建立映像
        docker build -t taiwan-bus-api:latest .

        echo -e "${GREEN}✓ 映像建立完成!${NC}"
        echo "映像名稱: taiwan-bus-api:latest"
        ;;
    3)
        echo -e "${YELLOW}離開部署程序${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}錯誤: 無效的選項${NC}"
        exit 1
        ;;
esac

# 顯示狀態
echo -e "${YELLOW}顯示服務狀態...${NC}"
echo ""
docker-compose ps

echo ""
echo -e "${GREEN}部署完成!${NC}"
echo ""
echo -e "${BLUE}後續步驟:${NC}"
echo "1. 測試API: curl http://localhost:8000/api/bus/health"
echo "2. 檢查日誌: docker-compose logs taiwan-bus-api"
echo "3. 停止服務: docker-compose down"
```

#### 1.6 建立healthcheck腳本
```bash
#!/bin/bash

# 台灣交通時刻表App - 健康檢查腳本

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 檢查API健康狀態
check_health() {
    local url="$1"
    local timeout="$2"

    echo -e "${YELLOW}檢查API健康狀態: $url${NC}"

    if curl --output /dev/null --silent --head --fail --max-time $timeout "$url"; then
        echo -e "${GREEN}✓ API健康${NC}"
        return 0
    else
        echo -e "${RED}✗ API不健康${NC}"
        return 1
    fi
}

# 檢查API功能
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}=  台灣交通時刻表App - 健康檢查 =
${BLUE}=========================================${NC}"

# 檢查API可用性
if check_health "http://localhost:8000/api/bus/health" 10; then
    echo -e "${GREEN}✓ API服務可用${NC}"
else
    echo -e "${RED}✗ API服務不可用${NC}"
    exit 1
fi

# 檢查API端點功能
echo -e "${YELLOW}檢查API端點功能...${NC}"

# 檢查路線列表
if check_health "http://localhost:8000/api/bus/routes" 10; then
    echo -e "${GREEN}✓ 路線列表API正常${NC}"
else
    echo -e "${RED}✗ 路線列表API異常${NC}"
fi

# 檢查搜尋功能
if check_health "http://localhost:8000/api/bus/search?query=藍" 10; then
    echo -e "${GREEN}✓ 搜尋功能正常${NC}"
else
    echo -e "${RED}✗ 搜尋功能異常${NC}"
fi

# 檢查業者列表
if check_health "http://localhost:8000/api/bus/operators" 10; then
    echo -e "${GREEN}✓ 業者列表正常${NC}"
else
    echo -e "${RED}✗ 業者列表異常${NC}"
fi

# 檢查日誌
echo -e "${YELLOW}檢查日誌...${NC}"
if [ -f "logs/app.log" ]; then
    echo -e "${GREEN}✓ 日誌檔案存在${NC}"
    tail -n 5 logs/app.log
else
    echo -e "${YELLOW}日誌檔案不存在，可能還在初始化${NC}"
fi

# 檢查快取
echo -e "${YELLOW}檢查快取...${NC}"
if [ -d "cache" ]; then
    echo -e "${GREEN}✓ 快取目錄存在${NC}"
    echo "快取檔案數量: $(find cache -type f | wc -l)"
else
    echo -e "${YELLOW}快取目錄不存在，正在建立...${NC}"
    mkdir -p cache
fi

# 總結
echo ""
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}=  健康檢查完成 =${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""
echo -e "${GREEN}API服務狀態: 正常運行${NC}"
echo "API位址: http://localhost:8000"
echo "API文件: http://localhost:8000/docs"
echo ""
echo -e "${BLUE}後續步驟:${NC}"
echo "1. 開始使用API"
echo "2. 檢查詳細日誌: docker-compose logs taiwan-bus-api"
echo "3. 監控服務狀態"
```

### 選項2: 傳統部署

#### 2.1 建立部署目錄
```bash
mkdir -p backend/deploy
cd backend/deploy
```

#### 2.2 建立requirements.txt
```txt
# 核心框架
fastapi==0.104.1
uvicorn==0.24.0

# 爬蟲和資料處理
playwright==1.40.0
httpx==0.25.2
pydantic==2.5.0

# 快取和資料庫
redis==5.0.0
aiosqlite==0.20.1

# 工具套件
python-dotenv==1.0.0
python-multipart==0.0.6
jinja2==3.1.2
python-multipart==0.0.6
```

#### 2.3 建立啟動腳本
```bash
#!/bin/bash

# 台灣交通時刻表App - API啟動腳本

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 顯示標題
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}=  台灣交通時刻表App - API啟動 =
${BLUE}=========================================${NC}"

# 檢查Python版本
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}錯誤: Python未安裝${NC}"
    echo "請先安裝Python 3.13+"
    exit 1
fi

# 檢查pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}錯誤: pip未安裝${NC}"
    exit 1
fi

# 安裝依賴
echo -e "${YELLOW}安裝Python依賴...${NC}"
pip install -r requirements.txt

# 安裝Playwright瀏覽器
echo -e "${YELLOW}安裝Playwright瀏覽器...${NC}"
pip install playwright
playwright install --with-deps

# 檢查環境變數
if [ ! -f .env ]; then
    echo -e "${YELLOW}建立.env檔案...${NC}"
    cp .env.example .env
fi

# 啟動API
echo -e "${YELLOW}啟動API服務...${NC}"

# 檢查是否使用Docker
if command -v docker &> /dev/null; then
    echo -e "${YELLOW}使用Docker啟動...${NC}"
    docker run -d \
        --name taiwan-bus-api \
        -p 8000:8000 \
        -v $(pwd)/logs:/app/logs \
        -v $(pwd)/cache:/app/cache \
        -e BUS_SCRAPER_HEADLESS=True \
        --restart unless-stopped \
        taiwan-bus-api:latest
else
    echo -e "${YELLOW}使用uvicorn啟動...${NC}"
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
fi

# 顯示服務資訊
echo ""
echo -e "${GREEN}✓ API服務啟動完成!${NC}"
echo ""
echo -e "${BLUE}服務資訊:${NC}"
echo "API位址: http://localhost:8000"
echo "API文件: http://localhost:8000/docs"
echo "健康檢查: http://localhost:8000/api/bus/health"

# 監控日誌
echo ""
echo -e "${YELLOW}監控日誌...${NC}"
echo "按Ctrl+C停止監控"
tail -f logs/app.log
```

## 部署步驟

### 步驟1: 準備環境
```bash
# 1. 安裝Docker
# 2. 複製程式碼
# 3. 建立部署目錄
# 4. 設定環境變數
```

### 步驟2: 配置環境
```bash
# 複製範本檔案
cp .env.example .env

# 編輯.env檔案
# 設定您的配置選項
```

### 步驟3: 建置映像
```bash
# 建置Docker映像
docker build -t taiwan-bus-api:latest .

# 測試映像
docker run -it --rm taiwan-bus-api:latest /bin/bash
```

### 步驟4: 啟動服務
```bash
# 使用Docker Compose啟動
docker-compose up -d

# 或使用傳統方式
./start.sh
```

### 步驟5: 測試服務
```bash
# 測試健康檢查
curl http://localhost:8000/api/bus/health

# 測試API端點
curl http://localhost:8000/api/bus/routes
```

## 監控和維護

### 檢查服務狀態
```bash
# Docker Compose
docker-compose ps

# 檢查日誌
docker-compose logs taiwan-bus-api

# 檢查資源使用
docker stats
```

### 更新服務
```bash
# 停止服務
docker-compose down

# 更新程式碼
git pull

# 重建映像
docker-compose build

# 啟動服務
docker-compose up -d
```

### 備份資料
```bash
# 備份快取資料
cp -r cache cache_backup_$(date +%Y%m%d_%H%M%S)

# 備份日誌
cp -r logs logs_backup_$(date +%Y%m%d_%H%M%S)
```

## 常見問題

### Q: 為什麼API啟動失敗？
**A**: 檢查Docker是否正確安裝，並確認所有依賴已正確安裝。

### Q: 如何處理爬蟲被封鎖？
**A**: 檢查網路連線，並考慮調整爬蟲的延遲設定。

### Q: 如何擴展服務？
**A**: 使用Docker Compose的scale功能，或部署到Kubernetes。

### Q: 如何監控服務？
**A**: 使用健康檢查端點，並整合監控系統如Prometheus + Grafana。

## 聯絡資訊

- **作者**: Claude Code
- **Email**: noreply@anthropic.com
- **專案位置**: D:\source\Taiwan_transport_app\backend

## 授權

本部署腳本使用MIT授權條款。