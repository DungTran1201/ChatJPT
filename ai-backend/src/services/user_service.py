"""User profile, security & preferences application service (SRP, DIP)."""

from typing import Any, Dict, List, Optional, Tuple

from src.core.exceptions import (
    ConflictError,
    NotFoundError,
    UnauthorizedError,
    ValidationDomainError,
)
from src.core.security import create_access_token, hash_password, verify_password
from src.models.v1.user import (
    ACCENT_COLOR_PRESETS,
    EMAIL_REGEX,
    HEX_COLOR_REGEX,
    USERNAME_REGEX,
    UserModel,
    UserPreferencesModel,
    UserStatsModel,
)
from src.repositories.user_repo import UserRepository
from src.schemas.v1.users import (
    ChangeEmailRequest,
    ChangePasswordRequest,
    UpdateAvatarRequest,
    UpdatePreferencesRequest,
    UpdateProfileRequest,
)

_ALLOWED_JAPANESE_LEVELS = {"CHUA_HOC", "N5", "N4", "N3", "N2", "N1"}
_SAFE_IMAGE_PREFIXES = (
    "http://",
    "https://",
    "data:image/png",
    "data:image/jpeg",
    "data:image/jpg",
    "data:image/webp",
    "data:image/gif",
)


def _is_safe_media_url(url: str) -> bool:
    low = url.lower()
    if low.startswith("data:image/svg"):
        return False
    return low.startswith(_SAFE_IMAGE_PREFIXES) or low.startswith("/")


