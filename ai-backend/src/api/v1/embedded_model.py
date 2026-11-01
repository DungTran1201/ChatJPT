from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from src.services.hardware_service import HardwareInspectionService
from src.services.embedded_model_service import EmbeddedModelService
from src.services.semantic_cache_service import SemanticCacheService

embedded_router = APIRouter(prefix="", tags=["Embedded Model & Semantic Cache"])

class DownloadRequest(BaseModel):
    model_id: Optional[str] = "qwen2.5-0.5b-embedded"

class LearnRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    response: str = Field(..., min_length=1)
    category: Optional[str] = "learned_chat"

# OP-042: Inspect host hardware specs and eligibility
@embedded_router.get("/models/embedded/hardware-check")
async def get_hardware_check():
    """Inspects host machine resources and evaluates embedded model download eligibility."""
    return HardwareInspectionService.evaluate_eligibility(
        min_ram_gb=4.0,
        min_avail_ram_gb=1.5,
        min_disk_gb=1.5,
        min_cpu_cores=2
    )

# OP-043: Download embedded model (Enforces hardware gate)
@embedded_router.post("/models/embedded/download")
async def download_embedded_model(payload: Optional[DownloadRequest] = None):
    """Enforces hardware gate check and downloads embedded model weights directly into project."""
    model_id = payload.model_id if payload and payload.model_id else "qwen2.5-0.5b-embedded"
    try:
        res = EmbeddedModelService.start_download(model_id=model_id)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failure: {str(e)}")

# OP-044: Embedded model status & progress
@embedded_router.get("/models/embedded/status")
async def get_embedded_model_status(model_id: Optional[str] = "qwen2.5-0.5b-embedded"):
    """Returns runtime status, download progress, and file presence of embedded model."""
    target_id = model_id or "qwen2.5-0.5b-embedded"
    return EmbeddedModelService.get_model_record(target_id)

# OP-045: Delete embedded model
@embedded_router.delete("/models/embedded")
async def delete_embedded_model(model_id: Optional[str] = "qwen2.5-0.5b-embedded"):
    """Removes embedded model weights to reclaim disk space."""
    target_id = model_id or "qwen2.5-0.5b-embedded"
    return EmbeddedModelService.delete_model(target_id)

# OP-046: Semantic cache stats
@embedded_router.get("/semantic-cache/stats")
async def get_semantic_cache_stats():
    """Returns total entries (10,000+), hit count, and category breakdown in Semantic Cache."""
    return SemanticCacheService.get_stats()

# Auto-learn endpoint (for manual or frontend test invocations)
@embedded_router.post("/semantic-cache/learn")
async def learn_interaction_endpoint(payload: LearnRequest):
    """Stores a Q&A interaction into semantic cache with strict deduplication."""
    return SemanticCacheService.learn_interaction(
        prompt_raw=payload.prompt,
        response_text=payload.response,
        category=payload.category or "learned_chat"
    )
