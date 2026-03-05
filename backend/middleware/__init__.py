# -*- coding: utf-8 -*-
"""
中間件模組 - 錯誤處理、日誌等
Middleware module - Error handling, logging, etc.
"""

from .error_handler import setup_error_handlers

__all__ = ["setup_error_handlers"]
