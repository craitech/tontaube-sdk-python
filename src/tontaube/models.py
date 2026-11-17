from datetime import datetime
from typing import ClassVar, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, model_validator

_MAX_TEXT_LENGTH = 30_000
_SINGLE_CALL_MAX_TEXT_LENGTH = 2_000
_STREAM_MAX_TEXT_LENGTH = 6_000
_ALLOWED_FORMATS = ["wav", "mp3", "opus"]

class Speaker(BaseModel):
    id: str
    name: str
    voice_key: str
    gender: Optional[str] = None
    language_restrictions: Optional[List[str]] = None
    voice_style: Optional[str] = None
    preview_url: Optional[str] = None

class Voice(BaseModel):
    id: str
    name: str
    type: str
    languages: List[str] = []
    preview_url: Optional[str] = None
    language: Optional[str] = None
    duration_seconds: Optional[float] = None
    created_at: Optional[datetime] = None
    model_version: Optional[str] = None
    n_codebooks: Optional[int] = None
    codec: Optional[str] = None
    gender: Optional[str] = None
    voice_style: Optional[str] = None

class Controls(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rate: Optional[int] = Field(None, ge=0, le=4)
    pause: Optional[int] = Field(None, ge=0, le=4)
    pitch_range: Optional[int] = Field(None, ge=0, le=5)
    pitch_level: Optional[int] = Field(None, ge=0, le=4)
    legato: Optional[int] = Field(None, ge=0, le=2)

class ContextSlice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ref: str = Field(repr=False)
    start: int = Field(ge=0)
    end: int = Field(ge=1)

class Silence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    silence: int = Field(ge=1, le=25)

class Prefix(BaseModel):
    text: str
    context: Optional[List[Union[ContextSlice, Silence]]] = None

class Word(BaseModel):
    text: str
    start: Optional[float] = None
    end: Optional[float] = None
    char_start: int
    char_end: int
    confidence: float

class Character(BaseModel):
    char: str
    index: int
    start: Optional[float] = None
    end: Optional[float] = None

class Timestamps(BaseModel):
    text: str
    words: List[Word] = []
    characters: List[Character] = []

class GenerateRequest(BaseModel):
    _single_call_max_text_length: ClassVar[int] = _SINGLE_CALL_MAX_TEXT_LENGTH

    text: str
    voice_id: Optional[str] = None
    voice_audio_b64: Optional[str] = Field(None, repr=False)
    speaker_id: Optional[str] = None
    language: Optional[str] = None
    format: Optional[str] = None
    temperature: Optional[float] = None
    controls: Optional[Controls] = None
    style: Optional[Literal["audiobook", "conversational", "agentic"]] = None
    seed: Optional[int] = Field(None, ge=0, le=2**32 - 1)
    prefix: Optional[Prefix] = None
    return_context: Optional[bool] = None
    include_timestamps: Optional[bool] = None
    audio_format: Optional[Literal["opus", "wav", "flac"]] = None
    sample_rate: Optional[Literal[24000, 48000]] = None

    @model_validator(mode="after")
    def validate_request(self):
        sources = [self.voice_id, self.voice_audio_b64, self.speaker_id]
        if sum(source is not None for source in sources) != 1:
            raise ValueError("Provide exactly one of voice_id, voice_audio or speaker_id")
        if len(self.text) > _MAX_TEXT_LENGTH:
            raise ValueError(f"Text length must be at most {_MAX_TEXT_LENGTH} characters")
        if self.single_call and len(self.text) > self._single_call_max_text_length:
            raise ValueError(
                "With prefix, return_context, include_timestamps, seed or style, "
                f"text length must be at most {_SINGLE_CALL_MAX_TEXT_LENGTH} characters"
            )
        if (self.audio_format or self.sample_rate) and not (self.return_context or self.include_timestamps):
            raise ValueError("audio_format and sample_rate need return_context or include_timestamps")
        if self.format and self.format.lower() not in _ALLOWED_FORMATS:
            raise ValueError(f"Format must be one of: {', '.join(_ALLOWED_FORMATS)}")
        if self.temperature is not None and (self.temperature < 0.5 or self.temperature > 2.0):
            raise ValueError("Temperature must be between 0.5 and 2.0")
        return self

    @property
    def single_call(self) -> bool:
        return bool(
            self.return_context or self.include_timestamps or self.prefix is not None
            or self.seed is not None or self.style
        )

class StreamRequest(GenerateRequest):
    _single_call_max_text_length: ClassVar[int] = _STREAM_MAX_TEXT_LENGTH

    @model_validator(mode="after")
    def validate_stream(self):
        if self.return_context or self.include_timestamps:
            raise ValueError("return_context and include_timestamps are not available when streaming")
        if len(self.text) > _STREAM_MAX_TEXT_LENGTH:
            raise ValueError(f"Text length must be at most {_STREAM_MAX_TEXT_LENGTH} characters when streaming")
        return self

class GenerateResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    content: bytes = Field(repr=False)
    mime_type: Optional[str] = None
    sample_rate: Optional[int] = None
    audio_duration: Optional[float] = None
    cost_usd: Optional[float] = None
    balance_usd: Optional[float] = None
    seed: Optional[int] = None
    request_id: Optional[str] = None
    context: Optional[str] = Field(None, repr=False)
    n_frames: Optional[int] = None
    frame_hz: Optional[float] = None
    model_version: Optional[str] = None
    timestamps: Optional[Timestamps] = None

    def context_slice(self, start: int = 0, end: Optional[int] = None) -> ContextSlice:
        if self.context is None:
            raise ValueError("This response has no context, generate it with return_context=True")
        return ContextSlice(ref=self.context, start=start, end=self.n_frames if end is None else end)
