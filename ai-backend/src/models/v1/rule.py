"""Pedagogical Rules domain entity (rules table)."""

from enum import Enum
from typing import List, Optional
from pydantic import Field
from src.models.v1.base import DomainModel

VALID_ACTIVATION_MODES = {"always_on", "model_decision", "glob", "manual"}
VALID_RULE_STATUSES = ("active", "inactive")


class RuleScope(str, Enum):
    SYSTEM = "system"
    USER = "user"


class RuleActivationMode(str, Enum):
    ALWAYS_ON = "always_on"
    MODEL_DECISION = "model_decision"
    GLOB = "glob"
    MANUAL = "manual"


class RuleStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class RuleEntity(DomainModel):
    """Domain entity mirroring the rules table."""

    id: str
    user_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    content: str
    scope: str = RuleScope.USER.value
    activation_mode: str = RuleActivationMode.ALWAYS_ON.value
    glob_patterns: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    priority: int = 50
    status: str = RuleStatus.ACTIVE.value
    version: int = 1
    created_at: str = ""
    updated_at: str = ""
    deleted_at: Optional[str] = None
