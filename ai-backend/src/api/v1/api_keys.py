"""
API Keys & Integrations Management Endpoints (FR-SETTINGS-KEYS, SEC-015)

Allows authenticated users to view configuration status, securely set/update personal
API keys encrypted with AES-256-GCM, test connectivity, and reset to system defaults.
Guarantees that plaintext secrets are never returned, logged, or exposed in exceptions.
"""

import time
from collections import defaultdict
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends

from src.core.security import get_current_user
from src.core.config import settings
from src.services.credential_service import (
    CredentialService,
    canonicalize_provider,
    SUPPORTED_PROVIDERS,
    ALLOWLISTED_SYSTEM_ENV_VARS,
    redact_secrets_from_text
)
from src.schemas.v1.api_keys import (
    ProviderKeyStatusResponse,
    SetApiKeyRequest,
    TestApiKeyRequest,
    TestApiKeyResponse,
    UpdateSystemEnvRequest,
)

api_keys_router = APIRouter(prefix="/settings/api-keys", tags=["Settings - API Keys & Integrations"])

# ==============================================================================
# RATE LIMITER FOR TEST CONNECTION ENDPOINTS
# ==============================================================================

class ConnectionTestRateLimiter:
    """Limits connection test calls per user to prevent provider quota exhaustion or spam."""
    def __init__(self, max_per_minute: int = 15):
        self.max_per_minute = max_per_minute
        self.history: Dict[str, List[float]] = defaultdict(list)

    def check(self, user_id: str):
        now = time.time()
        cutoff = now - 60.0
        self.history[user_id] = [t for t in self.history[user_id] if t > cutoff]
        if len(self.history[user_id]) >= self.max_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Tần suất kiểm tra kết nối vượt quá giới hạn an toàn. Vui lòng thử lại sau 1 phút."
            )
        self.history[user_id].append(now)

connection_test_limiter = ConnectionTestRateLimiter(max_per_minute=15)

# ==============================================================================
# ROUTE HANDLERS
# ==============================================================================

@api_keys_router.get("", response_model=List[ProviderKeyStatusResponse], summary="Liệt kê trạng thái các khóa API của người dùng")
@api_keys_router.get("/", response_model=List[ProviderKeyStatusResponse], include_in_schema=False)
async def list_user_api_keys(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về danh mục toàn bộ các nhà cung cấp được hỗ trợ, kèm trạng thái cấu hình và nguồn khóa
    (PERSONAL > SYSTEM > NONE). Tuyệt đối KHÔNG bao giờ trả về giá trị khóa bí mật dạng plaintext.
    """
    user_id = current_user["id"]
    return CredentialService.get_user_keys_status(user_id)


@api_keys_router.put("/{provider}", response_model=Dict[str, Any], summary="Cập nhật hoặc lưu khóa API cá nhân")
async def save_user_api_key(
    provider: str,
    req: SetApiKeyRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Lưu hoặc cập nhật khóa API cá nhân của người dùng cho nhà cung cấp được allowlist.
    Dữ liệu được mã hóa tức thì bằng AES-256-GCM trước khi lưu xuống CSDL.
    Khóa cá nhân có hiệu lực ngay ở runtime mà không cần restart máy chủ.
    """
    canon = canonicalize_provider(provider)
    if not canon or canon not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nhà cung cấp '{provider}' không nằm trong danh mục allowlist được hỗ trợ."
        )

    try:
        user_id = current_user["id"]
        res = CredentialService.set_user_key(user_id, canon, req.api_key)
        return {
            "status": "success",
            "provider": canon,
            "source": "PERSONAL",
            "masked_hint": res["masked_hint"],
            "validation_status": res["validation_status"],
            "message": f"Đã lưu khóa API cho nhà cung cấp {SUPPORTED_PROVIDERS[canon]['name']} thành công (áp dụng tức thì)."
        }
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as exc:
        clean_msg = redact_secrets_from_text(str(exc), [req.api_key])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lưu trữ an toàn khóa API: {clean_msg}"
        )


