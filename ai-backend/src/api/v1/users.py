"""Thin HTTP router for User Management endpoints (/api/v1/users)."""

from fastapi import APIRouter, Depends, Request, Response

from src.core.security import (
    auth_rate_limiter,
    build_auth_cookie_kwargs,
    get_current_user,
)
from src.dependencies import get_user_service
from src.schemas.v1.users import (
    ChangeEmailRequest,
    ChangePasswordRequest,
    UpdateAvatarRequest,
    UpdatePreferencesRequest,
    UpdateProfileRequest,
)
from src.services.user_service import UserService

users_router = APIRouter(prefix="/users", tags=["User Management"])


@users_router.get("/me")
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    return user_service.get_my_profile(current_user)


@users_router.patch("/me/profile")
async def update_profile(
    req: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    return user_service.update_profile(current_user["id"], req)


@users_router.patch("/me/avatar")
async def update_avatar(
    req: UpdateAvatarRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    return user_service.update_avatar(current_user["id"], req)


@users_router.post("/me/change-email")
async def change_email(
    req: ChangeEmailRequest,
    response: Response,
    raw_request: Request,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    client_ip = raw_request.client.host if raw_request.client else "127.0.0.1"
    auth_rate_limiter.check(client_ip)
    payload, new_token = user_service.change_email(current_user, req)
    response.set_cookie(**build_auth_cookie_kwargs(new_token))
    return payload


@users_router.post("/me/change-password")
async def change_password(
    req: ChangePasswordRequest,
    response: Response,
    raw_request: Request,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    client_ip = raw_request.client.host if raw_request.client else "127.0.0.1"
    auth_rate_limiter.check(client_ip)
    payload, new_token = user_service.change_password(current_user["id"], req)
    response.set_cookie(**build_auth_cookie_kwargs(new_token))
    return payload


@users_router.patch("/me/preferences")
async def update_preferences(
    req: UpdatePreferencesRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    return user_service.update_preferences(current_user["id"], req)


@users_router.get("/me/connections")
async def get_connections(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    return user_service.get_connections(current_user["id"])
