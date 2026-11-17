import warnings

import httpx
from packaging.version import Version
from typing import Optional

from ._exceptions import OutdatedSDKError
from .version import __version__
from .core import build_headers
from ._constants import DEFAULT_BASE_URL, DEFAULT_TIMEOUT


class BaseClient:
    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL, _check_version: bool = True):
        self.api_key = api_key
        self.base_url = base_url
        self._headers = build_headers(self.api_key)
        self._timeout = DEFAULT_TIMEOUT
        self._should_check_version = _check_version

    def _evaluate_version(self, data: dict) -> None:
        current = Version(__version__)
        min_version = Version(data["min_version"])
        latest_version = Version(data["latest_version"])

        if current < min_version:
            raise RuntimeError(
                f"This version of the SDK ({__version__}) is no longer supported. "
                f"Minimum required version is {min_version}. "
                "Please upgrade: pip install --upgrade tontaube"
            )

        if current < latest_version:
            warnings.warn(
                f"A newer version of the SDK is available ({latest_version}). "
                f"You are using {__version__}. "
                "Please upgrade: pip install --upgrade tontaube",
                DeprecationWarning,
                stacklevel=3,
            )

    def _handle_response(self, response: httpx.Response) -> httpx.Response:
        if response.status_code == 426:
            try:
                body = response.json()
                message = body.get("message", "SDK upgrade required.")
                upgrade_command = body.get(
                    "upgrade_command", "pip install --upgrade tontaube"
                )
            except Exception:
                message = "SDK upgrade required."
                upgrade_command = "pip install --upgrade tontaube"
            raise OutdatedSDKError(f"{message} Upgrade with: {upgrade_command}")
        response.raise_for_status()
        return response
