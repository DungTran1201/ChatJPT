"""Thin HTTP router for Sensei Guidance & System Prompts (/api/v1/system-prompts)."""

from typing import Optional
from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from src.core.security import get_optional_current_user
from src.dependencies import get_prompt_service, get_text_import_service
from src.schemas.v1.prompts import (
    SystemPromptCreateRequest,
    SystemPromptDetailResponse,
    SystemPromptListResponse,
    SystemPromptUpdateRequest,
)
from src.schemas.v1.text_import import TextFileImportRequest
from src.services.prompt_service import PromptService
from src.services.text_import_service import MAX_FILE_SIZE_BYTES, TextImportService

prompts_router = APIRouter(prefix="/system-prompts", tags=["Sensei Guidance & System Prompts"])


@prompts_router.get("", response_model=SystemPromptListResponse)
async def list_system_prompts(
    q: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    sort: str = Query("level_asc"),
    current_user: dict = Depends(get_optional_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    return prompt_service.list_prompts(
        user_id=current_user.get("id", "guest_user"),
        q=q,
        level=level,
        sort=sort,
    )


@prompts_router.post("", response_model=SystemPromptDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_system_prompt(
    payload: SystemPromptCreateRequest,
    current_user: dict = Depends(get_optional_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    return prompt_service.create_prompt(current_user.get("id", "guest_user"), payload)


# Keep static import paths BEFORE /{id} to avoid route shadowing
@prompts_router.post("/import-file", response_model=SystemPromptDetailResponse, status_code=status.HTTP_201_CREATED)
async def import_system_prompt_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_optional_current_user),
    import_service: TextImportService = Depends(get_text_import_service),
):
    user_id = current_user.get("id", "guest_user")
    filename = file.filename or "untitled.txt"
    content_bytes = await file.read(MAX_FILE_SIZE_BYTES + 1)
    text = import_service.validate_and_decode_bytes(filename, content_bytes)
    return import_service.import_prompt_instance(user_id=user_id, filename=filename, content=text)


@prompts_router.post("/import-text", response_model=SystemPromptDetailResponse, status_code=status.HTTP_201_CREATED)
async def import_system_prompt_text(
    req: TextFileImportRequest,
    current_user: dict = Depends(get_optional_current_user),
    import_service: TextImportService = Depends(get_text_import_service),
):
    user_id = current_user.get("id", "guest_user")
    text = import_service.validate_and_decode_bytes(req.filename, req.content.encode("utf-8"))
    return import_service.import_prompt_instance(
        user_id=user_id,
        filename=req.filename,
        content=text,
        override_name=req.override_name or req.name,
        override_desc=req.override_description or req.description,
    )


@prompts_router.get("/{id}", response_model=SystemPromptDetailResponse)
async def get_system_prompt_detail(
    id: str,
    current_user: dict = Depends(get_optional_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    return prompt_service.get_detail(id, current_user.get("id", "guest_user"))


@prompts_router.get("/{id}/attachments")
async def list_system_prompt_attachments(
    id: str,
    current_user: dict = Depends(get_optional_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    return prompt_service.list_prompt_attachments(id, current_user.get("id", "guest_user"))


@prompts_router.put("/{id}", response_model=SystemPromptDetailResponse)
async def update_system_prompt(
    id: str,
    payload: SystemPromptUpdateRequest,
    current_user: dict = Depends(get_optional_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    return prompt_service.update_prompt(id, current_user.get("id", "guest_user"), payload)


@prompts_router.delete("/{id}")
async def delete_system_prompt(
    id: str,
    current_user: dict = Depends(get_optional_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    return prompt_service.delete_prompt(id, current_user.get("id", "guest_user"))


@prompts_router.post("/{id}/clone", response_model=SystemPromptDetailResponse, status_code=status.HTTP_201_CREATED)
async def clone_system_prompt(
    id: str,
    current_user: dict = Depends(get_optional_current_user),
    prompt_service: PromptService = Depends(get_prompt_service),
):
    return prompt_service.clone_prompt(id, current_user.get("id", "guest_user"))
