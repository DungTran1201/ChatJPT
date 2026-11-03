import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Query, Response
from pydantic import BaseModel, Field

from src.core.security import get_optional_current_user
from src.services.voicevox_service import voicevox_service

logger = logging.getLogger("voices_api")

voices_router = APIRouter(prefix="/voices", tags=["Voice Management & VoiceVox TTS"])

# ==============================================================================
# 1. PYDANTIC SCHEMAS
# ==============================================================================

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
    sample_text: Optional[str] = Field(default="こんにちは！日本語の勉強を一緒に頑張りましょう。", max_length=255)
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

# ==============================================================================
# 2. CONTROLLER ENDPOINTS
# ==============================================================================

@voices_router.get("/status", response_model=VoiceEngineStatusResponse)
async def get_engine_status():
    """Returns local VoiceVox daemon connectivity status, version, and latency (OP-049, FR-071)."""
    return voicevox_service.get_engine_status()

@voices_router.get("", response_model=VoiceListResponse)
async def list_voices(
    gender: Optional[str] = Query(None, description="Filter by gender (female, male, other)"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, INACTIVE)"),
    q: Optional[str] = Query(None, description="Search keyword in name or character_name"),
    current_user: dict = Depends(get_optional_current_user)
):
    """Lists all available VoiceVox character voices (OP-047, FR-069)."""
    items = voicevox_service.list_voices(gender=gender, status=status, search=q)
    return VoiceListResponse(total=len(items), items=items)

@voices_router.get("/{id}", response_model=VoiceSummaryResponse)
async def get_voice(
    id: str,
    current_user: dict = Depends(get_optional_current_user)
):
    """Retrieves full voice configuration and acoustic parameters (OP-048, FR-070)."""
    voice = voicevox_service.get_voice(id)
    if not voice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy giọng đọc với mã '{id}'."
        )
    return voice

@voices_router.post("", response_model=VoiceSummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_voice(
    req: VoiceCreateRequest,
    current_user: dict = Depends(get_optional_current_user)
):
    """Creates a new custom VoiceVox character voice profile (OP-050, FR-070)."""
    user_id = current_user.get("id", "system")
    created = voicevox_service.create_voice(req.model_dump(), user_id=user_id)
    return created

@voices_router.put("/{id}", response_model=VoiceSummaryResponse)
async def update_voice(
    id: str,
    req: VoiceUpdateRequest,
    current_user: dict = Depends(get_optional_current_user)
):
    """Updates acoustic tuning parameters for a voice profile (OP-051, FR-070, BR-040)."""
    existing = voicevox_service.get_voice(id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy giọng đọc với mã '{id}'."
        )

    updated = voicevox_service.update_voice(id, req.model_dump(exclude_unset=True))
    return updated

@voices_router.delete("/{id}")
async def delete_voice(
    id: str,
    current_user: dict = Depends(get_optional_current_user)
):
    """Deletes a custom voice profile. System presets cannot be deleted (OP-052)."""
    existing = voicevox_service.get_voice(id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy giọng đọc với mã '{id}'."
        )
    if existing.get("is_system_preset"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể xóa giọng mẫu mặc định của hệ thống."
        )

    success = voicevox_service.delete_voice(id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể xóa hồ sơ giọng.")
    return {"message": f"Đã xóa thành công giọng đọc '{id}'."}

@voices_router.post("/synthesize")
async def synthesize_adhoc(req: SynthesisRequest):
    """Directly synthesizes Japanese text to PCM WAV audio stream (OP-053, FR-071, FR-073)."""
    speaker_id = req.speaker_id if req.speaker_id is not None else 8
    speed = req.speed_scale if req.speed_scale is not None else 1.0
    pitch = req.pitch_scale if req.pitch_scale is not None else 0.0
    intonation = req.intonation_scale if req.intonation_scale is not None else 1.0
    volume = req.volume_scale if req.volume_scale is not None else 1.0

    wav_bytes = voicevox_service.synthesize(
        text=req.text,
        speaker_id=speaker_id,
        speed_scale=speed,
        pitch_scale=pitch,
        intonation_scale=intonation,
        volume_scale=volume
    )
    return Response(content=wav_bytes, media_type="audio/wav")

@voices_router.post("/{id}/synthesize")
async def synthesize_by_voice_id(id: str, req: SynthesisRequest):
    """Synthesizes Japanese text using a stored voice profile's acoustic parameters (OP-054, FR-071, FR-073)."""
    voice = voicevox_service.get_voice(id)
    if not voice:
        # Fallback to default speaker 8 (Kasukabe Tsumugi) if voice not found
        speaker_id = 8
        speed = 1.0
        pitch = 0.0
        intonation = 1.0
        volume = 1.0
    else:
        speaker_id = voice["speaker_id"]
        speed = req.speed_scale if req.speed_scale is not None else voice.get("speed_scale", 1.0)
        pitch = req.pitch_scale if req.pitch_scale is not None else voice.get("pitch_scale", 0.0)
        intonation = req.intonation_scale if req.intonation_scale is not None else voice.get("intonation_scale", 1.0)
        volume = req.volume_scale if req.volume_scale is not None else voice.get("volume_scale", 1.0)

    wav_bytes = voicevox_service.synthesize(
        text=req.text,
        speaker_id=speaker_id,
        speed_scale=speed,
        pitch_scale=pitch,
        intonation_scale=intonation,
        volume_scale=volume
    )
    return Response(content=wav_bytes, media_type="audio/wav")

