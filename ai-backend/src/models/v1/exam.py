"""Exam, Exam Question, and Reference Material domain entities."""

from enum import Enum
from typing import Any, Mapping, Optional
from src.models.v1.base import DomainModel

VALID_EXAM_LEVELS = {"N5", "N4", "N3", "N2", "N1", "KAIWA", "GENERAL"}
VALID_MATERIAL_CATEGORIES = {
    "JLPT_N5",
    "JLPT_N4",
    "JLPT_N3",
    "JLPT_N2",
    "JLPT_N1",
    "KAIWA",
    "GRAMMAR_GUIDE",
    "VOCABULARY_DICT",
}


class ExamStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DRAFT = "DRAFT"
    ARCHIVED = "ARCHIVED"


class ExamQuestionEntity(DomainModel):
    """Domain entity mirroring the exam_questions table."""

    id: str
    exam_id: Optional[str] = None
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

    @classmethod
    def from_question_row(
        cls,
        row: Mapping[str, Any],
        *,
        include_answers: bool = False,
    ) -> "ExamQuestionEntity":
        return cls(
            id=row["id"],
            exam_id=row.get("exam_id"),
            section=row["section"],
            question_number=row["question_number"],
            question_text=row["question_text"],
            furigana_text=row.get("furigana_text"),
            option_1=row["option_1"],
            option_2=row["option_2"],
            option_3=row["option_3"],
            option_4=row["option_4"],
            correct_option=row.get("correct_option") if include_answers else None,
            explanation=row.get("explanation") if include_answers else None,
        )


class ExamEntity(DomainModel):
    """Domain entity mirroring the exams table."""

    id: str
    title: str
    description: Optional[str] = None
    level: str
    category: str = "JLPT_FULL"
    year: Optional[int] = None
    duration_minutes: int = 60
    total_questions: int = 0
    passing_score: int = 90
    max_score: int = 180
    drive_folder_url: Optional[str] = None
    status: str = ExamStatus.ACTIVE.value
    is_system_preset: bool = False
    user_id: Optional[str] = "system"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_exam_row(
        cls,
        row: Mapping[str, Any],
        *,
        total_questions_override: Optional[int] = None,
        default_is_preset: int = 1,
        user_id_override: Optional[str] = None,
    ) -> "ExamEntity":
        raw_preset = row.get("is_system_preset")
        is_preset = bool(default_is_preset if raw_preset is None else raw_preset)
        return cls(
            id=row["id"],
            title=row["title"],
            description=row.get("description"),
            level=row["level"],
            category=row.get("category") or "JLPT_FULL",
            year=row.get("year"),
            duration_minutes=row.get("duration_minutes") or 60,
            total_questions=(
                total_questions_override
                if total_questions_override is not None
                else (row.get("total_questions") or 0)
            ),
            passing_score=row.get("passing_score") or 90,
            max_score=row.get("max_score") or 180,
            drive_folder_url=row.get("drive_folder_url"),
            status=row.get("status") or ExamStatus.ACTIVE.value,
            is_system_preset=is_preset,
            user_id=user_id_override if user_id_override is not None else (row.get("user_id") or "system"),
            created_at=str(row.get("created_at") or ""),
            updated_at=str(row.get("updated_at") or ""),
        )


class ReferenceMaterialEntity(DomainModel):
    """Domain entity mirroring the reference_materials table."""

    id: str
    title: str
    description: Optional[str] = None
    category: str
    level: str = "ALL"
    source_type: str = "LOCAL_FILE"
    external_url: str
    author: Optional[str] = None
    file_type: str = "pdf"
    tags: Optional[str] = None
    is_pinned: bool = False
    is_system_preset: bool = True
    is_local_available: bool = True
    size_display: Optional[str] = None
    view_url: Optional[str] = None
    download_url: Optional[str] = None
    user_id: Optional[str] = "system"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_material_row(
        cls,
        row: Mapping[str, Any],
        *,
        default_author: Optional[str] = None,
        compute_size_display: bool = False,
        force_system_preset: Optional[bool] = None,
        user_id_override: Optional[str] = None,
    ) -> "ReferenceMaterialEntity":
        mat_id = row["id"]
        source_type = row.get("source_type") or "LOCAL_FILE"
        external_url = row.get("external_url") or ""
        if source_type == "LOCAL_FILE" or force_system_preset is False:
            view_url = f"/api/v1/exams/materials/view/{mat_id}"
            download_url = f"/api/v1/exams/materials/download/{mat_id}"
        else:
            view_url = external_url
            download_url = external_url

        desc = row.get("description") or ""
        size_display = None
        if compute_size_display:
            size_display = desc.split("(")[-1].split(")")[0] if "(" in desc else "Tài liệu"

        raw_preset = row.get("is_system_preset")
        is_preset = (
            force_system_preset
            if force_system_preset is not None
            else (True if raw_preset is None else bool(raw_preset))
        )

        return cls(
            id=mat_id,
            title=row["title"],
            description=row.get("description"),
            category=row["category"],
            level=row.get("level") or "ALL",
            source_type=source_type,
            external_url=external_url,
            author=row.get("author") or default_author,
            file_type=row.get("file_type") or "pdf",
            tags=row.get("tags"),
            is_pinned=bool(row.get("is_pinned", 0)),
            is_system_preset=is_preset,
            is_local_available=True,
            size_display=size_display,
            view_url=view_url,
            download_url=download_url,
            user_id=user_id_override if user_id_override is not None else (row.get("user_id") or "system"),
            created_at=str(row.get("created_at") or ""),
            updated_at=str(row.get("updated_at") or ""),
        )
