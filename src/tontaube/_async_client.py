from typing import List, Optional

import httpx

from .models import Speaker, GenerateRequest, GenerateResponse
from ._base_client import BaseClient
from ._constants import DEFAULT_BASE_URL, VERSION_CHECK_TIMEOUT


class AsyncClient(BaseClient):
    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL, **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self._http_client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers,
            timeout=self._timeout,
        )

    async def check_version(self) -> None:
        try:
            response = await self._http_client.get("/sdk-status", timeout=VERSION_CHECK_TIMEOUT)
            response.raise_for_status()
            self._evaluate_version(response.json())
        except RuntimeError:
            raise
        except Exception:
            return

    async def list_speakers(self) -> List[Speaker]:
        response = await self._http_client.get("/speech/speakers")
        self._handle_response(response)
        return [Speaker.model_validate(s) for s in response.json()]

    async def generate_speech(
        self,
        text: str,
        speaker_id: str,
        language: Optional[str] = None,
        format: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> GenerateResponse:
        payload = GenerateRequest(
            text=text,
            speaker_id=speaker_id,
            language=language,
            format=format,
            temperature=temperature,
        ).model_dump(exclude_none=True)

        response = await self._http_client.post("/speech/generate", json=payload)
        self._handle_response(response)
        return GenerateResponse(
            content=response.content,
            sample_rate=response.headers.get("x-sample-rate"),
            audio_duration=response.headers.get("x-audio-duration"),
            cost_usd=response.headers.get("x-cost-usd"),
            balance_usd=response.headers.get("x-balance-usd"),
        )

    async def close(self):
        await self._http_client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
