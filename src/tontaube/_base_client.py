import base64
import warnings

import httpx
from packaging.version import Version
from typing import Optional, Tuple, Type

from ._exceptions import APIError, OutdatedSDKError
from .version import __version__
from .core import AudioInput, build_headers, read_audio
from .models import GenerateRequest, GenerateResponse
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
        if response.is_error:
            raise APIError(response, *self._error_details(response))
        return response

    @staticmethod
    def _error_details(response: httpx.Response) -> Tuple[Optional[str], str]:
        try:
            detail = response.json().get("detail")
        except Exception:
            detail = None
        if isinstance(detail, dict):
            return detail.get("error"), detail.get("message") or str(detail)
        if isinstance(detail, list) and detail:
            messages = [item.get("msg", str(item)) if isinstance(item, dict) else str(item) for item in detail]
            return "invalid_request", "; ".join(messages)
        if isinstance(detail, str):
            return None, detail
        return None, response.text or response.reason_phrase

    @staticmethod
    def _speech_payload(model: Type[GenerateRequest], voice_audio: Optional[AudioInput] = None, **fields) -> dict:
        if voice_audio is not None:
            fields["voice_audio_b64"] = base64.b64encode(read_audio(voice_audio)[1]).decode("ascii")
        return model(**fields).model_dump(mode="json", exclude_none=True)

    @staticmethod
    def _speech_response(response: httpx.Response) -> GenerateResponse:
        headers = response.headers
        fields = {
            "mime_type": headers.get("content-type"),
            "sample_rate": headers.get("x-sample-rate"),
            "audio_duration": headers.get("x-audio-duration"),
            "cost_usd": headers.get("x-cost-usd"),
            "balance_usd": headers.get("x-balance-usd"),
            "seed": headers.get("x-seed"),
            "request_id": headers.get("x-request-id"),
        }
        if not fields["mime_type"] or not fields["mime_type"].startswith("application/json"):
            return GenerateResponse(content=response.content, **fields)
        body = response.json()
        content = base64.b64decode(body.pop("audio_b64"))
        body["audio_duration"] = body.pop("duration", fields["audio_duration"])
        return GenerateResponse(content=content, **{**fields, **body})

    @staticmethod
    def _voice_upload(name: str, audio: AudioInput, language: Optional[str]) -> dict:
        data = {"name": name}
        if language is not None:
            data["language"] = language
        return {"data": data, "files": {"file": read_audio(audio)}}