class UserService:
    """Encapsulates profile updates, credential rotations, and UI/pedagogy preferences."""

    def __init__(self, user_repo: UserRepository):
        self._users = user_repo

    def get_my_profile(self, current_user: Dict[str, Any]) -> Dict[str, Any]:
        total_convs, total_msgs = self._users.get_usage_stats(current_user["id"])
        stats = UserStatsModel(total_conversations=total_convs, total_messages=total_msgs)
        return {
            "user": UserModel.from_user_row(current_user, blank_missing_text=True).to_profile_dict(),
            "stats": stats.model_dump(),
        }

    def update_profile(self, user_id: str, req: UpdateProfileRequest) -> Dict[str, Any]:
        updates: List[str] = []
        params: List[Any] = []

        if req.full_name is not None:
            updates.append("full_name = ?")
            params.append(req.full_name.strip())

        if req.username is not None:
            clean_username = req.username.strip()
            if clean_username:
                if not USERNAME_REGEX.match(clean_username):
                    raise ValidationDomainError(
                        "Tên đăng nhập không hợp lệ. Chỉ chấp nhận 3-30 ký tự gồm chữ, số, gạch dưới và dấu chấm."
                    )
                if self._users.exists_by_username(clean_username, exclude_user_id=user_id):
                    raise ConflictError("Tên đăng nhập này đã được sử dụng. Vui lòng chọn tên khác.")
                updates.append("username = ?")
                params.append(clean_username)
            else:
                updates.append("username = NULL")

        for field_name in ("bio", "phone_number", "occupation", "interests", "learning_goal"):
            val = getattr(req, field_name)
            if val is not None:
                updates.append(f"{field_name} = ?")
                params.append(val.strip())

        if req.age is not None:
            updates.append("age = ?")
            params.append(req.age)

        if req.japanese_level is not None:
            level = req.japanese_level.strip().upper()
            if level and level not in _ALLOWED_JAPANESE_LEVELS:
                raise ValidationDomainError(
                    f"Trình độ tiếng Nhật không hợp lệ. Chọn một trong: {', '.join(sorted(_ALLOWED_JAPANESE_LEVELS))}."
                )
            updates.append("japanese_level = ?")
            params.append(level or "CHUA_HOC")

        self._users.update_fields(user_id, updates, params)
        updated = self._users.get_by_id(user_id)
        return {
            "message": "Cập nhật hồ sơ cá nhân thành công!",
            "user": UserModel.from_user_row(updated, blank_missing_text=True).to_profile_dict() if updated else None,
        }

    def update_avatar(self, user_id: str, req: UpdateAvatarRequest) -> Dict[str, Any]:
        avatar_url = req.avatar_url.strip()
        if not _is_safe_media_url(avatar_url):
            raise ValidationDomainError(
                "URL ảnh đại diện không hợp lệ. Phải bắt đầu bằng https://, http:// hoặc dữ liệu ảnh raster base64."
            )
        self._users.update_avatar(user_id, avatar_url)
        return {
            "message": "Cập nhật ảnh đại diện thành công!",
            "avatar_url": avatar_url,
        }

    def change_email(self, current_user: Dict[str, Any], req: ChangeEmailRequest) -> Tuple[Dict[str, Any], str]:
        user_id = current_user["id"]
        new_email = req.new_email.lower().strip()

        if not EMAIL_REGEX.match(new_email):
            raise ValidationDomainError("Định dạng email mới không hợp lệ.")

        if new_email == current_user["email"].lower():
            raise ValidationDomainError("Email mới phải khác địa chỉ email hiện tại của bạn.")

        creds = self._users.get_auth_credentials(user_id)
        if not creds or not creds.get("hashed_password") or not verify_password(req.current_password, creds["hashed_password"]):
            raise UnauthorizedError("Mật khẩu hiện tại không chính xác. Thao tác bị từ chối.")

        if self._users.exists_by_email(new_email, exclude_user_id=user_id):
            raise ConflictError("Địa chỉ email này đã được tài khoản khác sử dụng.")

        self._users.update_email(user_id, new_email)
        new_token = create_access_token(user_id=user_id, email=new_email)
        return (
            {
                "message": "Địa chỉ email đã được cập nhật thành công!",
                "email": new_email,
            },
            new_token,
        )

    def change_password(self, user_id: str, req: ChangePasswordRequest) -> Tuple[Dict[str, Any], str]:
        if len(req.new_password) < 8:
            raise ValidationDomainError("Mật khẩu mới phải có ít nhất 8 ký tự.")

        creds = self._users.get_auth_credentials(user_id)
        if not creds or not creds.get("hashed_password") or not verify_password(req.current_password, creds["hashed_password"]):
            raise UnauthorizedError("Mật khẩu hiện tại không chính xác.")

        if verify_password(req.new_password, creds["hashed_password"]):
            raise ValidationDomainError("Mật khẩu mới không được trùng với mật khẩu hiện tại của bạn.")

        self._users.update_password(user_id, hash_password(req.new_password))
        new_token = create_access_token(user_id=user_id, email=creds["email"])
        return (
            {
                "message": "Đổi mật khẩu thành công. Các phiên làm việc cũ đã được thu hồi.",
                "token": new_token,
            },
            new_token,
        )

    def update_preferences(self, user_id: str, req: UpdatePreferencesRequest) -> Dict[str, Any]:
        updates: List[str] = []
        params: List[Any] = []

        if req.theme_preference is not None:
            theme = req.theme_preference.upper()
            if theme not in ("DARK", "LIGHT", "SYSTEM"):
                raise ValidationDomainError("Chủ đề không hợp lệ. Chọn DARK, LIGHT, hoặc SYSTEM.")
            updates.append("theme_preference = ?")
            params.append(theme)

        if req.language_preference is not None:
            lang = req.language_preference.lower().strip()
            if lang not in ("vi", "en", "ja"):
                raise ValidationDomainError("Ngôn ngữ không hợp lệ. Chọn vi, en hoặc ja.")
            updates.append("language_preference = ?")
            params.append(lang)

        if req.custom_bg_url is not None:
            clean_bg = req.custom_bg_url.strip()
            if clean_bg and not _is_safe_media_url(clean_bg):
                raise ValidationDomainError("URL hình nền không hợp lệ (chỉ chấp nhận https://, http:// hoặc ảnh base64).")
            updates.append("custom_bg_url = ?")
            params.append(clean_bg if clean_bg else None)

        for int_field in ("bg_opacity", "bg_blur", "bg_dim"):
            val = getattr(req, int_field)
            if val is not None:
                updates.append(f"{int_field} = ?")
                params.append(val)

        if req.accent_color is not None:
            accent = req.accent_color.strip()
            if accent.lower() in ACCENT_COLOR_PRESETS:
                updates.append("accent_color = ?")
                params.append(accent.lower())
            elif HEX_COLOR_REGEX.match(accent):
                updates.append("accent_color = ?")
                params.append(accent)
            else:
                raise ValidationDomainError(
                    "Màu chủ đạo không hợp lệ. Chọn preset (emerald, sakura, violet, amber, sky) hoặc mã màu HEX hợp lệ (ví dụ #ec4899)."
                )

        if req.ui_font_size is not None:
            fsize = req.ui_font_size.lower().strip()
            if fsize not in ("small", "medium", "large"):
                raise ValidationDomainError("Cỡ chữ không hợp lệ. Chọn small, medium, hoặc large.")
            updates.append("ui_font_size = ?")
            params.append(fsize)

        for bool_field in (
            "response_show_translation",
            "response_show_furigana",
            "response_highlight_grammar",
            "response_show_romaji",
            "response_grammar_breakdown",
            "response_audio_speech",
        ):
            val = getattr(req, bool_field)
            if val is not None:
                updates.append(f"{bool_field} = ?")
                params.append(1 if val else 0)

        if req.response_bilingual_mode is not None:
            bmode = req.response_bilingual_mode.strip().lower()
            if bmode not in ("interlinear", "parallel", "japanese_only"):
                raise ValidationDomainError(
                    "Chế độ hiển thị song ngữ không hợp lệ. Chọn interlinear, parallel hoặc japanese_only."
                )
            updates.append("response_bilingual_mode = ?")
            params.append(bmode)

        self._users.update_fields(user_id, updates, params)
        updated = self._users.get_preferences(user_id) or {}
        prefs = UserPreferencesModel.from_user_row(updated)
        return {
            "message": "Cập nhật tùy chọn giao diện thành công!",
            **prefs.model_dump(),
        }

    def get_connections(self, user_id: str) -> Dict[str, Any]:
        creds = self._users.get_auth_credentials(user_id)
        if not creds:
            raise NotFoundError("Không tìm thấy người dùng.")
        return {
            "has_password": bool(creds.get("hashed_password")),
            "connections": {},
        }
