"""Health check API schemas."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    model_config = {"extra": "allow"}
    status: str = Field(default="healthy")
    service: Optional[str] = Field(default="ai-backend")
    version: Optional[str] = Field(default="1.0.0")
    details: Optional[Dict[str, Any]] = None
