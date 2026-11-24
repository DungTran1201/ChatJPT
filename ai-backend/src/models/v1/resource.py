"""Resource telemetry & token quota domain entities (user_quotas, api_metric_logs tables)."""

from typing import Any, Dict, Mapping, Optional
from src.models.v1.base import DomainModel


class UserQuotaEntity(DomainModel):
    """Domain entity mirroring the user_quotas table."""

    user_id: str
    daily_token_limit: int = 100000
    daily_tokens_used: int = 0
    reset_at: Optional[str] = None

    @property
    def percent_used(self) -> float:
        return round((self.daily_tokens_used / max(self.daily_token_limit, 1)) * 100, 1)

    @property
    def warning_80(self) -> bool:
        return self.percent_used >= 80.0

    @classmethod
    def from_quota_row(cls, user_id: str, row: Mapping[str, Any]) -> "UserQuotaEntity":
        raw_limit = row.get("daily_token_limit")
        raw_used = row.get("daily_tokens_used")
        return cls(
            user_id=user_id,
            daily_token_limit=100000 if raw_limit is None else raw_limit,
            daily_tokens_used=0 if raw_used is None else raw_used,
            reset_at=str(row["reset_at"]) if row.get("reset_at") is not None else None,
        )

    def to_status_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "daily_token_limit": self.daily_token_limit,
            "daily_tokens_used": self.daily_tokens_used,
            "percent_used": self.percent_used,
            "warning_80": self.warning_80,
            "reset_at": self.reset_at,
        }


class ApiMetricLogEntity(DomainModel):
    """Domain entity mirroring the api_metric_logs table."""

    id: str
    endpoint: str
    method: str
    status_code: int
    latency_ms: float
    ttft_ms: Optional[float] = None
    user_id: Optional[str] = None
    model_name: Optional[str] = None
    provider: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    error_code: Optional[str] = None
    created_at: Optional[str] = None
