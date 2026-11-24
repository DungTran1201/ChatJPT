"""Rules Management application service (SRP, DIP, atomic OCC, Anti-IDOR clone fix)."""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationDomainError,
)
from src.repositories.rule_repo import RuleRepository
from src.schemas.v1.rules import (
    PaginatedRuleResponse,
    ProjectRuleBindingRequest,
    RuleCreateRequest,
    RuleResponse,
    RuleStatusUpdateRequest,
    RuleUpdateRequest,
)


class RuleService:
    """Business logic for Rules Library CRUD, Anti-IDOR, System-rule protection, and OCC."""

    def __init__(self, rule_repo: Optional[RuleRepository] = None):
        self._rules = rule_repo or RuleRepository()

    @staticmethod
    def _parse_json_field(field_val: Any) -> List[str]:
        if not field_val:
            return []
        if isinstance(field_val, list):
            return [str(x) for x in field_val]
        if isinstance(field_val, str):
            try:
                parsed = json.loads(field_val)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed]
            except Exception:
                return []
        return []

    @classmethod
    def _map_row_to_response(cls, row: Dict[str, Any], current_user_id: str) -> RuleResponse:
        scope = row.get("scope") or "user"
        user_id = row.get("user_id")
        is_editable = (scope != "system") and (user_id == current_user_id)
        return RuleResponse(
            id=row["id"],
            user_id=user_id,
            name=row["name"],
            description=row.get("description"),
            content=row["content"],
            scope=scope,
            activation_mode=row.get("activation_mode") or "always_on",
            glob_patterns=cls._parse_json_field(row.get("glob_patterns")),
            tags=cls._parse_json_field(row.get("tags")),
            priority=row.get("priority", 50),
            status=row.get("status", "active"),
            version=row.get("version", 1),
            is_editable=is_editable,
            associated_projects_count=0,
            created_at=str(row.get("created_at") or ""),
            updated_at=str(row.get("updated_at") or ""),
            deleted_at=str(row.get("deleted_at")) if row.get("deleted_at") else None,
        )

    def _require_visible_rule(self, user_id: str, rule_id: str) -> Dict[str, Any]:
        row = self._rules.get_active_by_id(rule_id)
        if not row or (row.get("scope") != "system" and row.get("user_id") != user_id):
            raise NotFoundError(f"Quy tắc với ID '{rule_id}' không tồn tại hoặc đã bị xóa.")
        return row

    def _require_editable_rule(self, user_id: str, rule_id: str, *, action_label: str) -> Dict[str, Any]:
        row = self._rules.get_active_by_id(rule_id)
        if not row:
            raise NotFoundError(f"Quy tắc '{rule_id}' không tồn tại hoặc đã bị xóa.")
        if row.get("scope") == "system":
            raise ForbiddenError(action_label)
        if row.get("user_id") != user_id:
            raise NotFoundError(f"Quy tắc '{rule_id}' không tồn tại hoặc đã bị xóa.")
        return row

    def list_rules_instance(
        self,
        *,
        user_id: str,
        search: Optional[str] = None,
        scope: Optional[str] = "all",
        activation_mode: Optional[str] = None,
        status_filter: Optional[str] = "active",
        page: int = 1,
        limit: int = 20,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> PaginatedRuleResponse:
        safe_page = max(1, page)
        safe_limit = min(max(1, limit), 100)
        rows, total = self._rules.list_paginated(
            user_id=user_id,
            search=search,
            scope=scope,
            activation_mode=activation_mode,
            status_filter=status_filter,
            page=safe_page,
            limit=safe_limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        items = [self._map_row_to_response(r, user_id) for r in rows]
        total_pages = (total + safe_limit - 1) // safe_limit if total > 0 else 1
        return PaginatedRuleResponse(
            items=items,
            total=total,
            page=safe_page,
            limit=safe_limit,
            total_pages=total_pages,
        )

    def get_rule_instance(self, user_id: str, rule_id: str) -> RuleResponse:
        row = self._require_visible_rule(user_id, rule_id)
        return self._map_row_to_response(row, user_id)

    def create_rule_instance(self, user_id: str, req: RuleCreateRequest) -> RuleResponse:
        if req.activation_mode == "glob" and not req.glob_patterns:
            raise ValidationDomainError(
                "Khi chế độ kích hoạt là 'glob', danh sách glob_patterns bắt buộc phải có ít nhất 1 pattern."
            )
        if self._rules.exists_name_for_user(user_id, req.name):
            raise ConflictError(f"Tên quy tắc '{req.name}' đã tồn tại trong tài khoản của bạn. Vui lòng chọn tên khác.")

        new_id = f"rul_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        self._rules.create(
            {
                "id": new_id,
                "user_id": user_id,
                "name": req.name,
                "description": req.description,
                "content": req.content,
                "activation_mode": req.activation_mode,
                "glob_patterns": json.dumps(req.glob_patterns, ensure_ascii=False),
                "tags": json.dumps(req.tags, ensure_ascii=False),
                "priority": req.priority,
                "created_at": now,
                "updated_at": now,
            }
        )
        return self.get_rule_instance(user_id, new_id)

    def update_rule_instance(self, user_id: str, rule_id: str, req: RuleUpdateRequest) -> RuleResponse:
        existing = self._require_editable_rule(
            user_id,
            rule_id,
            action_label="Không thể chỉnh sửa Quy tắc Hệ thống (System Rule). Vui lòng nhân bản (Clone) để tạo bản sao riêng.",
        )

        current_version = existing.get("version", 1)
        if current_version != req.version:
            raise ConflictError(
                f"Quy tắc đã bị sửa đổi bởi một phiên khác (Phiên bản máy chủ: {current_version}, bạn gửi: {req.version}). Vui lòng tải lại dữ liệu mới nhất."
            )

        if req.name.lower() != existing["name"].lower() and self._rules.exists_name_for_user(
            user_id, req.name, exclude_id=rule_id
        ):
            raise ConflictError(f"Tên quy tắc '{req.name}' đã tồn tại trong tài khoản của bạn.")

        if req.activation_mode == "glob" and not req.glob_patterns:
            raise ValidationDomainError(
                "Khi chế độ kích hoạt là 'glob', danh sách glob_patterns bắt buộc phải có ít nhất 1 pattern."
            )

        now = datetime.now(timezone.utc).isoformat()
        new_status = req.status or existing.get("status", "active")
        if new_status not in ("active", "inactive", "archived"):
            raise ValidationDomainError("Trạng thái quy tắc không hợp lệ.")

        updated_rows = self._rules.update_with_occ(
            rule_id=rule_id,
            user_id=user_id,
            expected_version=req.version,
            fields={
                "name": req.name,
                "description": req.description,
                "content": req.content,
                "activation_mode": req.activation_mode,
                "glob_patterns": json.dumps(req.glob_patterns, ensure_ascii=False),
                "tags": json.dumps(req.tags, ensure_ascii=False),
                "priority": req.priority,
                "status": new_status,
                "updated_at": now,
            },
        )
        if updated_rows == 0:
            raise ConflictError("Quy tắc đã bị sửa đổi đồng thời bởi phiên khác. Vui lòng tải lại.")

        return self.get_rule_instance(user_id, rule_id)

    def update_status_instance(self, user_id: str, rule_id: str, new_status: str) -> RuleResponse:
        self._require_editable_rule(
            user_id,
            rule_id,
            action_label="Không thể thay đổi trạng thái của Quy tắc Hệ thống.",
        )
        now = datetime.now(timezone.utc).isoformat()
        self._rules.update_status(rule_id, user_id, new_status, now)
        return self.get_rule_instance(user_id, rule_id)

    def clone_rule_instance(self, user_id: str, rule_id: str) -> RuleResponse:
        # Enforces Anti-IDOR: user can only clone system rules or their own rules
        source = self._require_visible_rule(user_id, rule_id)

        base_name = source["name"].strip()
        copy_name = f"{base_name} (Copy)"
        for idx in range(2, 102):
            if not self._rules.exists_name_for_user(user_id, copy_name):
                break
            copy_name = f"{base_name} (Copy {idx})"

        new_id = f"rul_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        self._rules.create(
            {
                "id": new_id,
                "user_id": user_id,
                "name": copy_name[:100],
                "description": source.get("description"),
                "content": source["content"],
                "activation_mode": source.get("activation_mode", "always_on"),
                "glob_patterns": source.get("glob_patterns", "[]"),
                "tags": source.get("tags", "[]"),
                "priority": source.get("priority", 50),
                "created_at": now,
                "updated_at": now,
            }
        )
        return self.get_rule_instance(user_id, new_id)

    def delete_rule_instance(self, user_id: str, rule_id: str, force: bool = False) -> Dict[str, Any]:
        self._require_editable_rule(
            user_id,
            rule_id,
            action_label="Không thể xóa Quy tắc Hệ thống.",
        )
        now = datetime.now(timezone.utc).isoformat()
        self._rules.soft_delete(rule_id, user_id, now)
        return {
            "message": "Đã xóa mềm quy tắc thành công.",
            "id": rule_id,
            "deleted_at": now,
            "detached_projects_count": 0,
        }

    # ------------------------------------------------------------------
    # Backward-compatible classmethod facade
    # ------------------------------------------------------------------
    @classmethod
    def list_rules(cls, user_id: str, **kwargs: Any) -> PaginatedRuleResponse:
        return _default_rule_service.list_rules_instance(user_id=user_id, **kwargs)

    @classmethod
    def get_rule(cls, user_id: str, rule_id: str) -> RuleResponse:
        return _default_rule_service.get_rule_instance(user_id, rule_id)

    @classmethod
    def create_rule(cls, user_id: str, req: RuleCreateRequest) -> RuleResponse:
        return _default_rule_service.create_rule_instance(user_id, req)

    @classmethod
    def update_rule(cls, user_id: str, rule_id: str, req: RuleUpdateRequest) -> RuleResponse:
        return _default_rule_service.update_rule_instance(user_id, rule_id, req)

    @classmethod
    def update_status(cls, user_id: str, rule_id: str, new_status: str) -> RuleResponse:
        return _default_rule_service.update_status_instance(user_id, rule_id, new_status)

    @classmethod
    def clone_rule(cls, user_id: str, rule_id: str) -> RuleResponse:
        return _default_rule_service.clone_rule_instance(user_id, rule_id)

    @classmethod
    def delete_rule(cls, user_id: str, rule_id: str, force: bool = False) -> Dict[str, Any]:
        return _default_rule_service.delete_rule_instance(user_id, rule_id, force=force)


_default_rule_service = RuleService()

__all__ = [
    "RuleCreateRequest",
    "RuleUpdateRequest",
    "RuleStatusUpdateRequest",
    "RuleResponse",
    "PaginatedRuleResponse",
    "ProjectRuleBindingRequest",
    "RuleService",
]
