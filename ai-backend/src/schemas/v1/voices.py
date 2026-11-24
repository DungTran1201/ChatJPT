"""Voice Management & VoiceVox TTS API schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field
from src.models.v1.voice import DEFAULT_VOICE_SAMPLE_TEXT


class VoiceSummaryResponse(BaseModel):
    id: str
    name: str
    character_name: str
    speaker_id: int
    style_name: Optional[str] = "Normal"
    gender: str = "female"
    description: Optional[str] = None
    speed_scale: float = 1.0
    pitch_scale: float = 0.0
    intonation_scale: float = 1.0
    volume_scale: float = 1.0
    sample_text: Optional[str] = None
    avatar_url: Optional[str] = None
    status: str = "ACTIVE"
    is_system_preset: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class VoiceListResponse(BaseModel):
    total: int
    items: List[VoiceSummaryResponse]


class VoiceEngineStatusResponse(BaseModel):
    engine_available: bool
    engine_url: str
    version: Optional[str] = None
    latency_ms: Optional[float] = None
    cached_audio_count: int = 0
    error: Optional[str] = None
    engine_mode: Optional[str] = "embedded_core"
    loaded_models_count: Optional[int] = 0
    supported_speakers_count: Optional[int] = 0


class VoiceCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    character_name: str = Field(..., min_length=1, max_length=100)
    speaker_id: int = Field(..., ge=0)
    style_name: Optional[str] = Field(default="Normal", max_length=50)
    gender: Optional[str] = Field(default="female")
    description: Optional[str] = Field(default=None, max_length=500)
    speed_scale: Optional[float] = Field(default=1.0, ge=0.5, le=2.0)
    pitch_scale: Optional[float] = Field(default=0.0, ge=-0.15, le=0.15)
    intonation_scale: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    volume_scale: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    sample_text: Optional[str] = Field(default=DEFAULT_VOICE_SAMPLE_TEXT, max_length=255)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    status: Optional[str] = Field(default="ACTIVE")


class VoiceUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    character_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    speaker_id: Optional[int] = Field(default=None, ge=0)
    style_name: Optional[str] = Field(default=None, max_length=50)
    gender: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None, max_length=500)
    speed_scale: Optional[float] = Field(default=None, ge=0.5, le=2.0)
    pitch_scale: Optional[float] = Field(default=None, ge=-0.15, le=0.15)
    intonation_scale: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    volume_scale: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    sample_text: Optional[str] = Field(default=None, max_length=255)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    status: Optional[str] = Field(default=None)


class SynthesisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500, description="Japanese text to synthesize")
    speaker_id: Optional[int] = Field(default=None, ge=0)
    speed_scale: Optional[float] = Field(default=None, ge=0.5, le=2.0)
    pitch_scale: Optional[float] = Field(default=None, ge=-0.15, le=0.15)
    intonation_scale: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    volume_scale: Optional[float] = Field(default=None, ge=0.0, le=2.0)
