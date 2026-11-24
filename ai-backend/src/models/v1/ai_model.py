"""AI Model catalog domain entity (models table)."""

from enum import Enum
from typing import Any, Dict, Mapping, Optional
from src.models.v1.base import DomainModel

VALID_LLM_PROVIDERS = ("google", "anthropic", "openai", "groq", "ollama")


class ModelStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"
    DEGRADED = "DEGRADED"


class AIModelEntity(DomainModel):
    """Domain entity mirroring the models catalog table."""

    id: str
    name: str
    provider: str
    status: str = ModelStatus.INACTIVE.value
    is_default: bool = False
    context_window: int = 128000
    max_tokens: int = 4096
    supports_streaming: bool = True
    has_api_key: bool = False
    latency_ms: Optional[float] = None
    last_checked_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_model_row(
        cls,
        row: Mapping[str, Any],
        *,
        has_api_key: bool,
    ) -> "AIModelEntity":
        raw_stream = row.get("supports_streaming")
        return cls(
            id=row["id"],
            name=row["name"],
            provider=row["provider"],
            status=row.get("status") or ModelStatus.INACTIVE.value,
            is_default=bool(row.get("is_default", 0)),
            context_window=row.get("context_window") if row.get("context_window") is not None else 128000,
            max_tokens=row.get("max_tokens") if row.get("max_tokens") is not None else 4096,
            supports_streaming=True if raw_stream is None else bool(raw_stream),
            has_api_key=has_api_key,
            latency_ms=row.get("latency_ms"),
            last_checked_at=str(row["last_checked_at"]) if row.get("last_checked_at") is not None else None,
            created_at=str(row["created_at"]) if row.get("created_at") is not None else None,
            updated_at=str(row["updated_at"]) if row.get("updated_at") is not None else None,
        )

    def to_api_dict(self) -> Dict[str, Any]:
        return self.model_dump()
