"""
台灣交通時刻表 API - 重構版本
Taiwan Transport Timetable API - Refactored Version

這是 FastAPI 後端的主程式，採用模組化架構設計。
整合了台鐵、高鐵、公車三種交通工具的查詢功能。

主要特色：
- 使用 Playwright 進行網頁爬蟲
- 支援快取機制提升效能
- 完整的錯誤處理與重試機制
- CORS 設定支援 Flutter 前端
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import async_playwright, Browser

# 匯入配置
from config import settings

# 匯入資料模型
from models.bus_models import (
    BusRoute, BusTimeEntry, BusRealTimeArrival,
    BusStop, BusVehicle, BusRouteData
)
from models.railway_models import TrainStation, TrainTimeEntry
from models.thsr_models import THSRTrainEntry, THSRStation

# 匯入路由
from routers import health, bus, railway, thsr

# 匯入中間件
from middleware.error_handler import setup_error_handlers

# ==================== 全域變數 ====================

# Playwright 瀏覽器實例（全域共用）
_pw = None
_browser: Optional[Browser] = None


def get_browser() -> Optional[Browser]:
    """
    取得 Playwright 瀏覽器實例

    Returns:
        Browser: Playwright 瀏覽器實例，如果尚未初始化則返回 None
    """
    return _browser


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命週期管理器

    負責應用程式的啟動和關閉邏輯：
    - 啟動時：初始化 Playwright 瀏覽器
    - 關閉時：清理資源，關閉瀏覽器和 HTTP 客戶端

    Args:
        app: FastAPI 應用實例
    """
    global _pw, _browser

    # ===== 啟動階段 =====
    print("🚀 正在啟動台灣交通時刻表 API...")

    # 初始化 Playwright
    _pw = await async_playwright().start()
    _browser = await _pw.chromium.launch(
        headless=True,  # 無頭模式運行
        args=[
            '--disable-blink-features=AutomationControlled',  # 禁用自動化檢測
            '--no-sandbox',  # 在容器環境中需要
            '--disable-dev-shm-usage'  # 減少記憶體使用
        ]
    )
    print("✅ Playwright 瀏覽器已啟動")

    yield  # 應用程式運行期間

    # ===== 關閉階段 =====
    print("🛑 正在關閉 API 服務...")

    # 關閉瀏覽器
    if _browser:
        try:
            await _browser.close()
            print("✅ 瀏覽器已關閉")
        except Exception as e:
            print(f"⚠️ 瀏覽器關閉時發生錯誤: {e}")

    # 停止 Playwright
    if _pw:
        try:
            await _pw.stop()
            print("✅ Playwright 已停止")
        except Exception as e:
            print(f"⚠️ Playwright 停止時發生錯誤: {e}")

    print("👋 API 服務已完全關閉")


# ==================== FastAPI 應用初始化 ====================

def create_application() -> FastAPI:
    """
    創建並配置 FastAPI 應用實例

    這個工廠函式負責：
    1. 創建 FastAPI 實例
    2. 設定 CORS 中間件
    3. 註冊所有路由
    4. 設定錯誤處理

    Returns:
        FastAPI: 配置完成的 FastAPI 應用實例
    """

    # 創建 FastAPI 應用
    app = FastAPI(
        title=settings.APP_NAME,
        description="提供台灣台鐵、高鐵、公車時刻表查詢服務",
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs",  # Swagger UI 路徑
        redoc_url="/redoc",  # ReDoc 路徑
    )

    # ===== CORS 設定 =====
    # 允許 Flutter 前端跨域請求
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],  # 允許所有 HTTP 方法
        allow_headers=["*"],  # 允許所有標頭
    )

    # ===== 註冊路由 =====
    # 健康檢查端點
    app.include_router(health.router, tags=["Health"])

    # 公車相關 API
    app.include_router(
        bus.router,
        prefix="/api/bus",
        tags=["Bus"]
    )

    # 台鐵相關 API
    app.include_router(
        railway.router,
        prefix="/api/railway",
        tags=["Railway"]
    )

    # 高鐵相關 API
    app.include_router(
        thsr.router,
        prefix="/api/thsr",
        tags=["THSR"]
    )

    # ===== 設定錯誤處理 =====
    setup_error_handlers(app)

    # ===== 根端點 =====
    @app.get("/")
    async def root():
        """
        API 根端點 - 顯示基本資訊

        Returns:
            dict: API 基本資訊
        """
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "description": "台灣交通時刻表查詢 API",
            "endpoints": {
                "docs": "/docs",
                "health": "/api/health",
                "bus": "/api/bus",
                "railway": "/api/railway",
                "thsr": "/api/thsr"
            },
            "timestamp": datetime.now().isoformat()
        }

    return app


# 創建應用實例
app = create_application()


# ==================== 主程式入口 ====================

if __name__ == "__main__":
    import uvicorn

    print(f"🚀 啟動 {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📍 監聽地址: http://{settings.HOST}:{settings.PORT}")
    print(f"📚 API 文件: http://{settings.HOST}:{settings.PORT}/docs")

    uvicorn.run(
        "main_refactored:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,  # 開發模式啟用熱重載
        log_level="info"
    )
