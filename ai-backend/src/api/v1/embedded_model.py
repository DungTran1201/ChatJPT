"""Embedded Model & Semantic Cache API router — thin HTTP controller."""

import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from src.dependencies import get_embedded_model_service, get_semantic_cache_service
from src.models.v1.embedded_model import DEFAULT_EMBEDDED_MODEL_ID
from src.schemas.v1.embedded_model import DownloadRequest, LearnRequest
from src.services.embedded_model_service import EmbeddedModelService
from src.services.hardware_service import HardwareInspectionService
from src.services.semantic_cache_service import SemanticCacheService

embedded_router = APIRouter(prefix="", tags=["Embedded Model & Semantic Cache"])


@embedded_router.get("/models/embedded/hardware-check")
async def get_hardware_check():
    """OP-042: Inspects host machine resources and evaluates embedded model eligibility."""
    return HardwareInspectionService.evaluate_eligibility(
        min_ram_gb=4.0,
        min_avail_ram_gb=1.5,
        min_disk_gb=1.5,
        min_cpu_cores=2,
    )


@embedded_router.post("/models/embedded/download")
async def download_embedded_model(
    payload: Optional[DownloadRequest] = None,
    service: EmbeddedModelService = Depends(get_embedded_model_service),
):
    """OP-043: Enforces hardware gate check and downloads embedded model weights."""
    model_id = payload.model_id if payload and payload.model_id else DEFAULT_EMBEDDED_MODEL_ID
    try:
        return await asyncio.to_thread(service.download, model_id)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Download failure: {err}")


@embedded_router.get("/models/embedded/status")
async def get_embedded_model_status(
    model_id: Optional[str] = DEFAULT_EMBEDDED_MODEL_ID,
    service: EmbeddedModelService = Depends(get_embedded_model_service),
):
    """OP-044: Returns runtime status, download progress, and file presence of embedded model."""
    target_id = model_id or DEFAULT_EMBEDDED_MODEL_ID
    try:
        return service.get_record(target_id)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@embedded_router.delete("/models/embedded")
async def delete_embedded_model(
    model_id: Optional[str] = DEFAULT_EMBEDDED_MODEL_ID,
    service: EmbeddedModelService = Depends(get_embedded_model_service),
):
    """OP-045: Removes embedded model weights to reclaim disk space."""
    target_id = model_id or DEFAULT_EMBEDDED_MODEL_ID
    try:
        return service.remove(target_id)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@embedded_router.get("/semantic-cache/stats")
async def get_semantic_cache_stats(
    cache_service: SemanticCacheService = Depends(get_semantic_cache_service),
):
    """OP-046: Returns total entries, hit count, and category breakdown in Semantic Cache."""
    return cache_service.stats()


@embedded_router.post("/semantic-cache/learn")
async def learn_interaction_endpoint(
    payload: LearnRequest,
    cache_service: SemanticCacheService = Depends(get_semantic_cache_service),
):
    """Stores a Q&A interaction into semantic cache with strict deduplication."""
    return cache_service.learn(
        prompt_raw=payload.prompt,
        response_text=payload.response,
        category=payload.category or "learned_chat",
    )
