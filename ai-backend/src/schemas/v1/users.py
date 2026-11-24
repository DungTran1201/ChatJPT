"""User profile, security & preferences API schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    username: Optional[str] = Field(None, description="Tên đăng nhập (3-30 ký tự chữ, số, _, .)")
    bio: Optional[str] = Field(None, max_length=500)
    phone_number: Optional[str] = Field(None, max_length=20)
    age: Optional[int] = Field(None, ge=1, le=120, description="Tuổi người dùng (1 - 120)")
    occupation: Optional[str] = Field(None, max_length=100, description="Nghề nghiệp / Lĩnh vực công tác")
    interests: Optional[str] = Field(None, max_length=255, description="Sở thích cá nhân / chủ đề quan tâm")
    japanese_level: Optional[str] = Field(None, max_length=20, description="Trình độ tiếng Nhật (CHUA_HOC, N5, N4, N3, N2, N1)")
    learning_goal: Optional[str] = Field(None, max_length=255, description="Mục tiêu học tập tiếng Nhật")


class UpdateAvatarRequest(BaseModel):
    avatar_url: str = Field(..., max_length=500, description="URL ảnh đại diện hoặc chuỗi data URI")


class ChangeEmailRequest(BaseModel):
    new_email: str = Field(..., description="Email mới")
    current_password: str = Field(..., min_length=1, description="Mật khẩu hiện tại để xác thực lại")


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, description="Mật khẩu hiện tại")
    new_password: str = Field(..., min_length=8, description="Mật khẩu mới tối thiểu 8 ký tự")


class UpdatePreferencesRequest(BaseModel):
    theme_preference: Optional[str] = Field(None, description="DARK, LIGHT, hoặc SYSTEM")
    language_preference: Optional[str] = Field(None, description="vi, en hoặc ja")
    custom_bg_url: Optional[str] = Field(None, max_length=1000, description="URL hoặc chuỗi data URI hình nền tùy chỉnh")
    bg_opacity: Optional[int] = Field(None, ge=20, le=100, description="Độ mờ đục của các lớp layer phủ lên nền (20 - 100%)")
    bg_blur: Optional[int] = Field(None, ge=0, le=40, description="Độ mờ kính backdrop-filter blur (0 - 40px)")
    bg_dim: Optional[int] = Field(None, ge=0, le=100, description="Độ tối của hình nền (0 - 100%)")
    accent_color: Optional[str] = Field(None, max_length=30, description="Màu chủ đạo (emerald, sakura, violet, amber, sky hoặc mã màu HEX #xxxxxx)")
    ui_font_size: Optional[str] = Field(None, description="Cỡ chữ hiển thị (small, medium, large)")
    response_show_translation: Optional[bool] = Field(None, description="Công tắc dịch sang ngôn ngữ hiển thị")
    response_show_furigana: Optional[bool] = Field(None, description="Công tắc hiển thị Hiragana trên đầu chữ Kanji (Furigana / Ruby)")
    response_highlight_grammar: Optional[bool] = Field(None, description="Công tắc tô màu vùng ngữ pháp & trợ từ")
    response_show_romaji: Optional[bool] = Field(None, description="Công tắc hiển thị Romaji bên dưới từng từ")
    response_grammar_breakdown: Optional[bool] = Field(None, description="Công tắc phân tích ngữ pháp & từ vựng trọng tâm")
    response_audio_speech: Optional[bool] = Field(None, description="Công tắc hỗ trợ phát âm câu tiếng Nhật (Text-to-Speech)")
    response_bilingual_mode: Optional[str] = Field(None, description="Chế độ hiển thị song ngữ: interlinear, parallel, japanese_only")