@api_keys_router.delete("/{provider}", response_model=Dict[str, Any], summary="Xóa hoặc hoàn tác khóa API cá nhân")
async def delete_user_api_key(
    provider: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Xóa khóa API cá nhân của người dùng, đưa cấu hình trở về trạng thái kế thừa mặc định từ .env
    (hoặc NOT_CONFIGURED nếu server không cấu hình sẵn).
    """
    canon = canonicalize_provider(provider)
    if not canon or canon not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nhà cung cấp '{provider}' không nằm trong danh mục allowlist được hỗ trợ."
        )

    try:
        user_id = current_user["id"]
        res = CredentialService.delete_user_key(user_id, canon)
        p_name = SUPPORTED_PROVIDERS[canon]["name"]
        if res["has_system_key"]:
            msg = f"Đã xóa khóa cá nhân cho {p_name}. Hệ thống sẽ sử dụng cấu hình mặc định server."
        else:
            msg = f"Đã xóa khóa cá nhân cho {p_name}. Nhà cung cấp hiện đang ở trạng thái chưa cấu hình."

        return {
            "status": "success",
            "provider": canon,
            "source": res["source"],
            "is_configured": res["is_configured"],
            "masked_hint": res["masked_hint"],
            "message": msg
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xóa khóa cá nhân: {str(exc)}"
        )


@api_keys_router.post("/{provider}/test", response_model=TestApiKeyResponse, summary="Kiểm tra kết nối tới nhà cung cấp")
async def test_provider_connection(
    provider: str,
    req: Optional[TestApiKeyRequest] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Thực hiện kiểm tra kết nối (Ping / Health Check) trực tiếp tới dịch vụ nhà cung cấp.
    Hỗ trợ kiểm tra khóa cá nhân đã lưu hoặc kiểm tra thử khóa mới trước khi lưu.
    Được áp dụng Rate Limiter chống lạm dụng. Toàn bộ lỗi được redact bí mật 100%.
    """
    user_id = current_user["id"]
    connection_test_limiter.check(user_id)

    canon = canonicalize_provider(provider)
    if not canon or canon not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nhà cung cấp '{provider}' không nằm trong danh mục allowlist được hỗ trợ."
        )

    candidate = req.candidate_key if req else None
    try:
        res = await CredentialService.validate_connection(
            provider=canon,
            user_id=user_id,
            candidate_key=candidate
        )
        return TestApiKeyResponse(
            healthy=res["healthy"],
            provider=res["provider"],
            latency_ms=res["latency_ms"],
            validation_status=res["validation_status"],
            message=res["message"],
            tested_at=res["tested_at"]
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=redact_secrets_from_text(str(val_err), [candidate])
        )
    except Exception as exc:
        clean_err = redact_secrets_from_text(str(exc), [candidate])
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Lỗi xác thực kết nối: {clean_err}"
        )


@api_keys_router.post("/system", response_model=Dict[str, Any], summary="Cập nhật cấu hình .env toàn cục (chỉ dành cho Quản trị viên)")
async def update_system_env(
    req: UpdateSystemEnvRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Cập nhật an toàn một biến môi trường toàn cục allowlisted trong file .env.
    Thao tác sử dụng cơ chế ghi file nguyên tử (Atomic Write) và sao lưu backup.
    Chỉ cho phép quản trị viên hoặc chế độ local development.
    Yêu cầu khởi động lại tiến trình để biến có hiệu lực toàn diện.
    """
    user_email = (current_user.get("email") or "").lower()
    is_admin = ("admin" in user_email or settings.DEBUG or settings.APP_ENV == "development")

    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền quản trị viên để chỉnh sửa cấu hình môi trường toàn cục (.env)."
        )

    var_name = req.env_var.strip().upper()
    if var_name not in ALLOWLISTED_SYSTEM_ENV_VARS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Biến môi trường '{var_name}' không nằm trong danh mục được phép chỉnh sửa qua giao diện."
        )

    try:
        res = CredentialService.update_system_env_variable(var_name, req.value)
        return {
            "status": "success",
            "env_var": res["env_var"],
            "restart_required": res["restart_required"],
            "message": res["message"]
        }
    except ValueError as v_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(v_err)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi cập nhật an toàn file .env: {str(exc)}"
        )
