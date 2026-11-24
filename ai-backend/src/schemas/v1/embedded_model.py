"""Embedded Model & Semantic Cache API schemas."""

from typing import Optional
from pydantic import BaseModel, Field
from src.models.v1.embedded_model import DEFAULT_EMBEDDED_MODEL_ID


class DownloadRequest(BaseModel):
    model_id: Optional[str] = DEFAULT_EMBEDDED_MODEL_ID


class LearnRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    response: str = Field(..., min_length=1)
    category: Optional[str] = "learned_chat"
