"""Text file import API schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class TextFileImportRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255, description="Tên tệp gốc kèm phần mở rộng")
    content: str = Field(..., min_length=1, description="Toàn bộ nội dung văn bản thuần túy của tệp")
    target: Optional[str] = Field(default=None, description="Mục tiêu nhập: 'rule' hoặc 'prompt'")
    override_name: Optional[str] = Field(default=None, max_length=100, description="Tên hiển thị tùy chỉnh ghi đè")
    name: Optional[str] = Field(default=None, max_length=100, description="Tên hiển thị tùy chỉnh")
    override_description: Optional[str] = Field(default=None, max_length=500, description="Mô tả tóm tắt tùy chỉnh ghi đè")
    description: Optional[str] = Field(default=None, max_length=500, description="Mô tả tóm tắt")
    activation_mode: Optional[str] = Field(default=None, description="Chế độ kích hoạt cho Rule")
    glob_patterns: Optional[List[str]] = Field(default_factory=list, description="Danh sách glob patterns")
    tags: Optional[List[str]] = Field(default_factory=list, description="Danh sách tags cho Rule")
    priority: Optional[int] = Field(default=None, ge=0, le=100, description="Mức độ ưu tiên cho Rule")
