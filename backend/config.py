"""
配置管理模組
存放所有後端設定，包括 CORS、資料庫連線、API 設定等
"""

import os
from typing import List

# ==================== API 伺服器設定 ====================
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"

# ==================== CORS 設定 (允許 Flutter 前端存取) ====================
# 開發環境允許所有來源，生產環境請設定具體域名
ALLOWED_ORIGINS: List[str] = [
    "http://localhost:3000",      # React/Vue 開發伺服器
    "http://localhost:8080",      # 其他開發伺服器
    "http://localhost",           # Flutter Web
    "http://127.0.0.1",           # 本地測試
    "*",                          # 開發時允許所有來源 (生產環境建議移除)
]

# 生產環境的 CORS 設定 (建議)
PRODUCTION_ORIGINS: List[str] = [
    "https://your-app.com",
    "https://app.your-domain.com",
]

# ==================== Playwright 瀏覽器設定 ====================
BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"
BROWSER_TIMEOUT = int(os.getenv("BROWSER_TIMEOUT", "30000"))  # 30 秒
BROWSER_ARGS = ['--disable-blink-features=AutomationControlled']

# ==================== 快取設定 ====================
CACHE_TTL_RAILWAY = int(os.getenv("CACHE_TTL_RAILWAY", "300"))       # 台鐵快取 5 分鐘
CACHE_TTL_THSR = int(os.getenv("CACHE_TTL_THSR", "3600"))            # 高鐵站點快取 1 小時
CACHE_TTL_BUS = int(os.getenv("CACHE_TTL_BUS", "60"))                # 公車快取 1 分鐘

# ==================== 日誌設定 ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ==================== 外部 API 設定 ====================
# 台北市公車 Open Data
TAIPEI_BUS_DATASET_ID = "296cee16-9fc1-4bd9-bda4-7a4790f5a2d0"
TAIPEI_BUS_BASE_URL = "https://data.taipei/api/v1/dataset"
TAIPEI_BUS_REALTIME_URL = "https://www.5284.gov.taipei/ibus"

# 台鐵網站
TRA_WEBSITE_URL = "https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip112/gobytime"

# 高鐵網站
THSR_WEBSITE_URL = "https://www.thsrc.com.tw/"

# HTTP Client 設定
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "30.0"))
HTTP_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# ==================== API 文件設定 ====================
API_TITLE = "台灣交通時刻表 API"
API_DESCRIPTION = """
提供台灣交通運輸時刻表查詢服務，包含：

- **台鐵時刻表**: 查詢台灣鐵路列車時刻
- **高鐵時刻表**: 查詢台灣高鐵列車時刻
- **公車資訊**: 查詢大台北地區公車路線與即時到站資訊

使用 Playwright 進行網頁爬蟲，確保資料準確性。
"""
API_VERSION = "2.0.0"

# ==================== 錯誤重試設定 ====================
RETRY_MAX_ATTEMPTS = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
RETRY_DELAY_SECONDS = int(os.getenv("RETRY_DELAY_SECONDS", "2"))
