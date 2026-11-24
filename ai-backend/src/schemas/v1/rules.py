"""Rules Management API schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from src.models.v1.rule import VALID_ACTIVATION_MODES, VALID_RULE_STATUSES


class RuleBaseRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Tên quy tắc (1-100 ký tự)")
    description: Optional[str] = Field(default=None, max_length=500, description="Mô tả tóm tắt mục đích (tối đa 500 ký tự)")
    content: str = Field(..., min_length=1, max_length=10000, description="Nội dung Markdown quy tắc (1-10.000 ký tự)")
    activation_mode: str = Field(default="always_on", description="Chế độ kích hoạt: always_on, model_decision, glob, manual")
    glob_patterns: List[str] = Field(default_factory=list, description="Danh sách glob patterns khi activation_mode = 'glob'")
    tags: List[str] = Field(default_factory=list, description="Danh sách các tag phân loại")
    priority: int = Field(default=50, ge=0, le=100, description="Mức độ ưu tiên từ 0 đến 100")

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Tên quy tắc không được để trống hoặc chỉ chứa khoảng trắng.")
        return trimmed

    @field_validator("content")
    @classmethod
    def validate_content_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Nội dung quy tắc không được để trống hoặc chỉ chứa khoảng trắng.")
        return v

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        return trimmed if trimmed else None

    @field_validator("activation_mode")
    @classmethod
    def validate_activation_mode(cls, v: str) -> str:
        if v not in VALID_ACTIVATION_MODES:
            raise ValueError(f"activation_mode không hợp lệ. Phải là một trong: {VALID_ACTIVATION_MODES}")
        return v

    @field_validator("glob_patterns")
    @classmethod
    def validate_glob_patterns(cls, patterns: List[str]) -> List[str]:
        cleaned = []
        for p in patterns:
            p_str = str(p).strip()
            if not p_str:
                continue
            if ".." in p_str:
                raise ValueError("Glob pattern không được chứa ký tự điều hướng thư mục cha '..'.")
            cleaned.append(p_str)
        return cleaned


class RuleCreateRequest(RuleBaseRequest):
    pass


class RuleUpdateRequest(RuleBaseRequest):
    status: Optional[str] = Field(default="active", description="Trạng thái: active, inactive, archived")
    version: int = Field(..., ge=1, description="Số phiên bản hiện tại phục vụ Optimistic Concurrency Control")


class RuleStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="Trạng thái mới: 'active' hoặc 'inactive'")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_RULE_STATUSES:
            raise ValueError("Trạng thái chỉ có thể là 'active' hoặc 'inactive'.")
        return v


class RuleResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    content: str
    scope: str
    activation_mode: str
    glob_patterns: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    priority: int
    status: str
    version: int
    is_editable: bool = True
    associated_projects_count: int = 0
    created_at: str
    updated_at: str
    deleted_at: Optional[str] = None


class PaginatedRuleResponse(BaseModel):
    items: List[RuleResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class ProjectRuleBindingRequest(BaseModel):
    rule_ids: List[str] = Field(default_factory=list, description="Danh sách rule_id muốn gán cho dự án")
