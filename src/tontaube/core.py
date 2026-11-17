from typing import Optional
from ._constants import DEFAULT_USER_AGENT
from .version import __version__


def build_headers(api_key: Optional[str] = None) -> dict:
    headers = {
        "Content-Type": "application/json",
        "User-Agent": DEFAULT_USER_AGENT,
        "X-SDK-Version": __version__,
    }
    if api_key is not None:
        headers["X-API-Key"] = api_key
    return headers
