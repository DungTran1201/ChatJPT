"""System Prompt / Sensei Guidance application service (SRP, DIP, unified import)."""

import logging
import uuid
from typing import Any, Callable, Dict, Optional

from src.core.attachment_storage import delete_attachment_file
from src.core.exceptions import BadRequestError, ConflictError, DomainError, NotFoundError
from src.models.v1.prompt import SystemPromptEntity
from src.repositories.attachment_repo import AttachmentRepository
from src.repositories.prompt_repo import PromptRepository
from src.schemas.v1.prompts import (
    SystemPromptCreateRequest,
    SystemPromptDetailResponse,
    SystemPromptListResponse,
    SystemPromptSummaryResponse,
    SystemPromptUpdateRequest,
)

logger = logging.getLogger("system_prompts")


class PromptService:
    """Manages Sensei personas, preset copy-on-write forks, cloning, attachments, and imports."""

    def __init__(
        self,
        prompt_repo: PromptRepository,
        attachment_repo: AttachmentRepository,
        file_deleter: Optional[Callable[[str], bool]] = None,
    ):
        self._prompts = prompt_repo
        self._atts = attachment_repo
        self._delete_file = file_deleter or delete_attachment_file

    def list_prompts(
        self,
        *,
        user_id: str,
        q: Optional[str] = None,
        level: Optional[str] = None,
        sort: str = "level_asc",
    ) -> SystemPromptListResponse:
        rows = self._prompts.list_visible(user_id=user_id, q=q, level=level, sort=sort)
        items = [SystemPromptSummaryResponse.from_entity(SystemPromptEntity.from_prompt_row(r)) for r in rows]
        return SystemPromptListResponse(items=items, total=len(items))

    def create_prompt(self, user_id: str, payload: SystemPromptCreateRequest) -> SystemPromptDetailResponse:
        name = payload.name.strip()
        if self._prompts.exists_name_for_user(user_id, name):
            raise ConflictError(
                "Bạn đã có một Sensei mang tên này. Vui lòng chọn tên khác.",
                error_code="PROMPT_NAME_CONFLICT",
                structured=True,
            )

        prompt_id = f"sp_{uuid.uuid4().hex}"
        avatar = payload.avatar_url or SystemPromptEntity.default_avatar_url(prompt_id)

        row = self._prompts.create(
            {
                "id": prompt_id,
                "user_id": user_id,
                "name": name,
                "description": payload.description,
                "content": payload.content,
                "age": payload.age or 25,
                "gender": payload.gender or "female",
                "japanese_level": payload.japanese_level or "N5",
                "personality": payload.personality,
                "teaching_style": payload.teaching_style,
                "catchphrase": payload.catchphrase,
                "hobbies": payload.hobbies,
                "avatar_url": avatar,
                "voice_id": payload.voice_id,
                "is_default": bool(payload.is_default),
            }
        )
        if not row:
            raise DomainError("Không thể lưu Sensei vào cơ sở dữ liệu.", error_code="DB_INSERT_FAILED", structured=True)

        logger.info("Created Sensei: id=%s, user_id=%s, name='%s'", prompt_id, user_id, name)
        return SystemPromptDetailResponse.from_entity(
            SystemPromptEntity.from_prompt_row(row, fallback_avatar=avatar)
        )

    def get_detail(self, prompt_id: str, user_id: str) -> SystemPromptDetailResponse:
        row = self._prompts.get_visible(prompt_id, user_id)
        if not row:
            raise NotFoundError(
                "Sensei không tồn tại hoặc bạn không có quyền truy cập.",
                error_code="PROMPT_NOT_FOUND",
                structured=True,
            )
        atts = self._atts.list_by_prompt(prompt_id)
        return SystemPromptDetailResponse.from_entity(
            SystemPromptEntity.from_prompt_row(
                row,
                fallback_avatar=SystemPromptEntity.default_avatar_url(row["id"]),
                attachments=atts,
            )
        )

    def list_prompt_attachments(self, prompt_id: str, user_id: str) -> Dict[str, Any]:
        row = self._prompts.get_visible(prompt_id, user_id)
        if not row:
            raise NotFoundError(
                "Sensei không tồn tại hoặc bạn không có quyền truy cập.",
                error_code="PROMPT_NOT_FOUND",
                structured=True,
            )
        atts = self._atts.list_by_prompt(prompt_id)
        return {"items": atts, "total": len(atts)}

    def update_prompt(
        self,
        prompt_id: str,
        user_id: str,
        payload: SystemPromptUpdateRequest,
    ) -> SystemPromptDetailResponse:
        name = payload.name.strip()
        existing = self._prompts.get_visible(prompt_id, user_id)
        if not existing:
            raise NotFoundError(
                "Sensei không tồn tại hoặc bạn không có quyền truy cập.",
                error_code="PROMPT_NOT_FOUND",
                structured=True,
            )

        if self._prompts.exists_name_for_user(user_id, name, exclude_id=prompt_id):
            raise ConflictError(
                "Bạn đã có một Sensei khác mang tên này. Vui lòng chọn tên khác.",
                error_code="PROMPT_NAME_CONFLICT",
                structured=True,
            )

        if existing.get("is_system_preset"):
            fork_id = f"sp_custom_{uuid.uuid4().hex[:12]}"
            row = self._prompts.create(
                {
                    "id": fork_id,
                    "user_id": user_id,
                    "name": name,
                    "description": payload.description,
                    "content": payload.content,
                    "age": payload.age or existing.get("age", 25),
                    "gender": payload.gender or existing.get("gender", "female"),
                    "japanese_level": payload.japanese_level or existing.get("japanese_level", "N5"),
                    "personality": payload.personality,
                    "teaching_style": payload.teaching_style,
                    "catchphrase": payload.catchphrase,
                    "hobbies": payload.hobbies,
                    "avatar_url": payload.avatar_url or existing.get("avatar_url"),
                    "voice_id": payload.voice_id or existing.get("voice_id"),
                    "is_default": bool(payload.is_default),
                }
            )
        else:
            voice_to_set = payload.voice_id if payload.voice_id is not None else existing.get("voice_id")
            row = self._prompts.update(
                prompt_id,
                user_id,
                {
                    "name": name,
                    "description": payload.description,
                    "content": payload.content,
                    "age": payload.age or 25,
                    "gender": payload.gender or "female",
                    "japanese_level": payload.japanese_level or "N5",
                    "personality": payload.personality,
                    "teaching_style": payload.teaching_style,
                    "catchphrase": payload.catchphrase,
                    "hobbies": payload.hobbies,
                    "avatar_url": payload.avatar_url,
                    "voice_id": voice_to_set,
                    "is_default": bool(payload.is_default),
                },
            )
        return SystemPromptDetailResponse.from_entity(SystemPromptEntity.from_prompt_row(row or existing))

    def delete_prompt(self, prompt_id: str, user_id: str) -> Dict[str, Any]:
        existing = self._prompts.get_visible(prompt_id, user_id)
        if not existing:
            raise NotFoundError(
                "Sensei không tồn tại hoặc bạn không có quyền truy cập.",
                error_code="PROMPT_NOT_FOUND",
                structured=True,
            )
        if existing.get("is_system_preset"):
            raise BadRequestError(
                "Không thể xóa Sensei mẫu được bảo vệ của hệ thống.",
                error_code="CANNOT_DELETE_PRESET",
                structured=True,
            )

        att_paths = self._prompts.delete_and_collect_attachment_paths(prompt_id, user_id)
        for path in att_paths:
            self._delete_file(path)

        return {"success": True, "message": "Đã xóa Sensei thành công.", "deleted_id": prompt_id}

    def clone_prompt(self, prompt_id: str, user_id: str) -> SystemPromptDetailResponse:
        origin = self._prompts.get_visible(prompt_id, user_id)
        if not origin:
            raise NotFoundError(
                "Sensei không tồn tại hoặc bạn không có quyền truy cập.",
                error_code="PROMPT_NOT_FOUND",
                structured=True,
            )

        clone_name = self._next_unique_copy_name(user_id, origin["name"])
        new_id = f"sp_{uuid.uuid4().hex}"
        row = self._prompts.create(
            {
                "id": new_id,
                "user_id": user_id,
                "name": clone_name,
                "description": origin.get("description"),
                "content": origin["content"],
                "age": origin.get("age", 25),
                "gender": origin.get("gender", "female"),
                "japanese_level": origin.get("japanese_level", "N5"),
                "personality": origin.get("personality"),
                "teaching_style": origin.get("teaching_style"),
                "catchphrase": origin.get("catchphrase"),
                "hobbies": origin.get("hobbies"),
                "avatar_url": origin.get("avatar_url"),
                "voice_id": origin.get("voice_id"),
                "is_default": False,
            }
        )
        return SystemPromptDetailResponse.from_entity(
            SystemPromptEntity.from_prompt_row(row, force_system_preset=False)
        )

    def _next_unique_copy_name(self, user_id: str, origin_name: str, max_attempts: int = 100) -> str:
        base_name = origin_name
        candidate = f"{base_name[: 100 - len(' (Copy)')]} (Copy)"
        if not self._prompts.exists_name_for_user(user_id, candidate):
            return candidate
        for counter in range(2, max_attempts + 2):
            suffix = f" (Copy {counter})"
            candidate = f"{base_name[: 100 - len(suffix)]}{suffix}"
            if not self._prompts.exists_name_for_user(user_id, candidate):
                return candidate
        suffix = f" ({uuid.uuid4().hex[:6]})"
        return f"{base_name[: 100 - len(suffix)]}{suffix}"
