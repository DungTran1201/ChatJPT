import re
import uuid
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import FileResponse, RedirectResponse

from src.core.security import get_optional_current_user
from src.db import query_one, query_all, execute_commit
from src.models.v1.exam import (
    VALID_EXAM_LEVELS as VALID_LEVELS,
    VALID_MATERIAL_CATEGORIES,
    ExamEntity,
    ExamQuestionEntity,
    ReferenceMaterialEntity,
)
from src.schemas.v1.exams import (
    ExamQuestionSummary,
    ExamSummaryResponse,
    ExamDetailResponse,
    ExamListResponse,
    ExamCreateRequest,
    ExamUpdateRequest,
    ExamSubmissionRequest,
    QuestionResultItem,
    ExamSubmissionResult,
    ReferenceMaterialItem,
    ReferenceMaterialListResponse,
    ReferenceMaterialCreateRequest,
)
from src.services.rag_exam_service import RagExamService

logger = logging.getLogger("exams_api")

exams_router = APIRouter(prefix="/exams", tags=["Exam Management & Reference Materials"])

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
MATERIALS_DIR = DATA_DIR / "reference_materials"

# ==============================================================================
# HELPER: RESOLVE LOCAL MATERIAL FILE
# ==============================================================================

def resolve_material_file(mat_id: str) -> Optional[Path]:
    """Find local physical file on server matching the given material id."""
    manifest_path = DATA_DIR / "download_manifest.json"
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            for lvl, items in manifest.items():
                for item in items:
                    safe_name = item.get("safe_name", "")
                    stem = Path(safe_name).stem
                    candidate_id = f"loc_{lvl.lower()}_{re.sub(r'[^a-zA-Z0-9]', '_', stem)[:28].strip('_').lower()}"
                    if candidate_id == mat_id or mat_id.replace("mat_", "") in candidate_id or candidate_id in mat_id:
                        p = PROJECT_ROOT / item.get("local_path", "")
                        if p.exists() and p.is_file():
                            return p
        except Exception as e:
            logger.warning(f"Error reading manifest: {e}")

    # Fallback search inside MATERIALS_DIR
    if MATERIALS_DIR.exists():
        for p in MATERIALS_DIR.rglob("*.pdf"):
            if mat_id in p.name.lower() or p.stem[:20].lower() in mat_id:
                return p

    return None

# ==============================================================================
# REFERENCE MATERIALS ENDPOINTS (OP-061, OP-062, LOCAL SERVING & RAG)
# ==============================================================================

@exams_router.get("/materials", response_model=ReferenceMaterialListResponse)
async def list_reference_materials(
    category: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """
    List reference materials across JLPT N5..N1, Kaiwa, Tae Kim Grammar, and Dictionaries.
    Prioritizes locally downloaded files for direct in-browser access and offline study.
    """
    sql = "SELECT * FROM reference_materials WHERE 1=1"
    params = []

    if category:
        sql += " AND category = ?"
        params.append(category.upper())

    if level:
        sql += " AND (level = ? OR level = 'ALL')"
        params.append(level.upper())

    if search:
        s_term = f"%{search.strip()}%"
        sql += " AND (title LIKE ? OR description LIKE ? OR tags LIKE ?)"
        params.extend([s_term, s_term, s_term])

    sql += " ORDER BY is_pinned DESC, created_at ASC"
    rows = query_all(sql, tuple(params))

    items = [
        ReferenceMaterialItem.from_entity(
            ReferenceMaterialEntity.from_material_row(
                r,
                default_author="Kho học liệu tiếng Nhật ChatJPT",
                compute_size_display=True,
            )
        )
        for r in rows
    ]

    return ReferenceMaterialListResponse(total=len(items), items=items)

@exams_router.get("/materials/view/{material_id}")
async def view_reference_material(material_id: str):
    """
    Stream the local PDF or document file inline to the browser for in-app reading without leaving the website.
    """
    file_path = resolve_material_file(material_id)
    if not file_path or not file_path.exists():
        # Check database for external link fallback
        row = query_one("SELECT external_url FROM reference_materials WHERE id = ?", (material_id,))
        if row and row.get("external_url") and row["external_url"].startswith("http"):
            return RedirectResponse(url=row["external_url"])
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp tài liệu nội bộ")

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=file_path.name,
        headers={"Content-Disposition": f'inline; filename="{file_path.name}"'}
    )

