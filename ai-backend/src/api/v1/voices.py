"""Voice Management & VoiceVox TTS API router — thin HTTP controller."""

import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status

from src.core.exceptions import NotFoundError
from src.core.security import get_optional_current_user
from src.dependencies import get_voice_service
from src.models.v1.voice import DEFAULT_VOICE_SPEAKER_ID
from src.schemas.v1.voices import (
    SynthesisRequest,
    VoiceCreateRequest,
    VoiceEngineStatusResponse,
    VoiceListResponse,
    VoiceSummaryResponse,
    VoiceUpdateRequest,
)
from src.services.voicevox_service import VoicevoxService

voices_router = APIRouter(prefix="/voices", tags=["Voice Management & VoiceVox TTS"])


@voices_router.get("/status", response_model=VoiceEngineStatusResponse)
async def get_engine_status(service: VoicevoxService = Depends(get_voice_service)):
    """OP-049: Returns local VoiceVox engine connectivity status, version, and latency."""
    return await asyncio.to_thread(service.get_engine_status)


@voices_router.get("", response_model=VoiceListResponse)
async def list_voices(
    gender: Optional[str] = Query(None, description="Filter by gender (female, male, other)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (ACTIVE, INACTIVE)"),
    q: Optional[str] = Query(None, description="Search keyword in name or character_name"),
    _current_user: dict = Depends(get_optional_current_user),
    service: VoicevoxService = Depends(get_voice_service),
):
    """OP-047: Lists all available VoiceVox character voices."""
    items = service.list_voices(gender=gender, status=status_filter, search=q)
    return VoiceListResponse(total=len(items), items=items)


@voices_router.get("/{id}", response_model=VoiceSummaryResponse)
async def get_voice(
    id: str,
    _current_user: dict = Depends(get_optional_current_user),
    service: VoicevoxService = Depends(get_voice_service),
):
    """OP-048: Retrieves full voice configuration and acoustic parameters."""
    return service.get_voice_or_404(id)


@voices_router.post("", response_model=VoiceSummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_voice(
    req: VoiceCreateRequest,
    current_user: dict = Depends(get_optional_current_user),
    service: VoicevoxService = Depends(get_voice_service),
):
    """OP-050: Creates a new custom VoiceVox character voice profile."""
    return service.create_voice(req.model_dump(), user_id=current_user.get("id", "system"))


@voices_router.put("/{id}", response_model=VoiceSummaryResponse)
async def update_voice(
    id: str,
    req: VoiceUpdateRequest,
    current_user: dict = Depends(get_optional_current_user),
    service: VoicevoxService = Depends(get_voice_service),
):
    """OP-051: Updates acoustic tuning parameters for a voice profile."""
    updated = service.update_voice(id, req.model_dump(exclude_unset=True), current_user=current_user)
    if not updated:
        raise NotFoundError(f"Không tìm thấy giọng đọc với mã '{id}'.")
    return updated


@voices_router.delete("/{id}")
async def delete_voice(
    id: str,
    current_user: dict = Depends(get_optional_current_user),
    service: VoicevoxService = Depends(get_voice_service),
):
    """OP-052: Deletes a custom voice profile. System presets cannot be deleted."""
    service.delete_voice(id, current_user=current_user)
    return {"message": f"Đã xóa thành công giọng đọc '{id}'."}


@voices_router.post("/synthesize")
async def synthesize_adhoc(
    req: SynthesisRequest,
    service: VoicevoxService = Depends(get_voice_service),
):
    """OP-053: Directly synthesizes Japanese text to PCM WAV audio stream."""
    wav_bytes = await asyncio.to_thread(
        service.synthesize,
        text=req.text,
        speaker_id=req.speaker_id if req.speaker_id is not None else DEFAULT_VOICE_SPEAKER_ID,
        speed_scale=req.speed_scale if req.speed_scale is not None else 1.0,
        pitch_scale=req.pitch_scale if req.pitch_scale is not None else 0.0,
        intonation_scale=req.intonation_scale if req.intonation_scale is not None else 1.0,
        volume_scale=req.volume_scale if req.volume_scale is not None else 1.0,
    )
    return Response(content=wav_bytes, media_type="audio/wav")


@voices_router.post("/{id}/synthesize")
async def synthesize_by_voice_id(
    id: str,
    req: SynthesisRequest,
    service: VoicevoxService = Depends(get_voice_service),
):
    """OP-054: Synthesizes Japanese text using a stored voice or Sensei profile."""
    wav_bytes = await asyncio.to_thread(
        service.synthesize_for_profile,
        id,
        text=req.text,
        speed_scale=req.speed_scale,
        pitch_scale=req.pitch_scale,
        intonation_scale=req.intonation_scale,
        volume_scale=req.volume_scale,
    )
    return Response(content=wav_bytes, media_type="audio/wav")
