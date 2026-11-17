import os
from pathlib import Path
from typing import BinaryIO, Optional, Tuple, Union
from ._constants import DEFAULT_USER_AGENT
from .version import __version__

AudioInput = Union[bytes, str, os.PathLike, BinaryIO]


def build_headers(api_key: Optional[str] = None) -> dict:
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "X-SDK-Version": __version__,
    }
    if api_key is not None:
        headers["X-API-Key"] = api_key
    return headers


def read_audio(audio: AudioInput) -> Tuple[str, bytes]:
    if isinstance(audio, (bytes, bytearray)):
        return "audio", bytes(audio)
    if isinstance(audio, (str, os.PathLike)):
        path = Path(audio)
        return path.name, path.read_bytes()
    return Path(getattr(audio, "name", "audio")).name, audio.read()
