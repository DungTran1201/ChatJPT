"""Base domain model primitives for v1 entities."""

from typing import Any, Mapping, Type, TypeVar
from pydantic import BaseModel, ConfigDict

TModel = TypeVar("TModel", bound="DomainModel")


class DomainModel(BaseModel):
    """Base entity model supporting SQLite dict/row hydration."""

    model_config = ConfigDict(from_attributes=True, extra="ignore")

    @classmethod
    def from_row(cls: Type[TModel], row: Mapping[str, Any]) -> TModel:
        return cls.model_validate(dict(row))
