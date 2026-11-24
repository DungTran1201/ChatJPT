"""Embedded Model & Semantic Cache domain entities (embedded_models, semantic_cache tables)."""

from enum import Enum
from typing import Optional
from src.models.v1.base import DomainModel

DEFAULT_EMBEDDED_MODEL_ID = "qwen2.5-0.5b-embedded"


class EmbeddedDownloadStatus(str, Enum):
    NOT_DOWNLOADED = "NOT_DOWNLOADED"
    DOWNLOADING = "DOWNLOADING"
    READY = "READY"
    ERROR = "ERROR"


class EmbeddedModelEntity(DomainModel):
    """Domain entity mirroring the embedded_models table."""

    id: str = DEFAULT_EMBEDDED_MODEL_ID
    name: str
    file_path: str
    file_size_bytes: int = 0
    min_ram_gb: float = 4.0
    min_avail_ram_gb: float = 1.5
    min_disk_gb: float = 1.5
    min_cpu_cores: int = 2
    download_status: str = EmbeddedDownloadStatus.NOT_DOWNLOADED.value
    download_progress: int = 0
    is_active: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SemanticCacheEntry(DomainModel):
    """Domain entity mirroring the semantic_cache table."""

    id: str
    prompt_raw: str
    prompt_normalized: str
    category: str = "general"
    response_text: str
    keywords: Optional[str] = None
    similarity_score: float = 1.0
    hit_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
