"""Thin HTTP router for Authentication endpoints (/api/v1/auth)."""

from fastapi import APIRouter, Depends, Request, Response, status

from src.core.security import (
    auth_rate_limiter,
    build_auth_cookie_kwargs,
    get_current_user,
)
from src.dependencies import get_auth_service
from src.schemas.v1.auth import LoginRequest, RegisterRequest
from src.services.auth_service import AuthService

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterRequest,
    raw_request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    client_ip = raw_request.client.host if raw_request.client else "127.0.0.1"
    auth_rate_limiter.check(client_ip)
    return auth_service.register(req)


@auth_router.post("/login")
async def login(
    req: LoginRequest,
    response: Response,
    raw_request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    client_ip = raw_request.client.host if raw_request.client else "127.0.0.1"
    auth_rate_limiter.check(client_ip)
    payload, token = auth_service.login(req)
    response.set_cookie(**build_auth_cookie_kwargs(token))
    return payload


@auth_router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token", path="/")
    return {"message": "Đăng xuất thành công!"}


@auth_router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"user": current_user}
