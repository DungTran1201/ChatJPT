"""Authentication application service (SRP, DIP, zero raw SQL, zero HTTPException)."""

import uuid
from typing import Any, Dict, Tuple

from src.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    UnauthorizedError,
    ValidationDomainError,
)
from src.core.security import create_access_token, hash_password, verify_password
from src.models.v1.user import EMAIL_REGEX, UserModel, UserStatus
from src.repositories.user_repo import UserRepository
from src.schemas.v1.auth import LoginRequest, RegisterRequest


class AuthService:
    """Handles user registration and authentication workflows."""

    def __init__(self, user_repo: UserRepository):
        self._users = user_repo

    def register(self, req: RegisterRequest) -> Dict[str, Any]:
        email_clean = req.email.lower().strip()
        if not EMAIL_REGEX.match(email_clean):
            raise ValidationDomainError("Định dạng email không hợp lệ.")

        if self._users.exists_by_email(email_clean):
            raise ConflictError("Email này đã được sử dụng. Vui lòng đăng nhập hoặc chọn email khác.")

        user_id = str(uuid.uuid4())
        hashed_pw = hash_password(req.password)
        name_clean = req.full_name.strip() if req.full_name else email_clean.split("@")[0]

        created_user = self._users.create(
            user_id=user_id,
            email=email_clean,
            full_name=name_clean,
            hashed_password=hashed_pw,
        )
        return {
            "message": "Đăng ký tài khoản thành công!",
            "user": created_user,
        }

    def login(self, req: LoginRequest) -> Tuple[Dict[str, Any], str]:
        email_clean = req.email.lower().strip()
        user = self._users.get_by_email_with_password(email_clean)

        if not user:
            raise UnauthorizedError("Email hoặc mật khẩu không chính xác.")

        if user.get("hashed_password") is None:
            raise BadRequestError(
                "Tài khoản này được đăng ký qua Discord. Vui lòng đăng nhập bằng nút Tiếp tục với Discord."
            )

        if not verify_password(req.password, user["hashed_password"]):
            raise UnauthorizedError("Email hoặc mật khẩu không chính xác.")

        if user["status"] != UserStatus.ACTIVE.value:
            raise ForbiddenError("Tài khoản hiện đang bị tạm khóa.")

        self._users.touch_last_login(user["id"])
        refreshed = self._users.get_by_id(user["id"]) or user
        token = create_access_token(user_id=refreshed["id"], email=refreshed["email"])

        payload = {
            "message": "Đăng nhập thành công!",
            "user": UserModel.from_user_row(refreshed).to_login_dict(),
            "token": token,
        }
        return payload, token
