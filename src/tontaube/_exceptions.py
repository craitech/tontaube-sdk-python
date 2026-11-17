from typing import Optional

import httpx


class OutdatedSDKError(Exception):
    """Raised when the API returns HTTP 426 Upgrade Required."""


class APIError(httpx.HTTPStatusError):
    def __init__(self, response: httpx.Response, code: Optional[str], message: str):
        prefix = f"{response.status_code} {code}" if code else str(response.status_code)
        super().__init__(f"{prefix}: {message}", request=response.request, response=response)
        self.status_code = response.status_code
        self.code = code
        self.message = message
