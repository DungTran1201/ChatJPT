"""Thin HTTP router for Rules Management (/api/v1/rules)."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from src.core.security import get_optional_current_user
from src.dependencies import get_rule_service, get_text_import_service
from src.schemas.v1.rules import (
    PaginatedRuleResponse,
    RuleCreateRequest,
    RuleResponse,
    RuleStatusUpdateRequest,
    RuleUpdateRequest,
)
from src.schemas.v1.text_import import TextFileImportRequest
from src.services.rule_service import RuleService
from src.services.text_import_service import MAX_FILE_SIZE_BYTES, TextImportService

rules_router = APIRouter(prefix="/rules", tags=["Rules Management"])


@rules_router.get("", response_model=PaginatedRuleResponse, summary="List rules with search, filters, and pagination")
async def list_rules_endpoint(
    search: Optional[str] = Query(None),
    scope: Optional[str] = Query("all"),
    activation_mode: Optional[str] = Query(None),
    status_filter: Optional[str] = Query("active", alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("updated_at"),
    sort_order: str = Query("desc"),
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    rule_service: RuleService = Depends(get_rule_service),
):
    return rule_service.list_rules_instance(
        user_id=current_user.get("id", "guest_user"),
        search=search,
        scope=scope,
        activation_mode=activation_mode,
        status_filter=status_filter,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@rules_router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED, summary="Create a new rule")
async def create_rule_endpoint(
    req: RuleCreateRequest,
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    rule_service: RuleService = Depends(get_rule_service),
):
    return rule_service.create_rule_instance(user_id=current_user.get("id", "guest_user"), req=req)


@rules_router.post("/import-file", response_model=RuleResponse, status_code=status.HTTP_201_CREATED, summary="Import rule from a text file")
async def import_rule_file_endpoint(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    import_service: TextImportService = Depends(get_text_import_service),
):
    user_id = current_user.get("id", "guest_user")
    filename = file.filename or "untitled.txt"
    content_bytes = await file.read(MAX_FILE_SIZE_BYTES + 1)
    text = import_service.validate_and_decode_bytes(filename, content_bytes)
    return import_service.import_rule_instance(user_id=user_id, filename=filename, content=text)


@rules_router.post("/import-text", response_model=RuleResponse, status_code=status.HTTP_201_CREATED, summary="Import rule from verified text payload")
async def import_rule_text_endpoint(
    req: TextFileImportRequest,
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    import_service: TextImportService = Depends(get_text_import_service),
):
    user_id = current_user.get("id", "guest_user")
    text = import_service.validate_and_decode_bytes(req.filename, req.content.encode("utf-8"))
    return import_service.import_rule_instance(
        user_id=user_id,
        filename=req.filename,
        content=text,
        override_name=req.override_name or req.name,
        override_desc=req.override_description or req.description,
        activation_mode=req.activation_mode,
        glob_patterns=req.glob_patterns,
        tags=req.tags,
        priority=req.priority,
    )


@rules_router.get("/{rule_id}", response_model=RuleResponse, summary="Get rule details by ID")
async def get_rule_endpoint(
    rule_id: str,
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    rule_service: RuleService = Depends(get_rule_service),
):
    return rule_service.get_rule_instance(user_id=current_user.get("id", "guest_user"), rule_id=rule_id)


@rules_router.put("/{rule_id}", response_model=RuleResponse, summary="Update an existing rule")
async def update_rule_endpoint(
    rule_id: str,
    req: RuleUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    rule_service: RuleService = Depends(get_rule_service),
):
    return rule_service.update_rule_instance(user_id=current_user.get("id", "guest_user"), rule_id=rule_id, req=req)


@rules_router.patch("/{rule_id}/status", response_model=RuleResponse, summary="Quick toggle rule active status")
async def update_rule_status_endpoint(
    rule_id: str,
    req: RuleStatusUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    rule_service: RuleService = Depends(get_rule_service),
):
    return rule_service.update_status_instance(
        user_id=current_user.get("id", "guest_user"),
        rule_id=rule_id,
        new_status=req.status,
    )


@rules_router.post("/{rule_id}/clone", response_model=RuleResponse, status_code=status.HTTP_201_CREATED, summary="Clone a rule to user library")
async def clone_rule_endpoint(
    rule_id: str,
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    rule_service: RuleService = Depends(get_rule_service),
):
    return rule_service.clone_rule_instance(user_id=current_user.get("id", "guest_user"), rule_id=rule_id)


@rules_router.delete("/{rule_id}", summary="Soft delete a rule with reference guard")
async def delete_rule_endpoint(
    rule_id: str,
    force: bool = Query(False),
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    rule_service: RuleService = Depends(get_rule_service),
):
    return rule_service.delete_rule_instance(
        user_id=current_user.get("id", "guest_user"),
        rule_id=rule_id,
        force=force,
    )
