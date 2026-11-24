"""User & Identity domain models (users table)."""

import re
from enum import Enum
from typing import Any, Dict, Mapping, Optional
from src.models.v1.base import DomainModel

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_.]{3,30}$")
HEX_COLOR_REGEX = re.compile(r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
ACCENT_COLOR_PRESETS = ("emerald", "sakura", "violet", "amber", "sky")


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class ThemePreference(str, Enum):
    DARK = "DARK"
    LIGHT = "LIGHT"
    SYSTEM = "SYSTEM"


class LanguagePreference(str, Enum):
    VI = "vi"
    EN = "en"
    JA = "ja"


class UiFontSize(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class BilingualMode(str, Enum):
    INTERLINEAR = "interlinear"
    PARALLEL = "parallel"
    JAPANESE_ONLY = "japanese_only"


class UserPreferencesModel(DomainModel):
    """Appearance, i18n, and Sensei response formatting preferences."""

    theme_preference: str = "DARK"
    language_preference: str = "vi"
    custom_bg_url: str = ""
    bg_opacity: int = 90
    bg_blur: int = 12
    bg_dim: int = 0
    accent_color: str = "emerald"
    ui_font_size: str = "medium"
    response_show_translation: bool = True
    response_show_furigana: bool = True
    response_highlight_grammar: bool = True
    response_show_romaji: bool = True
    response_grammar_breakdown: bool = True
    response_audio_speech: bool = True
    response_bilingual_mode: str = "interlinear"

    @classmethod
    def from_user_row(cls, row: Mapping[str, Any]) -> "UserPreferencesModel":
        return cls(
            theme_preference=row.get("theme_preference") or "DARK",
            language_preference=row.get("language_preference") or "vi",
            custom_bg_url=row.get("custom_bg_url") or "",
            bg_opacity=row["bg_opacity"] if row.get("bg_opacity") is not None else 90,
            bg_blur=row["bg_blur"] if row.get("bg_blur") is not None else 12,
            bg_dim=row["bg_dim"] if row.get("bg_dim") is not None else 0,
            accent_color=row.get("accent_color") or "emerald",
            ui_font_size=row.get("ui_font_size") or "medium",
            response_show_translation=bool(row.get("response_show_translation", 1)),
            response_show_furigana=bool(row.get("response_show_furigana", 1)),
            response_highlight_grammar=bool(row.get("response_highlight_grammar", 1)),
            response_show_romaji=bool(row.get("response_show_romaji", 1)),
            response_grammar_breakdown=bool(row.get("response_grammar_breakdown", 1)),
            response_audio_speech=bool(row.get("response_audio_speech", 1)),
            response_bilingual_mode=row.get("response_bilingual_mode") or "interlinear",
        )


class UserStatsModel(DomainModel):
    total_conversations: int = 0
    total_messages: int = 0


class UserModel(DomainModel):
    """Domain entity mirroring the users table."""

    id: str
    email: str
    full_name: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = None
    age: Optional[int] = None
    occupation: str = ""
    interests: str = ""
    japanese_level: str = "CHUA_HOC"
    learning_goal: str = ""
    discord_id: Optional[str] = None
    discord_username: Optional[str] = None
    custom_bg_url: str = ""
    bg_opacity: int = 90
    bg_blur: int = 12
    bg_dim: int = 0
    accent_color: str = "emerald"
    ui_font_size: str = "medium"
    theme_preference: str = "DARK"
    language_preference: str = "vi"
    response_show_translation: bool = True
    response_show_furigana: bool = True
    response_highlight_grammar: bool = True
    response_show_romaji: bool = True
    response_grammar_breakdown: bool = True
    response_audio_speech: bool = True
    response_bilingual_mode: str = "interlinear"
    status: str = UserStatus.ACTIVE.value
    created_at: Optional[str] = None
    last_login_at: Optional[str] = None
    password_changed_at: Optional[str] = None

    @classmethod
    def from_user_row(
        cls,
        row: Mapping[str, Any],
        *,
        blank_missing_text: bool = False,
    ) -> "UserModel":
        prefs = UserPreferencesModel.from_user_row(row)
        default_str = "" if blank_missing_text else None
        return cls(
            id=row["id"],
            email=row["email"],
            full_name=row.get("full_name") or default_str if blank_missing_text else row.get("full_name"),
            username=row.get("username") or default_str if blank_missing_text else row.get("username"),
            avatar_url=row.get("avatar_url") or default_str if blank_missing_text else row.get("avatar_url"),
            bio=row.get("bio") or default_str if blank_missing_text else row.get("bio"),
            phone_number=row.get("phone_number") or default_str if blank_missing_text else row.get("phone_number"),
            age=row.get("age"),
            occupation=row.get("occupation") or "",
            interests=row.get("interests") or "",
            japanese_level=row.get("japanese_level") or "CHUA_HOC",
            learning_goal=row.get("learning_goal") or "",
            discord_id=row.get("discord_id"),
            discord_username=row.get("discord_username"),
            status=row.get("status") or UserStatus.ACTIVE.value,
            created_at=str(row["created_at"]) if row.get("created_at") is not None else None,
            last_login_at=str(row["last_login_at"]) if row.get("last_login_at") is not None else None,
            password_changed_at=str(row["password_changed_at"]) if row.get("password_changed_at") is not None else None,
            **prefs.model_dump(),
        )

    def to_login_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude={"password_changed_at"})

    def to_profile_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude={"discord_id", "discord_username", "password_changed_at"})
