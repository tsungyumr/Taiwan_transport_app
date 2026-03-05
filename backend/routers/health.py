"""
健康檢查路由模組
提供系統狀態監控端點
"""

from fastapi import APIRouter, Request
from datetime import datetime
from typing import Dict

router = APIRouter(
    prefix="/api/health",
    tags=["health"],
    responses={404: {"description": "Not found"}}
)


@router.get("/")
async def health_check(request: Request) -> Dict[str, str]:
    """
    健康檢查端點 - 確認服務是否正常運行

    Returns:
        Dict[str, str]: 包含狀態和時間戳的資訊

    Example:
        {
            "status": "ok",
            "timestamp": "2026-03-04T10:30:00.123456"
        }
    """
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/detailed")
async def detailed_health_check(request: Request) -> Dict:
    """
    詳細健康檢查端點 - 提供更多系統狀態資訊

    Returns:
        Dict: 包含服務狀態、Playwright 狀態等詳細資訊
    """
    # 取得 app state 中的 browser 實例（如果存在）
    browser = getattr(request.app.state, 'browser', None)

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "playwright": "active" if browser else "inactive",
        "version": "2.0.0",
        "services": {
            "railway": "available",
            "thsr": "available",
            "bus": "available"
        }
    }
