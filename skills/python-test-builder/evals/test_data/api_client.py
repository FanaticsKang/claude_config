import requests
from typing import Dict, Any, Optional
import time


class ApiClient:
    """API 客户端示例"""

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self._session = requests.Session()

        if api_key:
            self._session.headers.update({"Authorization": f"Bearer {api_key}"})

    def get_user(self, user_id: int) -> Dict[str, Any]:
        """获取用户信息"""
        if user_id <= 0:
            raise ValueError("user_id must be positive")

        url = f"{self.base_url}/users/{user_id}"
        response = self._session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def create_order(self, user_id: int, items: list) -> Dict[str, Any]:
        """创建订单"""
        if not items:
            raise ValueError("items cannot be empty")

        url = f"{self.base_url}/orders"
        payload = {
            "user_id": user_id,
            "items": items,
            "timestamp": int(time.time())
        }

        response = self._session.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def retry_request(self, func, max_retries: int = 3) -> Any:
        """带重试的请求"""
        last_exception = None

        for attempt in range(max_retries):
            try:
                return func()
            except requests.RequestException as e:
                last_exception = e
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避

        raise last_exception
