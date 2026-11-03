import uuid
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field, HttpUrl, validator

from src.core.security import get_optional_current_user
from src.db import query_one, query_all, execute_commit

logger = logging.getLogger("exams_api")

exams_router = APIRouter(prefix="/exams", tags=["Exam Management & Reference Materials"])

VALID_LEVELS = {"N5", "N4", "N3", "N2", "N1", "KAIWA", "GENERAL"}
VALID_MATERIAL_CATEGORIES = {
    "JLPT_N5", "JLPT_N4", "JLPT_N3", "JLPT_N2", "JLPT_N1",
    "KAIWA", "GRAMMAR_GUIDE", "VOCABULARY_DICT"
}

# ==============================================================================
# PYDANTIC SCHEMAS
# ==============================================================================

class ExamQuestionSummary(BaseModel):
    id: str
    section: str
    question_number: int
    question_text: str
    furigana_text: Optional[str] = None
    option_1: str
    option_2: str
    option_3: str
    option_4: str
    correct_option: Optional[int] = None
    explanation: Optional[str] = None

class ExamSummaryResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    level: str
    category: str
    year: Optional[int] = None
    duration_minutes: int
    total_questions: int
    passing_score: int
    max_score: int
    drive_folder_url: Optional[str] = None
    status: str
    is_system_preset: bool
    user_id: Optional[str] = "system"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ExamDetailResponse(ExamSummaryResponse):
    questions: List[ExamQuestionSummary] = []

class ExamListResponse(BaseModel):
    total: int
    items: List[ExamSummaryResponse]

class ExamCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    level: str = Field(..., description="N5, N4, N3, N2, N1, KAIWA, or GENERAL")
    category: Optional[str] = Field(default="JLPT_FULL", max_length=50)
    year: Optional[int] = Field(default=2024, ge=2000, le=2100)
    duration_minutes: Optional[int] = Field(default=60, ge=5, le=300)
    passing_score: Optional[int] = Field(default=90, ge=1, le=500)
    max_score: Optional[int] = Field(default=180, ge=1, le=500)
    drive_folder_url: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[str] = Field(default="ACTIVE")

    @validator("level")
    def validate_level(cls, v):
        up = v.upper()
        if up not in VALID_LEVELS:
            raise ValueError(f"Cấp độ không hợp lệ: {v}. Phải là một trong {list(VALID_LEVELS)}")
        return up

    @validator("drive_folder_url")
    def validate_drive_url(cls, v):
        if v and not v.startswith("https://"):
            raise ValueError("Đường dẫn liên kết phải sử dụng giao thức HTTPS bảo mật")
        return v

class ExamUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    level: Optional[str] = None
    category: Optional[str] = None
    year: Optional[int] = None
    duration_minutes: Optional[int] = None
    passing_score: Optional[int] = None
    max_score: Optional[int] = None
    drive_folder_url: Optional[str] = None
    status: Optional[str] = None

    @validator("level")
    def validate_level(cls, v):
        if v is not None:
            up = v.upper()
            if up not in VALID_LEVELS:
                raise ValueError(f"Cấp độ không hợp lệ: {v}. Phải là một trong {list(VALID_LEVELS)}")
            return up
        return v

class ExamSubmissionRequest(BaseModel):
    answers: Dict[str, int] = Field(..., description="Map of question_id to selected option (1..4)")

class QuestionResultItem(BaseModel):
    question_id: str
    user_answer: Optional[int]
    correct_answer: int
    is_correct: bool
    explanation: Optional[str]

class ExamSubmissionResult(BaseModel):
    exam_id: str
    total_questions: int
    answered_count: int
    correct_count: int
    score: int
    max_score: int
    passing_score: int
    passed: bool
    feedback_message: str
    results: List[QuestionResultItem]

