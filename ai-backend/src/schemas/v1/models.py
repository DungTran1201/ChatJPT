"""AI Model management API request & response schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class SetDefaultModelRequest(BaseModel):
    model_id: str = Field(..., description="Định danh mô hình muốn đặt làm mặc định")


class CreateModelRequest(BaseModel):
    id: str = Field(..., min_length=1, max_length=100, description="Mã định danh duy nhất (bất biến) của mô hình")
    name: str = Field(..., min_length=1, max_length=255, description="Tên hiển thị của mô hình")
    provider: str = Field(..., description="Nhà cung cấp: google, anthropic, openai, groq, ollama")
    context_window: int = Field(default=128000, ge=1000, description="Ngữ cảnh tối đa (tokens >= 1000)")
    max_tokens: int = Field(default=4096, ge=256, description="Phản hồi tối đa (tokens >= 256)")
    supports_streaming: bool = Field(default=True, description="Hỗ trợ SSE streaming")


class UpdateModelRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255, description="Tên hiển thị mới")
    context_window: Optional[int] = Field(default=None, ge=1000, description="Ngữ cảnh tối đa (tokens >= 1000)")
    max_tokens: Optional[int] = Field(default=None, ge=256, description="Phản hồi tối đa (tokens >= 256)")
    supports_streaming: Optional[bool] = Field(default=None, description="Hỗ trợ SSE streaming")


class ModelResponse(BaseModel):
    id: str
    name: str
    provider: str
    status: str
    is_default: bool
    context_window: int
    max_tokens: int
    supports_streaming: bool
    has_api_key: bool
    latency_ms: Optional[float] = None
    last_checked_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ModelSearchResponse(BaseModel):
    total: int
    execution_time_ms: float
    items: List[ModelResponse]