@exams_router.get("/materials/download/{material_id}")
async def download_reference_material(material_id: str):
    """
    Download the local PDF or document file to user computer.
    """
    file_path = resolve_material_file(material_id)
    if not file_path or not file_path.exists():
        row = query_one("SELECT external_url FROM reference_materials WHERE id = ?", (material_id,))
        if row and row.get("external_url") and row["external_url"].startswith("http"):
            return RedirectResponse(url=row["external_url"])
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp tài liệu để tải về")

    return FileResponse(
        path=str(file_path),
        media_type="application/octet-stream",
        filename=file_path.name,
        headers={"Content-Disposition": f'attachment; filename="{file_path.name}"'}
    )

@exams_router.get("/rag/search")
async def search_rag_knowledge(
    query: str = Query("", description="Từ khóa ngữ pháp, từ vựng hoặc dạng bài cần tra cứu"),
    level: Optional[str] = Query(None, description="Cấp độ JLPT N5..N1 hoặc KAIWA"),
    limit: int = Query(6, ge=1, le=20)
):
    """
    Search pedagogical knowledge base and study guides extracted from local materials.
    """
    results = RagExamService.search_rag(query=query, level=level, limit=limit)
    return {
        "query": query,
        "level": level or "ALL",
        "total": len(results),
        "results": results
    }

