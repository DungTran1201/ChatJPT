"""Thin HTTP router for AI Model Catalog Management (/api/v1/models)."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status

from src.core.security import get_current_user
from src.dependencies import get_model_service
from src.schemas.v1.models import (
    CreateModelRequest,
    SetDefaultModelRequest,
    UpdateModelRequest,
)
from src.services.model_service import ModelService

models_router = APIRouter(prefix="/models", tags=["Model Management"])


def _extract_uid(current_user: Any) -> Optional[str]:
    return current_user.get("id") if isinstance(current_user, dict) else None


@models_router.get("", response_model=List[Dict[str, Any]])
@models_router.get("/", response_model=List[Dict[str, Any]])
async def list_models(
    status_filter: Optional[str] = Query("ALL", alias="status"),
    current_user: dict = Depends(get_current_user),
    model_service: ModelService = Depends(get_model_service),
):
    return model_service.list_models(status_filter=status_filter or "ALL", user_id=_extract_uid(current_user))


@models_router.post("", status_code=status.HTTP_201_CREATED)
@models_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_model(
    req: CreateModelRequest,
    current_user: dict = Depends(get_current_user),
    model_service: ModelService = Depends(get_model_service),
):
    return model_service.create_model(req, user_id=_extract_uid(current_user))


@models_router.get("/search")
async def search_models(
    q: Optional[str] = Query(None),
    provider: Optional[str] = Query("ALL"),
    status_filter: Optional[str] = Query("ALL", alias="status"),
    has_api_key: Optional[bool] = Query(None),
    is_default: Optional[bool] = Query(None),
    sort: Optional[str] = Query("name_asc"),
    current_user: dict = Depends(get_current_user),
    model_service: ModelService = Depends(get_model_service),
):
    return model_service.search_models(
        q=q,
        provider=provider,
        status_filter=status_filter,
        has_api_key=has_api_key,
        is_default=is_default,
        sort=sort,
        user_id=_extract_uid(current_user),
    )


@models_router.patch("/default")
async def set_default_model(
    req: SetDefaultModelRequest,
    current_user: dict = Depends(get_current_user),
    model_service: ModelService = Depends(get_model_service),
):
    return model_service.set_default_model(req)


@models_router.get("/{model_id}")
async def get_model_detail(
    model_id: str,
    current_user: dict = Depends(get_current_user),
    model_service: ModelService = Depends(get_model_service),
):
    return model_service.get_model(model_id, user_id=_extract_uid(current_user))


@models_router.put("/{model_id}")
async def update_model(
    model_id: str,
    req: UpdateModelRequest,
    current_user: dict = Depends(get_current_user),
    model_service: ModelService = Depends(get_model_service),
):
    return model_service.update_model(model_id, req, user_id=_extract_uid(current_user))


@models_router.delete("/{model_id}")
async def archive_model(
    model_id: str,
    current_user: dict = Depends(get_current_user),
    model_service: ModelService = Depends(get_model_service),
):
    return model_service.archive_model(model_id)


@models_router.post("/{model_id}/test")
async def test_model_connection(
    model_id: str,
    current_user: dict = Depends(get_current_user),
    model_service: ModelService = Depends(get_model_service),
):
    return await model_service.test_connection(model_id, user_id=_extract_uid(current_user))


@models_router.patch("/{model_id}/activate")
async def activate_model(
    model_id: str,
    current_user: dict = Depends(get_current_user),
    model_service: ModelService = Depends(get_model_service),
):
    return model_service.activate_model(model_id, user_id=_extract_uid(current_user))


@models_router.patch("/{model_id}/deactivate")
async def deactivate_model(
    model_id: str,
    current_user: dict = Depends(get_current_user),
    model_service: ModelService = Depends(get_model_service),
):
    return model_service.deactivate_model(model_id)
