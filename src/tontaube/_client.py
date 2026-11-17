from typing import Iterator, List, Optional, Union

import httpx

from .models import Speaker, Voice, Controls, Prefix, GenerateRequest, GenerateResponse, StreamRequest
from .core import AudioInput
from ._base_client import BaseClient
from ._constants import DEFAULT_BASE_URL, VERSION_CHECK_TIMEOUT


class Client(BaseClient):
    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL, **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self._http_client = httpx.Client(
            base_url=self.base_url,
            headers=self._headers,
            timeout=self._timeout,
        )

    def check_version(self) -> None:
        try:
            response = self._http_client.get("/sdk-status", timeout=VERSION_CHECK_TIMEOUT)
            response.raise_for_status()
            self._evaluate_version(response.json())
        except RuntimeError:
            raise
        except Exception:
            return

    def list_speakers(self) -> List[Speaker]:
        response = self._http_client.get("/speech/speakers")
        self._handle_response(response)
        return [Speaker.model_validate(s) for s in response.json()]

    def list_voices(self, type: Optional[str] = None) -> List[Voice]:
        response = self._http_client.get("/voices", params={"type": type} if type else None)
        self._handle_response(response)
        return [Voice.model_validate(v) for v in response.json()]

    def get_voice(self, voice_id: str) -> Voice:
        response = self._http_client.get(f"/voices/{voice_id}")
        self._handle_response(response)
        return Voice.model_validate(response.json())

    def create_voice(self, name: str, audio: AudioInput, language: Optional[str] = None) -> Voice:
        response = self._http_client.post("/voices", **self._voice_upload(name, audio, language))
        self._handle_response(response)
        return Voice.model_validate(response.json())

    def delete_voice(self, voice_id: str) -> None:
        response = self._http_client.delete(f"/voices/{voice_id}")
        self._handle_response(response)

    def generate_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: Optional[str] = None,
        format: Optional[str] = None,
        temperature: Optional[float] = None,
        speaker_id: Optional[str] = None,
        voice_audio: Optional[AudioInput] = None,
        controls: Optional[Union[Controls, dict]] = None,
        style: Optional[str] = None,
        seed: Optional[int] = None,
        prefix: Optional[Union[Prefix, dict]] = None,
        return_context: Optional[bool] = None,
        include_timestamps: Optional[bool] = None,
        audio_format: Optional[str] = None,
        sample_rate: Optional[int] = None,
    ) -> GenerateResponse:
        payload = self._speech_payload(
            GenerateRequest,
            text=text,
            voice_id=voice_id,
            speaker_id=speaker_id,
            voice_audio=voice_audio,
            language=language,
            format=format,
            temperature=temperature,
            controls=controls,
            style=style,
            seed=seed,
            prefix=prefix,
            return_context=return_context,
            include_timestamps=include_timestamps,
            audio_format=audio_format,
            sample_rate=sample_rate,
        )

        response = self._http_client.post("/speech/generate", json=payload)
        self._handle_response(response)
        return self._speech_response(response)

    def stream_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: Optional[str] = None,
        temperature: Optional[float] = None,
        speaker_id: Optional[str] = None,
        voice_audio: Optional[AudioInput] = None,
        controls: Optional[Union[Controls, dict]] = None,
    ) -> Iterator[bytes]:
        payload = self._speech_payload(
            StreamRequest,
            text=text,
            voice_id=voice_id,
            speaker_id=speaker_id,
            voice_audio=voice_audio,
            language=language,
            temperature=temperature,
            controls=controls,
        )

        with self._http_client.stream("POST", "/speech/stream", json=payload) as response:
            if response.is_error:
                response.read()
            self._handle_response(response)
            yield from response.iter_bytes()

    def close(self):
        self._http_client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
