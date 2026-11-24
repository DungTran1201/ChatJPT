"""Thin HTTP router for BYOK API Keys & Provider Integrations (/api/v1/settings/api-keys)."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from src.core.security import connection_test_limiter, get_current_user, is_admin_user
from src.schemas.v1.api_keys import (
    ProviderKeyStatusResponse,
    SetApiKeyRequest,
    TestApiKeyRequest,
    TestApiKeyResponse,
    UpdateSystemEnvRequest,
)
from src.services.credential_service import (
    ALLOWLISTED_SYSTEM_ENV_VARS,
    SUPPORTED_PROVIDERS,
    CredentialService,
    canonicalize_provider,
    redact_secrets_from_text,
)

api_keys_router = APIRouter(prefix="/settings/api-keys", tags=["Settings - API Keys & Integrations"])


@api_keys_router.get("", response_model=List[ProviderKeyStatusResponse], summary="Liệt kê trạng thái các khóa API của người dùng")
@api_keys_router.get("/", response_model=List[ProviderKeyStatusResponse], include_in_schema=False)
async def list_user_api_keys(current_user: dict = Depends(get_current_user)):
    return CredentialService.get_user_keys_status(current_user["id"])


@api_keys_router.put("/{provider}", response_model=Dict[str, Any], summary="Cập nhật hoặc lưu khóa API cá nhân")
async def save_user_api_key(
    provider: str,
    req: SetApiKeyRequest,
    current_user: dict = Depends(get_current_user),
):
    canon = canonicalize_provider(provider)
    if not canon or canon not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nhà cung cấp '{provider}' không nằm trong danh mục allowlist được hỗ trợ.",
        )

    try:
        res = CredentialService.set_user_key(current_user["id"], canon, req.api_key)
        return {
            "status": "success",
            "provider": canon,
            "source": "PERSONAL",
            "masked_hint": res["masked_hint"],
            "validation_status": res["validation_status"],
            "message": f"Đã lưu khóa API cho nhà cung cấp {SUPPORTED_PROVIDERS[canon]['name']} thành công (áp dụng tức thì).",
        }
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as exc:
        clean_msg = redact_secrets_from_text(str(exc), [req.api_key])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lưu trữ an toàn khóa API: {clean_msg}",
        )


@api_keys_router.delete("/{provider}", response_model=Dict[str, Any], summary="Xóa hoặc hoàn tác khóa API cá nhân")
async def delete_user_api_key(
    provider: str,
    current_user: dict = Depends(get_current_user),
):
    canon = canonicalize_provider(provider)
    if not canon or canon not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nhà cung cấp '{provider}' không nằm trong danh mục allowlist được hỗ trợ.",
        )

    try:
        res = CredentialService.delete_user_key(current_user["id"], canon)
        p_name = SUPPORTED_PROVIDERS[canon]["name"]
        msg = (
            f"Đã xóa khóa cá nhân cho {p_name}. Hệ thống sẽ sử dụng cấu hình mặc định server."
            if res["has_system_key"]
            else f"Đã xóa khóa cá nhân cho {p_name}. Nhà cung cấp hiện đang ở trạng thái chưa cấu hình."
        )
        return {
            "status": "success",
            "provider": canon,
            "source": res["source"],
            "is_configured": res["is_configured"],
            "masked_hint": res["masked_hint"],
            "message": msg,
        }
    except Exception as exc:
        clean_msg = redact_secrets_from_text(str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xóa khóa cá nhân: {clean_msg}",
        )


@api_keys_router.post("/{provider}/test", response_model=TestApiKeyResponse, summary="Kiểm tra kết nối tới nhà cung cấp")
async def test_provider_connection(
    provider: str,
    req: Optional[TestApiKeyRequest] = None,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]
    connection_test_limiter.check(user_id)

    canon = canonicalize_provider(provider)
    if not canon or canon not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nhà cung cấp '{provider}' không nằm trong danh mục allowlist được hỗ trợ.",
        )

    candidate = req.candidate_key if req else None
    try:
        res = await CredentialService.validate_connection(
            provider=canon,
            user_id=user_id,
            candidate_key=candidate,
        )
        return TestApiKeyResponse(**res)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=redact_secrets_from_text(str(val_err), [candidate]),
        )
    except Exception as exc:
        clean_err = redact_secrets_from_text(str(exc), [candidate])
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Lỗi xác thực kết nối: {clean_err}",
        )


@api_keys_router.post("/system", response_model=Dict[str, Any], summary="Cập nhật cấu hình .env toàn cục (chỉ dành cho Quản trị viên)")
async def update_system_env(
    req: UpdateSystemEnvRequest,
    current_user: dict = Depends(get_current_user),
):
    if not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền quản trị viên để chỉnh sửa cấu hình môi trường toàn cục (.env).",
        )

    var_name = req.env_var.strip().upper()
    if var_name not in ALLOWLISTED_SYSTEM_ENV_VARS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Biến môi trường '{var_name}' không nằm trong danh mục được phép chỉnh sửa qua giao diện.",
        )

    try:
        res = CredentialService.update_system_env_variable(var_name, req.value)
        return {
            "status": "success",
            "env_var": res["env_var"],
            "restart_required": res["restart_required"],
            "message": res["message"],
        }
    except ValueError as v_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(v_err))
    except Exception as exc:
        clean_msg = redact_secrets_from_text(str(exc), [req.value])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi cập nhật an toàn file .env: {clean_msg}",
        )
