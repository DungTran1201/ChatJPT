"""Exam Management & Reference Materials API router — thin HTTP controller."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse, RedirectResponse

from src.core.security import get_optional_current_user
from src.dependencies import get_exam_service
from src.schemas.v1.exams import (
    ExamCreateRequest,
    ExamDetailResponse,
    ExamListResponse,
    ExamSubmissionRequest,
    ExamSubmissionResult,
    ExamSummaryResponse,
    ExamUpdateRequest,
    ReferenceMaterialCreateRequest,
    ReferenceMaterialItem,
    ReferenceMaterialListResponse,
)
from src.services.attachment_service import build_content_disposition
from src.services.exam_service import ExamService

exams_router = APIRouter(prefix="/exams", tags=["Exam Management & Reference Materials"])


def _serve_material_response(service: ExamService, material_id: str, *, inline: bool):
    kind, target = service.resolve_material_asset(material_id)
    if kind == "redirect":
        return RedirectResponse(url=target)

    disposition = "inline" if inline else "attachment"
    media_type = "application/pdf" if inline else "application/octet-stream"
    return FileResponse(
        path=str(target),
        media_type=media_type,
        filename=target.name,
        headers={"Content-Disposition": build_content_disposition(disposition, target.name)},
    )


@exams_router.get("/materials", response_model=ReferenceMaterialListResponse)
async def list_reference_materials(
    category: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    service: ExamService = Depends(get_exam_service),
):
    return service.list_materials(category=category, level=level, search=search)


@exams_router.get("/materials/view/{material_id}")
async def view_reference_material(
    material_id: str,
    service: ExamService = Depends(get_exam_service),
):
    return _serve_material_response(service, material_id, inline=True)


@exams_router.get("/materials/download/{material_id}")
async def download_reference_material(
    material_id: str,
    service: ExamService = Depends(get_exam_service),
):
    return _serve_material_response(service, material_id, inline=False)


@exams_router.get("/rag/search")
async def search_rag_knowledge(
    query: str = Query("", description="Từ khóa ngữ pháp, từ vựng hoặc dạng bài cần tra cứu"),
    level: Optional[str] = Query(None, description="Cấp độ JLPT N5..N1 hoặc KAIWA"),
    limit: int = Query(6, ge=1, le=20),
    service: ExamService = Depends(get_exam_service),
):
    return service.search_rag(query=query, level=level, limit=limit)


@exams_router.post("/materials", response_model=ReferenceMaterialItem, status_code=status.HTTP_201_CREATED)
async def create_reference_material(
    payload: ReferenceMaterialCreateRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
    service: ExamService = Depends(get_exam_service),
):
    return service.create_material(payload, current_user=current_user)


@exams_router.delete("/materials/{material_id}")
async def delete_reference_material(
    material_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
    service: ExamService = Depends(get_exam_service),
):
    return service.delete_material(material_id, current_user=current_user)


@exams_router.get("", response_model=ExamListResponse)
async def list_exams(
    level: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    service: ExamService = Depends(get_exam_service),
):
    return service.list_exams(level=level, category=category, search=search)


@exams_router.get("/{exam_id}", response_model=ExamDetailResponse)
async def get_exam_detail(
    exam_id: str,
    include_answers: bool = Query(False),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
    service: ExamService = Depends(get_exam_service),
):
    return service.get_exam_detail(exam_id, include_answers=include_answers, current_user=current_user)


@exams_router.post("", response_model=ExamSummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(
    payload: ExamCreateRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
    service: ExamService = Depends(get_exam_service),
):
    return service.create_exam(payload, current_user=current_user)


@exams_router.put("/{exam_id}", response_model=ExamSummaryResponse)
async def update_exam(
    exam_id: str,
    payload: ExamUpdateRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
    service: ExamService = Depends(get_exam_service),
):
    return service.update_exam(exam_id, payload, current_user=current_user)


@exams_router.delete("/{exam_id}")
async def delete_exam(
    exam_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
    service: ExamService = Depends(get_exam_service),
):
    return service.delete_exam(exam_id, current_user=current_user)


@exams_router.post("/{exam_id}/submit", response_model=ExamSubmissionResult)
async def submit_exam(
    exam_id: str,
    payload: ExamSubmissionRequest,
    service: ExamService = Depends(get_exam_service),
):
    return service.submit_exam(exam_id, payload)