@exams_router.post("/materials", response_model=ReferenceMaterialItem, status_code=status.HTTP_201_CREATED)
async def create_reference_material(
    payload: ReferenceMaterialCreateRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """
    Create a new reference material link in the repository.
    """
    mat_id = f"mat_{uuid.uuid4().hex[:12]}"
    user_id = current_user.get("id") if current_user else "user"

    sql = """
        INSERT INTO reference_materials (
            id, title, description, category, level, source_type,
            external_url, author, file_type, tags, is_pinned, is_system_preset, user_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
    """
    execute_commit(sql, (
        mat_id, payload.title, payload.description, payload.category,
        payload.level or "ALL", payload.source_type or "LOCAL_FILE",
        payload.external_url, payload.author, payload.file_type or "pdf",
        payload.tags, 1 if payload.is_pinned else 0, user_id
    ))

    created = query_one("SELECT * FROM reference_materials WHERE id = ?", (mat_id,))
    return ReferenceMaterialItem.from_entity(
        ReferenceMaterialEntity.from_material_row(
            created,
            force_system_preset=False,
            user_id_override=user_id,
        )
    )

@exams_router.delete("/materials/{material_id}")
async def delete_reference_material(
    material_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """
    Delete reference material link. Protects preset materials.
    """
    existing = query_one("SELECT * FROM reference_materials WHERE id = ?", (material_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu tham khảo")

    if existing.get("is_system_preset"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Không thể xóa tài liệu tham khảo hệ thống"
        )

    execute_commit("DELETE FROM reference_materials WHERE id = ?", (material_id,))
    return {"message": "Đã xóa tài liệu tham khảo thành công", "id": material_id}

# ==============================================================================
# EXAMS CATALOG & MANAGEMENT ENDPOINTS (OP-055..OP-059)
# ==============================================================================

@exams_router.get("", response_model=ExamListResponse)
async def list_exams(
    level: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """
    List all exams with level, category, and keyword search filters (OP-055).
    """
    sql = "SELECT * FROM exams WHERE status != 'ARCHIVED'"
    params = []

    if level:
        sql += " AND level = ?"
        params.append(level.upper())

    if category:
        sql += " AND category = ?"
        params.append(category.upper())

    if search:
        s_term = f"%{search.strip()}%"
        sql += " AND (title LIKE ? OR description LIKE ?)"
        params.extend([s_term, s_term])

    sql += " ORDER BY CASE level WHEN 'N5' THEN 1 WHEN 'N4' THEN 2 WHEN 'N3' THEN 3 WHEN 'N2' THEN 4 WHEN 'N1' THEN 5 ELSE 6 END ASC, created_at ASC"
    rows = query_all(sql, tuple(params))

    # Calculate actual questions count for each exam
    items = []
    for r in rows:
        q_count_row = query_one("SELECT COUNT(*) as count FROM exam_questions WHERE exam_id = ?", (r["id"],))
        actual_q_count = q_count_row["count"] if q_count_row else r["total_questions"]
        items.append(
            ExamSummaryResponse.from_entity(
                ExamEntity.from_exam_row(r, total_questions_override=actual_q_count, default_is_preset=1)
            )
        )

    return ExamListResponse(total=len(items), items=items)

@exams_router.get("/{exam_id}", response_model=ExamDetailResponse)
async def get_exam_detail(
    exam_id: str,
    include_answers: bool = Query(False)
):
    """
    Retrieve full exam metadata and question list for interactive test taking (OP-056).
    Omits correct_option and explanation unless explicitly authorized to prevent cheating (CTRL-EXAM-03).
    """
    exam = query_one("SELECT * FROM exams WHERE id = ?", (exam_id,))
    if not exam:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề thi yêu cầu")

    questions_raw = query_all(
        "SELECT * FROM exam_questions WHERE exam_id = ? ORDER BY question_number ASC",
        (exam_id,)
    )

    question_entities = [
        ExamQuestionEntity.from_question_row(q, include_answers=include_answers)
        for q in questions_raw
    ]
    exam_entity = ExamEntity.from_exam_row(
        exam,
        total_questions_override=len(question_entities),
        default_is_preset=1,
    )
    return ExamDetailResponse.from_entities(exam_entity, question_entities)

@exams_router.post("", response_model=ExamSummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(
    payload: ExamCreateRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """
    Create a new custom mock exam (OP-057).
    """
    exam_id = f"exam_{uuid.uuid4().hex[:12]}"
    user_id = current_user.get("id") if current_user else "user"

    sql = """
        INSERT INTO exams (
            id, title, description, level, category, year,
            duration_minutes, total_questions, passing_score, max_score,
            drive_folder_url, status, is_system_preset, user_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, 0, ?)
    """
    execute_commit(sql, (
        exam_id, payload.title, payload.description, payload.level,
        payload.category or "JLPT_FULL", payload.year or 2024,
        payload.duration_minutes or 60, payload.passing_score or 90,
        payload.max_score or 180, payload.drive_folder_url,
        payload.status or "ACTIVE", user_id
    ))

    created = query_one("SELECT * FROM exams WHERE id = ?", (exam_id,))
    return ExamSummaryResponse.from_entity(
        ExamEntity.from_exam_row(
            created,
            total_questions_override=0,
            default_is_preset=0,
            user_id_override=user_id,
        )
    )

@exams_router.put("/{exam_id}", response_model=ExamSummaryResponse)
async def update_exam(
    exam_id: str,
    payload: ExamUpdateRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """
    Update exam metadata (OP-058).
    """
    existing = query_one("SELECT * FROM exams WHERE id = ?", (exam_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề thi cần sửa")

    updates = []
    params = []
    for field, val in payload.model_dump(exclude_unset=True).items():
        if val is not None:
            updates.append(f"{field} = ?")
            params.append(val)

    if updates:
        sql = f"UPDATE exams SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        params.append(exam_id)
        execute_commit(sql, tuple(params))

    updated = query_one("SELECT * FROM exams WHERE id = ?", (exam_id,))
    return ExamSummaryResponse.from_entity(ExamEntity.from_exam_row(updated, default_is_preset=0))

@exams_router.delete("/{exam_id}")
async def delete_exam(
    exam_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """
    Delete custom exam. Enforces BR-044: System presets cannot be deleted.
    """
    existing = query_one("SELECT * FROM exams WHERE id = ?", (exam_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề thi")

    if existing.get("is_system_preset"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Không thể xóa bộ đề thi mặc định của hệ thống (BR-044)"
        )

    execute_commit("DELETE FROM exams WHERE id = ?", (exam_id,))
    return {"message": "Đã xóa đề thi thành công", "id": exam_id}

# ==============================================================================
# ONLINE EXAM SUBMISSION & AUTO-SCORING (OP-060)
# ==============================================================================

@exams_router.post("/{exam_id}/submit", response_model=ExamSubmissionResult)
async def submit_exam(
    exam_id: str,
    payload: ExamSubmissionRequest
):
    """
    Submit interactive exam answers, auto-score, check pass/fail, and generate Sensei explanations (OP-060).
    """
    exam = query_one("SELECT * FROM exams WHERE id = ?", (exam_id,))
    if not exam:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề thi")

    questions = query_all("SELECT * FROM exam_questions WHERE exam_id = ? ORDER BY question_number ASC", (exam_id,))
    if not questions:
        raise HTTPException(status_code=400, detail="Đề thi này hiện chưa có câu hỏi nào để chấm điểm")

    total_questions = len(questions)
    correct_count = 0
    answered_count = 0
    results: List[QuestionResultItem] = []

    for q in questions:
        q_id = q["id"]
        correct_answer = q["correct_option"]
        user_ans = payload.answers.get(q_id)

        if user_ans is not None:
            answered_count += 1
            is_correct = (user_ans == correct_answer)
        else:
            is_correct = False

        if is_correct:
            correct_count += 1

        results.append(QuestionResultItem(
            question_id=q_id,
            user_answer=user_ans,
            correct_answer=correct_answer,
            is_correct=is_correct,
            explanation=q.get("explanation")
        ))

    # Calculate proportional score
    max_score = exam["max_score"] or 180
    passing_score = exam["passing_score"] or 90
    score = int(round((correct_count / total_questions) * max_score)) if total_questions > 0 else 0
    passed = (score >= passing_score)

    percentage = round((correct_count / total_questions) * 100, 1) if total_questions > 0 else 0
    if percentage >= 90:
        feedback = f"Subarashii! (素晴らしい!) Bạn đạt {score}/{max_score} điểm ({percentage}%). Kiến thức rất vững vàng, chúc bạn tiếp tục phát huy!"
    elif percentage >= 70:
        feedback = f"Yoku dekimashita! (よくできました!) Bạn đạt {score}/{max_score} điểm ({percentage}%). Đã vượt qua điểm chuẩn đỗ, hãy xem lại các câu giải thích để hoàn thiện hơn."
    elif percentage >= 50:
        feedback = f"Mou sukoshi desu! (もう少しです!) Bạn đạt {score}/{max_score} điểm ({percentage}%). Hãy ôn luyện kỹ lại phần ngữ pháp và từ vựng qua kho tài liệu tham khảo nhé!"
    else:
        feedback = f"Ganbatte kudasai! (頑張ってください!) Bạn đạt {score}/{max_score} điểm ({percentage}%). Đừng nản lòng, hãy cùng Sensei ôn tập lại từ bài học căn bản!"

    return ExamSubmissionResult(
        exam_id=exam_id,
        total_questions=total_questions,
        answered_count=answered_count,
        correct_count=correct_count,
        score=score,
        max_score=max_score,
        passing_score=passing_score,
        passed=passed,
        feedback_message=feedback,
        results=results
    )
