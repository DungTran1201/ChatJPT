"""Resource telemetry & quota API schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class QuotaStatusData(BaseModel):
    user_id: str
    daily_token_limit: int
    daily_tokens_used: int
    percent_used: float
    warning_80: bool
    reset_at: Optional[str] = None


class ResourceHistoryData(BaseModel):
    items: List[Dict[str, Any]]
    count: int
    limit: int
    offset: int
