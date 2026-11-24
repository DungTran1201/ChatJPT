"""BYOK API Keys & Provider Integrations schemas (never expose raw secrets)."""

from typing import Optional
from pydantic import BaseModel, Field


class ProviderKeyStatusResponse(BaseModel):
    provider: str = Field(..., description="Mã định danh chuẩn hóa của nhà cung cấp")
    name: str = Field(..., description="Tên hiển thị thân thiện")
    category: str = Field(..., description="Phân loại: LLM hoặc SEARCH")
    env_var: str = Field(..., description="Tên biến môi trường hệ thống tương ứng")
    description: str = Field(..., description="Mô tả mục đích sử dụng")
    doc_url: str = Field(..., description="Đường dẫn tài liệu tạo khóa API")
    placeholder: str = Field(..., description="Gợi ý định dạng mẫu")
    is_secret: bool = Field(default=True, description="Khóa có phải là thông tin bí mật cần che giấu không")
    is_configured: bool = Field(..., description="Trạng thái đã được cấu hình hay chưa")
    source: str = Field(..., description="Nguồn cấu hình: PERSONAL (khóa riêng), SYSTEM (mặc định server), hoặc NONE")
    masked_hint: str = Field(default="", description="Gợi ý đã che giấu (ví dụ: '****abcd')")
    has_personal_key: bool = Field(..., description="Người dùng hiện tại có khóa cá nhân riêng hay không")
    has_system_key: bool = Field(..., description="Hệ thống có cấu hình mặc định .env hay không")
    validation_status: str = Field(default="NOT_TESTED", description="Trạng thái kiểm tra: NOT_TESTED, VALID, INVALID, ERROR")
    last_validated_at: Optional[str] = Field(default=None, description="Thời điểm kiểm tra kết nối gần nhất")
    last_error_summary: Optional[str] = Field(default=None, description="Tóm tắt lỗi kiểm tra gần nhất (đã loại bỏ bí mật)")
    updated_at: Optional[str] = Field(default=None, description="Thời điểm cập nhật khóa cá nhân gần nhất")
    requires_restart: bool = Field(default=False, description="Có cần khởi động lại dịch vụ không (khóa user áp dụng runtime ngay)")


class SetApiKeyRequest(BaseModel):
    api_key: str = Field(..., min_length=1, max_length=500, description="Giá trị khóa API mới")


class TestApiKeyRequest(BaseModel):
    candidate_key: Optional[str] = Field(default=None, max_length=500, description="Khóa API tạm thời cần kiểm tra trước khi lưu")


class TestApiKeyResponse(BaseModel):
    healthy: bool = Field(..., description="Kết nối thành công hay không")
    provider: str = Field(..., description="Mã định danh nhà cung cấp")
    latency_ms: int = Field(..., description="Độ trễ phản hồi (ms)")
    validation_status: str = Field(..., description="VALID, INVALID, hoặc ERROR")
    message: str = Field(..., description="Thông báo kết quả đã làm sạch bí mật")
    tested_at: str = Field(..., description="Thời điểm hoàn tất kiểm tra")


class UpdateSystemEnvRequest(BaseModel):
    env_var: str = Field(..., description="Tên biến môi trường cần cập nhật (phải thuộc allowlist)")
    value: str = Field(..., description="Giá trị mới cần ghi vào .env")
