"""Exam Management & Reference Materials API schemas (Pydantic v2)."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from src.models.v1.exam import (
    VALID_EXAM_LEVELS,
    VALID_MATERIAL_CATEGORIES,
    ExamEntity,
    ExamQuestionEntity,
    ReferenceMaterialEntity,
)


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

    @classmethod
    def from_entity(cls, entity: ExamQuestionEntity) -> "ExamQuestionSummary":
        return cls.model_validate(entity.model_dump(exclude={"exam_id"}))


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

    @classmethod
    def from_entity(cls, entity: ExamEntity) -> "ExamSummaryResponse":
        return cls.model_validate(entity.model_dump())


class ExamDetailResponse(ExamSummaryResponse):
    questions: List[ExamQuestionSummary] = Field(default_factory=list)

    @classmethod
    def from_entities(
        cls,
        exam: ExamEntity,
        questions: List[ExamQuestionEntity],
    ) -> "ExamDetailResponse":
        return cls(
            **exam.model_dump(),
            questions=[ExamQuestionSummary.from_entity(q) for q in questions],
        )


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

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        up = v.upper()
        if up not in VALID_EXAM_LEVELS:
            raise ValueError(f"Cấp độ không hợp lệ: {v}. Phải là một trong {list(VALID_EXAM_LEVELS)}")
        return up

    @field_validator("drive_folder_url")
    @classmethod
    def validate_drive_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith("https://") and not v.startswith("/"):
            raise ValueError("Đường dẫn liên kết phải sử dụng giao thức HTTPS bảo mật hoặc đường dẫn nội bộ")
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

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            up = v.upper()
            if up not in VALID_EXAM_LEVELS:
                raise ValueError(f"Cấp độ không hợp lệ: {v}. Phải là một trong {list(VALID_EXAM_LEVELS)}")
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
    def from_entity(cls, entity: ReferenceMaterialEntity) -> "ReferenceMaterialItem":
        return cls.model_validate(entity.model_dump())


class ReferenceMaterialListResponse(BaseModel):
    total: int
    items: List[ReferenceMaterialItem]


class ReferenceMaterialCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    category: str = Field(...)
    level: Optional[str] = Field(default="ALL")
    source_type: Optional[str] = Field(default="LOCAL_FILE")
    external_url: str = Field(..., max_length=1000)
    author: Optional[str] = Field(default=None, max_length=100)
    file_type: Optional[str] = Field(default="pdf")
    tags: Optional[str] = Field(default=None, max_length=255)
    is_pinned: Optional[bool] = False

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        up = v.upper()
        if up not in VALID_MATERIAL_CATEGORIES:
            raise ValueError(f"Chuyên mục tài liệu không hợp lệ: {v}")
        return up

    @field_validator("external_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith("https://") and not v.startswith("/"):
            raise ValueError("Đường dẫn liên kết phải sử dụng giao thức HTTPS bảo mật hoặc đường dẫn nội bộ")
        return v
