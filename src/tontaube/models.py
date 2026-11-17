from typing import Optional, List
from pydantic import BaseModel, ConfigDict, model_validator

_MAX_TEXT_LENGTH = 30_000
_ALLOWED_FORMATS = ["wav", "mp3", "opus"]

class Speaker(BaseModel):
    id: str
    name: str
    voice_key: str
    gender: Optional[str] = None
    language_restrictions: Optional[List[str]] = None
    voice_style: Optional[str] = None
    preview_url: Optional[str] = None

class GenerateRequest(BaseModel):
    text: str
    speaker_id: str
    language: Optional[str] = None
    format: Optional[str] = None
    temperature: Optional[float] = None

    @model_validator(mode="after")
    def validate_request(self):
        if len(self.text) > _MAX_TEXT_LENGTH:
            raise ValueError(f"Text length must be at most {_MAX_TEXT_LENGTH} characters")
        if self.format and self.format.lower() not in _ALLOWED_FORMATS:
            raise ValueError(f"Format must be one of: {', '.join(_ALLOWED_FORMATS)}")
        if self.temperature and (self.temperature < 0.5 or self.temperature > 2.0):
            raise ValueError("Temperature must be between 0.5 and 2.0")
        return self

class GenerateResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    content: bytes
    sample_rate: Optional[int] = None
    audio_duration: Optional[float] = None
    cost_usd: Optional[float] = None
    balance_usd: Optional[float] = None