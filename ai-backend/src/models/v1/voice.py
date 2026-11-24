"""VoiceVox Voice domain entity (voices table)."""

from enum import Enum
from typing import Optional
from src.models.v1.base import DomainModel

DEFAULT_VOICE_SPEAKER_ID = 8
DEFAULT_VOICE_SAMPLE_TEXT = "こんにちは！日本語の勉強を一緒に頑張りましょう。"


class VoiceGender(str, Enum):
    FEMALE = "female"
    MALE = "male"
    OTHER = "other"


class VoiceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class VoiceEntity(DomainModel):
    """Domain entity mirroring the voices table."""

    id: str
    name: str
    character_name: str
    speaker_id: int
    style_name: Optional[str] = "Normal"
    gender: str = VoiceGender.FEMALE.value
    description: Optional[str] = None
    speed_scale: float = 1.0
    pitch_scale: float = 0.0
    intonation_scale: float = 1.0
    volume_scale: float = 1.0
    sample_text: Optional[str] = DEFAULT_VOICE_SAMPLE_TEXT
    avatar_url: Optional[str] = None
    status: str = VoiceStatus.ACTIVE.value
    is_system_preset: bool = False
    user_id: Optional[str] = "system"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
