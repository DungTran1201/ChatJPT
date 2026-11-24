"""Authentication API request & response schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str = Field(description="Email đăng ký")
    password: str = Field(min_length=6, description="Mật khẩu tối thiểu 6 ký tự")
    full_name: Optional[str] = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = ""
    status: str
    created_at: str
