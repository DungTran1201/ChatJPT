"""AI Model Catalog application service (SRP, DIP, reuses ProviderRegistry probes)."""

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.core.exceptions import (
    BadRequestError,
    ConflictError,
    ExternalServiceError,
    NotFoundError,
    ValidationDomainError,
)
from src.models.v1.ai_model import AIModelEntity, VALID_LLM_PROVIDERS
from src.repositories.model_repo import ModelRepository
from src.schemas.v1.models import CreateModelRequest, SetDefaultModelRequest, UpdateModelRequest
from src.services.credential_service import CredentialService
from src.services.provider_registry import (
    ProviderRegistry,
    provider_registry,
    redact_secrets_from_text,
)


class ModelService:
    """Handles AI model catalog CRUD, search, activation lifecycle, default guard, and ping."""

    def __init__(
        self,
        model_repo: ModelRepository,
        credential_service: CredentialService,
        registry: Optional[ProviderRegistry] = None,
    ):
        self._models = model_repo
        self._creds = credential_service
        self._registry = registry or provider_registry

    def _format_record(self, row: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        has_key = (
            True
            if row["id"] == "offline-semantic-cache"
            else self._creds.check_provider_configured(row["provider"], user_id=user_id)
        )
        return AIModelEntity.from_model_row(row, has_api_key=has_key).to_api_dict()

    def list_models(self, status_filter: str = "ALL", user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        rows = self._models.list_by_status(status_filter)
        return [self._format_record(r, user_id=user_id) for r in rows]

    def get_model(self, model_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        row = self._models.get_by_id(model_id)
        if not row:
            raise NotFoundError(f"Không tìm thấy mô hình '{model_id}'.")
        return self._format_record(row, user_id=user_id)

    def create_model(self, req: CreateModelRequest, user_id: Optional[str] = None) -> Dict[str, Any]:
        if req.max_tokens > req.context_window:
            raise ValidationDomainError(
                f"Tham số max_tokens ({req.max_tokens}) không được vượt quá context_window ({req.context_window}) (BR-024)."
            )

        provider_clean = req.provider.lower().strip()
        if provider_clean not in VALID_LLM_PROVIDERS:
            raise ValidationDomainError(
                f"Nhà cung cấp không hợp lệ '{req.provider}'. Phải là một trong: {', '.join(VALID_LLM_PROVIDERS)}."
            )

        model_id = req.id.strip()
        if self._models.get_by_id(model_id):
            raise ConflictError(f"Mô hình với mã định danh '{model_id}' đã tồn tại trong hệ thống (BR-022).")

        created = self._models.create(
            model_id=model_id,
            name=req.name.strip(),
            provider=provider_clean,
            context_window=req.context_window,
            max_tokens=req.max_tokens,
            supports_streaming=req.supports_streaming,
        )
        record = self._format_record(created, user_id=user_id)
        record["message"] = "Đăng ký mô hình mới thành công."
        return record

    def search_models(
        self,
        *,
        q: Optional[str] = None,
        provider: Optional[str] = "ALL",
        status_filter: Optional[str] = "ALL",
        has_api_key: Optional[bool] = None,
        is_default: Optional[bool] = None,
        sort: Optional[str] = "name_asc",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        rows = self._models.search(
            q=q,
            provider=provider,
            status_filter=status_filter,
            is_default=is_default,
            sort=sort,
        )
        items = [self._format_record(r, user_id=user_id) for r in rows]
        if has_api_key is not None:
            items = [item for item in items if item["has_api_key"] == has_api_key]

        execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "total": len(items),
            "execution_time_ms": execution_time_ms,
            "items": items,
        }

    def set_default_model(self, req: SetDefaultModelRequest) -> Dict[str, Any]:
        model = self._models.get_by_id(req.model_id)
        if not model:
            raise NotFoundError(f"Không tìm thấy mô hình với mã định danh '{req.model_id}'.")

        if model["status"] != "ACTIVE":
            raise BadRequestError(
                f"Mô hình '{model['name']}' đang ở trạng thái {model['status']}. Chỉ có thể đặt mô hình ACTIVE làm mặc định (BR-013)."
            )

        self._models.set_default_atomic(req.model_id)
        return {
            "default_model": req.model_id,
            "message": f"Đã thiết lập '{model['name']}' làm mô hình mặc định thành công.",
        }

    def update_model(
        self,
        model_id: str,
        req: UpdateModelRequest,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        model = self._models.get_by_id(model_id)
        if not model:
            raise NotFoundError(f"Không tìm thấy mô hình với mã định danh '{model_id}'.")

        new_name = req.name.strip() if req.name is not None else model["name"]
        new_cw = req.context_window if req.context_window is not None else model["context_window"]
        new_mt = req.max_tokens if req.max_tokens is not None else model["max_tokens"]
        new_streaming = req.supports_streaming if req.supports_streaming is not None else bool(model["supports_streaming"])

        if new_cw < 1000 or new_mt < 256:
            raise ValidationDomainError("Vi phạm ngưỡng an toàn: context_window >= 1000 và max_tokens >= 256 (BR-024).")
        if new_mt > new_cw:
            raise ValidationDomainError(
                f"Tham số max_tokens ({new_mt}) không được vượt quá context_window ({new_cw}) (BR-024)."
            )

        updated = self._models.update_config(
            model_id=model_id,
            name=new_name,
            context_window=new_cw,
            max_tokens=new_mt,
            supports_streaming=new_streaming,
        )
        record = self._format_record(updated or model, user_id=user_id)
        record["message"] = "Cập nhật cấu hình mô hình thành công."
        return record

    def archive_model(self, model_id: str) -> Dict[str, Any]:
        model = self._models.get_by_id(model_id)
        if not model:
            raise NotFoundError(f"Không tìm thấy mô hình với mã định danh '{model_id}'.")

        if bool(model["is_default"]):
            raise BadRequestError(
                f"Không thể lưu trữ mô hình '{model['name']}' vì đây là mô hình mặc định của hệ thống. Hãy chọn mô hình khác làm mặc định trước (BR-023)."
            )

        self._models.update_status(model_id, "ARCHIVED")
        return {
            "model_id": model_id,
            "status": "ARCHIVED",
            "message": f"Đã chuyển mô hình '{model['name']}' vào trạng thái lưu trữ an toàn.",
        }

    async def test_connection(self, model_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        model = self._models.get_by_id(model_id)
        if not model:
            raise NotFoundError(f"Không tìm thấy mô hình '{model_id}'.")

        provider = model["provider"]
        effective_key = self._creds.resolve_effective_key(user_id, provider)
        if not effective_key:
            raise BadRequestError(f"Chưa cấu hình API Key cho nhà cung cấp '{provider}' (BR-014).")

        start_time = time.perf_counter()
        tested_at_str = datetime.now(timezone.utc).isoformat()
        try:
            await self._registry.probe(provider, effective_key, model_id=model_id)
            latency_ms = max(1, int((time.perf_counter() - start_time) * 1000))
        except Exception as exc:
            err_msg = redact_secrets_from_text(str(exc), [effective_key])
            raise ExternalServiceError(f"Lỗi kết nối tới nhà cung cấp {provider}: {err_msg}")

        self._models.record_latency(model_id, latency_ms)
        return {
            "model_id": model_id,
            "healthy": True,
            "latency_ms": latency_ms,
            "message": f"Kết nối thành công với nhà cung cấp {provider.title()} ({model['name']}).",
            "tested_at": tested_at_str,
        }

    def activate_model(self, model_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        model = self._models.get_by_id(model_id)
        if not model:
            raise NotFoundError(f"Không tìm thấy mô hình '{model_id}'.")

        provider = model["provider"]
        if not self._creds.check_provider_configured(provider, user_id=user_id):
            raise BadRequestError(
                f"Không thể kích hoạt mô hình: Chưa cấu hình API Key cho nhà cung cấp '{provider}' trong file .env (BR-014)."
            )

        self._models.update_status(model_id, "ACTIVE")
        return {
            "model_id": model_id,
            "status": "ACTIVE",
            "message": f"Mô hình '{model['name']}' đã được kích hoạt thành công.",
        }

    def deactivate_model(self, model_id: str) -> Dict[str, Any]:
        model = self._models.get_by_id(model_id)
        if not model:
            raise NotFoundError(f"Không tìm thấy mô hình '{model_id}'.")

        if bool(model["is_default"]):
            raise BadRequestError(
                f"Không thể hủy kích hoạt '{model['name']}' vì đây là mô hình mặc định của hệ thống. Hãy chọn mô hình mặc định khác trước (BR-013)."
            )

        self._models.update_status(model_id, "INACTIVE")
        return {
            "model_id": model_id,
            "status": "INACTIVE",
            "message": f"Mô hình '{model['name']}' đã được hủy kích hoạt thành công.",
        }
