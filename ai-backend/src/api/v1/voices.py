import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query, Response

from src.core.security import get_optional_current_user
from src.db import query_one
from src.models.v1.voice import DEFAULT_VOICE_SPEAKER_ID
from src.schemas.v1.voices import (
    VoiceSummaryResponse,
    VoiceListResponse,
    VoiceEngineStatusResponse,
    VoiceCreateRequest,
    VoiceUpdateRequest,
    SynthesisRequest,
)
from src.services.voicevox_service import voicevox_service

logger = logging.getLogger("voices_api")

voices_router = APIRouter(prefix="/voices", tags=["Voice Management & VoiceVox TTS"])

# ==============================================================================
# 1. CONTROLLER ENDPOINTS
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
    speaker_id = req.speaker_id if req.speaker_id is not None else DEFAULT_VOICE_SPEAKER_ID
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
        # Check if id is a sensei_id (system_prompts.id)
        sensei = query_one("SELECT voice_id FROM system_prompts WHERE id = ?", (id,))
        if sensei and sensei.get("voice_id"):
            voice = voicevox_service.get_voice(sensei["voice_id"])

    if not voice:
        # Fallback to default speaker 8 (Kasukabe Tsumugi) if voice not found
        speaker_id = DEFAULT_VOICE_SPEAKER_ID
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

