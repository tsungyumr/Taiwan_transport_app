"""
TDX API OAuth 2.0 認證模組
處理 TDX API 的 OAuth 2.0 認證流程與權杖管理
"""
import base64
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict

import httpx

logger = logging.getLogger(__name__)

# TDX API 認證設定
TDX_AUTH_URL = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
TDX_API_BASE_URL = "https://tdx.transportdata.tw/api"

# 用戶提供的認證資訊
DEFAULT_CLIENT_ID = "tsungyumr-01112815-ad21-4504"
DEFAULT_CLIENT_SECRET = "4966f67c-3165-4f1d-88cf-ffd12b6de7a9"


class TDXAuth:
    """
    TDX API OAuth 2.0 認證管理器

    處理 access token 的取得、快取與自動更新
    """

    def __init__(
        self,
        client_id: str = DEFAULT_CLIENT_ID,
        client_secret: str = DEFAULT_CLIENT_SECRET,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None
        self._token_buffer_seconds = 60  # 提前 60 秒更新權杖，避免邊界問題

    def _is_token_valid(self) -> bool:
        """檢查目前的 access token 是否仍然有效"""
        if not self._access_token or not self._token_expires_at:
            return False
        # 預留緩衝時間，避免在請求過程中過期
        return time.time() < (self._token_expires_at - self._token_buffer_seconds)

    async def get_access_token(self) -> str:
        """
        取得 TDX API 的 access token

        如果已有有效的快取權杖，直接回傳；
        否則向 TDX 認證伺服器請求新的權杖。

        Returns:
            有效的 access token 字串

        Raises:
            Exception: 當認證失敗時拋出例外
        """
        if self._is_token_valid():
            logger.debug("使用快取的 access token")
            return self._access_token

        logger.info("向 TDX 請求新的 access token")

        # 準備 OAuth 2.0 client credentials 請求
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    TDX_AUTH_URL,
                    headers=headers,
                    data=data,
                    timeout=30.0,
                )
                response.raise_for_status()

                token_data = response.json()
                self._access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 3600)  # 預設 1 小時

                # 計算過期時間
                self._token_expires_at = time.time() + expires_in

                logger.info(f"成功取得 access token，有效期 {expires_in} 秒")
                return self._access_token

        except httpx.HTTPStatusError as e:
            logger.error(f"TDX 認證 HTTP 錯誤: {e.response.status_code} - {e.response.text}")
            raise Exception(f"TDX 認證失敗: HTTP {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"TDX 認證請求錯誤: {e}")
            raise Exception(f"TDX 認證請求失敗: {e}")
        except Exception as e:
            logger.error(f"TDX 認證未知錯誤: {e}")
            raise Exception(f"TDX 認證失敗: {e}")

    async def get_auth_headers(self) -> Dict[str, str]:
        """
        取得包含認證資訊的 HTTP 標頭

        Returns:
            包含 Authorization 標頭的字典
        """
        token = await self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def clear_cache(self):
        """清除快取的權杖（用於測試或強制重新認證）"""
        self._access_token = None
        self._token_expires_at = None
        logger.info("已清除 access token 快取")


# 全域認證實例（單例模式）
_tdx_auth_instance: Optional[TDXAuth] = None


def get_tdx_auth(
    client_id: str = DEFAULT_CLIENT_ID,
    client_secret: str = DEFAULT_CLIENT_SECRET,
) -> TDXAuth:
    """
    取得 TDX 認證實例（單例模式）

    Args:
        client_id: TDX 應用程式 ID
        client_secret: TDX 應用程式密鑰

    Returns:
        TDXAuth 實例
    """
    global _tdx_auth_instance
    if _tdx_auth_instance is None:
        _tdx_auth_instance = TDXAuth(client_id, client_secret)
    return _tdx_auth_instance


# 測試函數
async def test_auth():
    """測試 TDX 認證功能"""
    print("測試 TDX OAuth 2.0 認證...")

    auth = get_tdx_auth()

    # 測試取得 token
    try:
        token = await auth.get_access_token()
        print(f"[OK] 成功取得 access token: {token[:50]}...")

        # 測試快取機制
        start_time = time.time()
        token2 = await auth.get_access_token()
        elapsed = time.time() - start_time
        print(f"[OK] 快取機制正常，第二次取得耗時 {elapsed:.4f} 秒")

        # 測試 headers
        headers = await auth.get_auth_headers()
        print(f"[OK] 認證標頭產生成功: {headers['Authorization'][:30]}...")

        return True
    except Exception as e:
        print(f"[FAIL] 認證失敗: {e}")
        return False


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    asyncio.run(test_auth())
