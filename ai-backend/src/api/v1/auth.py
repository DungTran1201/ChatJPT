import uuid
from fastapi import APIRouter, Response, HTTPException, status, Depends
from src.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from src.db import query_one, execute_commit
from src.models.v1.user import EMAIL_REGEX, UserModel
from src.schemas.v1.auth import (
    RegisterRequest,
    LoginRequest,
    UserProfileResponse,
)

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest):
    # Kiểm tra trùng lặp email (D-AUTH-01, TC-002)
    existing = query_one("SELECT id FROM users WHERE email = ?", (req.email.lower().strip(),))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email này đã được sử dụng. Vui lòng đăng nhập hoặc chọn email khác."
        )

    user_id = str(uuid.uuid4())
    hashed_pw = hash_password(req.password)
    email_clean = req.email.lower().strip()
    name_clean = req.full_name.strip() if req.full_name else email_clean.split("@")[0]

    execute_commit(
        """
        INSERT INTO users (id, email, full_name, hashed_password, status)
        VALUES (?, ?, ?, ?, 'ACTIVE')
        """,
        (user_id, email_clean, name_clean, hashed_pw)
    )

    created_user = query_one("SELECT id, email, full_name, status, created_at FROM users WHERE id = ?", (user_id,))
    return {
        "message": "Đăng ký tài khoản thành công!",
        "user": created_user
    }

@auth_router.post("/login")
async def login(req: LoginRequest, response: Response):
    email_clean = req.email.lower().strip()
    user = query_one(
        """
        SELECT id, email, full_name, username, avatar_url, bio, phone_number,
               age, occupation, interests, japanese_level, learning_goal,
               custom_bg_url, bg_opacity, bg_blur, bg_dim, accent_color, ui_font_size,
               discord_id, discord_username,
               theme_preference, language_preference, status, created_at,
               last_login_at, hashed_password
        FROM users WHERE email = ?
        """,
        (email_clean,)
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác."
        )

    # Kiểm tra bất biến tài khoản đăng ký qua Discord không có mật khẩu (BR-018)
    if user.get("hashed_password") is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài khoản này được đăng ký qua Discord. Vui lòng đăng nhập bằng nút Tiếp tục với Discord."
        )

    if not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác."
        )

    if user["status"] != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản hiện đang bị tạm khóa."
        )

    # Cập nhật thời điểm đăng nhập gần nhất (PROC-002, FR-015)
    execute_commit(
        "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?",
        (user["id"],)
    )

    token = create_access_token(user_id=user["id"], email=user["email"])

    # Đóng gói Token vào HttpOnly Secure Cookie (ADR-002, SEC-004)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,  # Set False for local development HTTP support
        samesite="lax",
        max_age=7 * 24 * 3600,
        path="/"
    )

    return {
        "message": "Đăng nhập thành công!",
        "user": UserModel.from_user_row(user).to_login_dict(),
        "token": token
    }

@auth_router.post("/logout")
async def logout(response: Response):
    # Thu hồi cookie phiên làm việc (PROC-003, TC-005)
    response.delete_cookie(key="access_token", path="/")
    return {"message": "Đăng xuất thành công!"}

@auth_router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "user": current_user
    }

