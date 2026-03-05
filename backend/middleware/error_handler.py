# -*- coding: utf-8 -*-
"""
全域錯誤處理中間件
Global error handling middleware

這個模組就像一個「安全網」，當 API 發生錯誤時，
它會攔截錯誤並回傳統一格式的錯誤訊息給前端。
"""

import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """
    標準錯誤回應格式
    Standard error response format
    """
    success: bool = False
    error_code: str
    message: str
    detail: Optional[Any] = None
    timestamp: str
    path: Optional[str] = None


class APIError(Exception):
    """
    自定義 API 錯誤類別
    Custom API error class
    """
    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR", status_code: int = 500, detail: Any = None):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class ScraperError(APIError):
    """
    爬蟲相關錯誤
    Scraper-related errors
    """
    def __init__(self, message: str, detail: Any = None):
        super().__init__(
            message=message,
            error_code="SCRAPER_ERROR",
            status_code=503,
            detail=detail
        )


class ValidationError(APIError):
    """
    資料驗證錯誤
    Data validation errors
    """
    def __init__(self, message: str, detail: Any = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            detail=detail
        )


class NotFoundError(APIError):
    """
    資源未找到錯誤
    Resource not found errors
    """
    def __init__(self, message: str, detail: Any = None):
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=404,
            detail=detail
        )


def setup_error_handlers(app: FastAPI) -> None:
    """
    設定全域錯誤處理器
    Setup global error handlers

    就像給 API 穿上防護衣，各種錯誤都會被優雅地處理
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """處理 HTTP 異常"""
        logger.warning(f"HTTP {exc.status_code}: {exc.detail} - Path: {request.url.path}")

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error_code=f"HTTP_{exc.status_code}",
                message=str(exc.detail),
                timestamp=datetime.now().isoformat(),
                path=request.url.path
            ).dict()
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """處理請求驗證錯誤（例如缺少必填欄位）"""
        logger.warning(f"Validation error: {exc.errors()} - Path: {request.url.path}")

        # 簡化錯誤訊息
        simplified_errors = []
        for error in exc.errors():
            simplified_errors.append({
                "field": ".".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })

        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error_code="VALIDATION_ERROR",
                message="請求資料格式不正確",
                detail=simplified_errors,
                timestamp=datetime.now().isoformat(),
                path=request.url.path
            ).dict()
        )

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError):
        """處理自定義 API 錯誤"""
        logger.error(f"API Error [{exc.error_code}]: {exc.message} - Path: {request.url.path}")

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error_code=exc.error_code,
                message=exc.message,
                detail=exc.detail,
                timestamp=datetime.now().isoformat(),
                path=request.url.path
            ).dict()
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """處理所有未預期的異常"""
        error_traceback = traceback.format_exc()
        logger.error(f"Unexpected error: {str(exc)}\n{error_traceback}")

        # 在生產環境中不要暴露詳細錯誤訊息
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error_code="INTERNAL_SERVER_ERROR",
                message="伺服器內部錯誤，請稍後再試",
                detail=None,  # 不暴露內部錯誤細節
                timestamp=datetime.now().isoformat(),
                path=request.url.path
            ).dict()
        )

    logger.info("✅ 錯誤處理中間件已啟動")
