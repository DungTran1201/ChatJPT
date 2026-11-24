"""System Prompt / Sensei Guidance API schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from src.models.v1.prompt import SystemPromptEntity


class SystemPromptBaseRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Tên của Sensei (1-100 ký tự, e.g. Sakura-sensei 桜先生)",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Mô tả tóm tắt phong cách hoặc chuyên môn của Sensei (tối đa 500 ký tự)",
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Chỉ thị Persona cốt lõi cho AI (System Prompt instructions, 1-10.000 ký tự)",
    )
    age: Optional[int] = Field(
        default=25,
        ge=18,
        le=100,
        description="Tuổi của Sensei (18-100)",
    )
    gender: Optional[str] = Field(
        default="female",
        description="Giới tính / Xưng hô của Sensei (female, male, other)",
    )
    japanese_level: Optional[str] = Field(
        default="N5",
        description="Trình độ tiếng Nhật chuyên trách (N5, N4, N3, N2, N1, ALL)",
    )
    personality: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Nét tính cách sư phạm đặc trưng (e.g. Dịu dàng, Kiên nhẫn, Hóm hỉnh)",
    )
    teaching_style: Optional[str] = Field(
        default=None,
        description="Phương pháp sư phạm & quy chuẩn Furigana/Song ngữ",
    )
    catchphrase: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Câu nói cửa miệng / Lời chào thương hiệu của Sensei",
    )
    hobbies: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Sở thích & chủ đề đàm thoại yêu thích của Sensei",
    )
    avatar_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Ảnh đại diện Sensei (Avatar URL)",
    )
    voice_id: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Mã giọng nói VoiceVox gán cho Sensei (FK -> voices.id)",
    )
    is_default: Optional[bool] = Field(
        default=False,
        description="Đặt làm Sensei mặc định đồng hành",
    )

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Tên Sensei không được để trống hoặc chỉ chứa khoảng trắng.")
        return trimmed

    @field_validator("content")
    @classmethod
    def validate_content_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Nội dung chỉ dẫn Persona không được để trống hoặc chỉ chứa khoảng trắng.")
        return v

    @field_validator("description", "personality", "teaching_style", "catchphrase", "hobbies", "avatar_url")
    @classmethod
    def sanitize_optional_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        return trimmed if trimmed else None


class SystemPromptCreateRequest(SystemPromptBaseRequest):
    pass


class SystemPromptUpdateRequest(SystemPromptBaseRequest):
    pass


class SystemPromptSummaryResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    content_length: int
    age: Optional[int] = 25
    gender: Optional[str] = "female"
    japanese_level: Optional[str] = "N5"
    personality: Optional[str] = None
    teaching_style: Optional[str] = None
    catchphrase: Optional[str] = None
    hobbies: Optional[str] = None
    avatar_url: Optional[str] = None
    voice_id: Optional[str] = None
    is_default: bool = False
    is_system_preset: bool = False
    created_at: str
    updated_at: str

    @classmethod
    def from_entity(cls, entity: SystemPromptEntity) -> "SystemPromptSummaryResponse":
        return cls(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            content_length=entity.content_length,
            age=entity.age,
            gender=entity.gender,
            japanese_level=entity.japanese_level,
            personality=entity.personality,
            teaching_style=entity.teaching_style,
            catchphrase=entity.catchphrase,
            hobbies=entity.hobbies,
            avatar_url=entity.avatar_url or SystemPromptEntity.default_avatar_url(entity.id),
            voice_id=entity.voice_id,
            is_default=entity.is_default,
            is_system_preset=entity.is_system_preset,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class SystemPromptListResponse(BaseModel):
    items: List[SystemPromptSummaryResponse]
    total: int


class SystemPromptDetailResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    content: str
    age: Optional[int] = 25
    gender: Optional[str] = "female"
    japanese_level: Optional[str] = "N5"
    personality: Optional[str] = None
    teaching_style: Optional[str] = None
    catchphrase: Optional[str] = None
    hobbies: Optional[str] = None
    avatar_url: Optional[str] = None
    voice_id: Optional[str] = None
    is_default: bool = False
    is_system_preset: bool = False
    attachments: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    created_at: str
    updated_at: str

    @classmethod
    def from_entity(cls, entity: SystemPromptEntity) -> "SystemPromptDetailResponse":
        return cls(
            id=entity.id,
            user_id=entity.user_id or "",
            name=entity.name,
            description=entity.description,
            content=entity.content or "",
            age=entity.age,
            gender=entity.gender,
            japanese_level=entity.japanese_level,
            personality=entity.personality,
            teaching_style=entity.teaching_style,
            catchphrase=entity.catchphrase,
            hobbies=entity.hobbies,
            avatar_url=entity.avatar_url,
            voice_id=entity.voice_id,
            is_default=entity.is_default,
            is_system_preset=entity.is_system_preset,
            attachments=entity.attachments,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
