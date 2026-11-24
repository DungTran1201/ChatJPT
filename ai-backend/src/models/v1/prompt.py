"""System Prompt / Sensei Persona domain entity (system_prompts table)."""

from typing import Any, Dict, List, Mapping, Optional
from src.models.v1.base import DomainModel


class SystemPromptEntity(DomainModel):
    """Domain entity mirroring the system_prompts table."""

    id: str
    user_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    content: Optional[str] = None
    content_length: int = 0
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
    attachments: List[Dict[str, Any]] = []
    created_at: str = ""
    updated_at: str = ""

    @staticmethod
    def default_avatar_url(prompt_id: str) -> str:
        return f"https://api.dicebear.com/7.x/bottts/svg?seed={prompt_id}"

    @classmethod
    def from_prompt_row(
        cls,
        row: Mapping[str, Any],
        *,
        fallback_avatar: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        force_system_preset: Optional[bool] = None,
    ) -> "SystemPromptEntity":
        content = row.get("content")
        content_len = row.get("content_length")
        if content_len is None:
            content_len = len(content) if content else 0

        avatar = row.get("avatar_url")
        if not avatar and fallback_avatar is not None:
            avatar = fallback_avatar

        is_preset = (
            force_system_preset
            if force_system_preset is not None
            else bool(row.get("is_system_preset", 0))
        )

        return cls(
            id=row["id"],
            user_id=row.get("user_id"),
            name=row["name"],
            description=row.get("description"),
            content=content,
            content_length=content_len,
            age=row.get("age", 25),
            gender=row.get("gender", "female"),
            japanese_level=row.get("japanese_level", "N5"),
            personality=row.get("personality"),
            teaching_style=row.get("teaching_style"),
            catchphrase=row.get("catchphrase"),
            hobbies=row.get("hobbies"),
            avatar_url=avatar,
            voice_id=row.get("voice_id"),
            is_default=bool(row.get("is_default", 0)),
            is_system_preset=is_preset,
            attachments=attachments or [],
            created_at=str(row.get("created_at")),
            updated_at=str(row.get("updated_at")),
        )