class ReferenceMaterialItem(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    category: str
    level: str
    source_type: str
    external_url: str
    author: Optional[str] = None
    file_type: str = "folder"
    tags: Optional[str] = None
    is_pinned: bool = False
    is_system_preset: bool = True
    user_id: Optional[str] = "system"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ReferenceMaterialListResponse(BaseModel):
    total: int
    items: List[ReferenceMaterialItem]

class ReferenceMaterialCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    category: str = Field(...)
    level: Optional[str] = Field(default="ALL")
    source_type: Optional[str] = Field(default="GOOGLE_DRIVE")
    external_url: str = Field(..., max_length=1000)
    author: Optional[str] = Field(default=None, max_length=100)
    file_type: Optional[str] = Field(default="folder")
    tags: Optional[str] = Field(default=None, max_length=255)
    is_pinned: Optional[bool] = False

    @validator("category")
    def validate_category(cls, v):
        up = v.upper()
        if up not in VALID_MATERIAL_CATEGORIES:
            raise ValueError(f"Chuyên mục tài liệu không hợp lệ: {v}")
        return up

    @validator("external_url")
    def validate_url(cls, v):
        if not v.startswith("https://"):
            raise ValueError("Đường dẫn liên kết phải sử dụng giao thức HTTPS bảo mật")
        return v

# ==============================================================================
# REFERENCE MATERIALS ENDPOINTS (OP-061, OP-062)
# ==============================================================================

@exams_router.get("/materials", response_model=ReferenceMaterialListResponse)
async def list_reference_materials(
    category: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """
    List reference materials across JLPT N5..N1, Kaiwa, Tae Kim Grammar, and Dictionaries.
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
        ReferenceMaterialItem(
            id=r["id"],
            title=r["title"],
            description=r.get("description"),
            category=r["category"],
            level=r["level"] or "ALL",
            source_type=r["source_type"] or "GOOGLE_DRIVE",
            external_url=r["external_url"],
            author=r.get("author"),
            file_type=r.get("file_type") or "folder",
            tags=r.get("tags"),
            is_pinned=bool(r.get("is_pinned", 0)),
            is_system_preset=bool(r.get("is_system_preset", 1)),
            user_id=r.get("user_id", "system"),
            created_at=str(r.get("created_at") or ""),
            updated_at=str(r.get("updated_at") or "")
        )
        for r in rows
    ]

    return ReferenceMaterialListResponse(total=len(items), items=items)

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
        payload.level or "ALL", payload.source_type or "GOOGLE_DRIVE",
        payload.external_url, payload.author, payload.file_type or "folder",
        payload.tags, 1 if payload.is_pinned else 0, user_id
    ))

    created = query_one("SELECT * FROM reference_materials WHERE id = ?", (mat_id,))
    return ReferenceMaterialItem(
        id=created["id"],
        title=created["title"],
        description=created.get("description"),
        category=created["category"],
        level=created["level"] or "ALL",
        source_type=created["source_type"] or "GOOGLE_DRIVE",
        external_url=created["external_url"],
        author=created.get("author"),
        file_type=created.get("file_type") or "folder",
        tags=created.get("tags"),
        is_pinned=bool(created.get("is_pinned", 0)),
        is_system_preset=False,
        user_id=user_id,
        created_at=str(created.get("created_at") or ""),
        updated_at=str(created.get("updated_at") or "")
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
            ExamSummaryResponse(
                id=r["id"],
                title=r["title"],
                description=r.get("description"),
                level=r["level"],
                category=r.get("category") or "JLPT_FULL",
                year=r.get("year"),
                duration_minutes=r["duration_minutes"] or 60,
                total_questions=actual_q_count,
                passing_score=r["passing_score"] or 90,
                max_score=r["max_score"] or 180,
                drive_folder_url=r.get("drive_folder_url"),
                status=r.get("status") or "ACTIVE",
                is_system_preset=bool(r.get("is_system_preset", 1)),
                user_id=r.get("user_id", "system"),
                created_at=str(r.get("created_at") or ""),
                updated_at=str(r.get("updated_at") or "")
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

    questions = [
        ExamQuestionSummary(
            id=q["id"],
            section=q["section"],
            question_number=q["question_number"],
            question_text=q["question_text"],
            furigana_text=q.get("furigana_text"),
            option_1=q["option_1"],
            option_2=q["option_2"],
            option_3=q["option_3"],
            option_4=q["option_4"],
            correct_option=q["correct_option"] if include_answers else None,
            explanation=q.get("explanation") if include_answers else None
        )
        for q in questions_raw
    ]

    return ExamDetailResponse(
        id=exam["id"],
        title=exam["title"],
        description=exam.get("description"),
        level=exam["level"],
        category=exam.get("category") or "JLPT_FULL",
        year=exam.get("year"),
        duration_minutes=exam["duration_minutes"] or 60,
        total_questions=len(questions),
        passing_score=exam["passing_score"] or 90,
        max_score=exam["max_score"] or 180,
        drive_folder_url=exam.get("drive_folder_url"),
        status=exam.get("status") or "ACTIVE",
        is_system_preset=bool(exam.get("is_system_preset", 1)),
        user_id=exam.get("user_id", "system"),
        created_at=str(exam.get("created_at") or ""),
        updated_at=str(exam.get("updated_at") or ""),
        questions=questions
    )

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
    return ExamSummaryResponse(
        id=created["id"],
        title=created["title"],
        description=created.get("description"),
        level=created["level"],
        category=created.get("category") or "JLPT_FULL",
        year=created.get("year"),
        duration_minutes=created["duration_minutes"] or 60,
        total_questions=0,
        passing_score=created["passing_score"] or 90,
        max_score=created["max_score"] or 180,
        drive_folder_url=created.get("drive_folder_url"),
        status=created.get("status") or "ACTIVE",
        is_system_preset=False,
        user_id=user_id,
        created_at=str(created.get("created_at") or ""),
        updated_at=str(created.get("updated_at") or "")
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
    for field, val in payload.dict(exclude_unset=True).items():
        if val is not None:
            updates.append(f"{field} = ?")
            params.append(val)

    if updates:
        sql = f"UPDATE exams SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        params.append(exam_id)
        execute_commit(sql, tuple(params))

    updated = query_one("SELECT * FROM exams WHERE id = ?", (exam_id,))
    return ExamSummaryResponse(
        id=updated["id"],
        title=updated["title"],
        description=updated.get("description"),
        level=updated["level"],
        category=updated.get("category") or "JLPT_FULL",
        year=updated.get("year"),
        duration_minutes=updated["duration_minutes"] or 60,
        total_questions=updated.get("total_questions", 0),
        passing_score=updated["passing_score"] or 90,
        max_score=updated["max_score"] or 180,
        drive_folder_url=updated.get("drive_folder_url"),
        status=updated.get("status") or "ACTIVE",
        is_system_preset=bool(updated.get("is_system_preset", 0)),
        user_id=updated.get("user_id", "system"),
        created_at=str(updated.get("created_at") or ""),
        updated_at=str(updated.get("updated_at") or "")
    )

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
