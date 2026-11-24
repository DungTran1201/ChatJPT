"""Authentication, JWT session validation, password hashing, rate limiting & authz guards."""

import time
import bcrypt
import jwt
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from fastapi import Request, HTTPException, status

from src.core.config import settings
from src.core.database import db_manager

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 7
GUEST_USER_ID = "guest_user"


class InMemoryRateLimiter:
    """Sliding-window in-memory rate limiter reusable across IP or user scopes.

    ponytail: in-process memory dict with periodic empty-bucket cleanup; ceiling is single
    worker process. Upgrade path: swap backing store to Redis INCR/EXPIRE when multi-worker.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        detail: str = "Application rate limit exceeded: maximum requests per minute reached.",
    ):
        self.requests_per_minute = requests_per_minute
        self.detail = detail
        self.clients: Dict[str, List[float]] = defaultdict(list)

    def check(self, key: str) -> None:
        now = time.time()
        cutoff = now - 60.0
        timestamps = [t for t in self.clients.get(key, ()) if t > cutoff]
        if len(timestamps) >= self.requests_per_minute:
            self.clients[key] = timestamps
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=self.detail,
            )
        timestamps.append(now)
        self.clients[key] = timestamps


# Shared rate limiter instances
app_rate_limiter = InMemoryRateLimiter(requests_per_minute=60)
auth_rate_limiter = InMemoryRateLimiter(
    requests_per_minute=30,
    detail="Quá nhiều yêu cầu xác thực. Vui lòng thử lại sau 1 phút.",
)
connection_test_limiter = InMemoryRateLimiter(
    requests_per_minute=15,
    detail="Tần suất kiểm tra kết nối vượt quá giới hạn an toàn. Vui lòng thử lại sau 1 phút.",
)


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    expire_minutes = max(1, int(settings.ACCESS_TOKEN_EXPIRE_MINUTES or (JWT_EXPIRATION_DAYS * 1440)))
    expire = now + timedelta(minutes=expire_minutes)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": now,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def extract_token_from_request(request: Request, *, allow_query: bool = False) -> Optional[str]:
    """Single source of truth for extracting JWT from HttpOnly cookie, Bearer header, or query."""
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
    if not token and allow_query:
        token = request.query_params.get("token")
    return token


def build_auth_cookie_kwargs(token: str) -> Dict[str, Any]:
    """Unified HttpOnly session cookie settings (ADR-002, SEC-004)."""
    max_age = max(60, int(settings.ACCESS_TOKEN_EXPIRE_MINUTES or (JWT_EXPIRATION_DAYS * 1440)) * 60)
    return {
        "key": "access_token",
        "value": token,
        "httponly": True,
        "secure": bool(settings.COOKIE_SECURE),
        "samesite": "lax",
        "max_age": max_age,
        "path": "/",
    }


def _parse_utc_timestamp(ts_value: Any) -> Optional[float]:
    if not ts_value:
        return None
    if isinstance(ts_value, (int, float)):
        return float(ts_value)
    text = str(ts_value).strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except ValueError:
        pass
    try:
        dt = datetime.strptime(text, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except ValueError:
        return None


def is_token_revoked_by_password_change(payload: Dict[str, Any], password_changed_at: Any) -> bool:
    """Enforces SEC-007: rejects JWTs issued strictly before the last password change."""
    changed_ts = _parse_utc_timestamp(password_changed_at)
    if changed_ts is None:
        return False
    iat = payload.get("iat")
    if iat is None:
        return False
    # Allow 1-second skew so a token minted in the same second as CURRENT_TIMESTAMP stays valid.
    return float(iat) < (changed_ts - 1.0)


def is_admin_user(user: Optional[Dict[str, Any]]) -> bool:
    """Explicit admin authorization without unsafe substring matching."""
    if not user:
        return False
    email = (user.get("email") or "").strip().lower()
    if email and email in settings.admin_emails:
        return True
    if settings.DEBUG and settings.APP_ENV == "development":
        return True
    return False


_USER_AUTH_SELECT = """
    SELECT id, email, full_name, username, avatar_url, bio, phone_number,
           age, occupation, interests, japanese_level, learning_goal,
           custom_bg_url, bg_opacity, bg_blur, bg_dim, accent_color, ui_font_size,
           discord_id, discord_username,
           theme_preference, language_preference,
           response_show_translation, response_show_furigana,
           response_highlight_grammar, response_show_romaji,
           response_grammar_breakdown, response_audio_speech,
           response_bilingual_mode,
           status, created_at, last_login_at, password_changed_at
    FROM users WHERE id = ?
"""


def authenticate_token(token: Optional[str]) -> Dict[str, Any]:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chưa xác thực: Vui lòng đăng nhập để tiếp tục.",
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phiên đăng nhập không hợp lệ hoặc đã hết hạn.",
        )

    user = db_manager.query_one(_USER_AUTH_SELECT, (payload["sub"],))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản người dùng không tồn tại.",
        )

    if user.get("status") != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản hiện đang bị tạm khóa.",
        )

    if is_token_revoked_by_password_change(payload, user.get("password_changed_at")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phiên đăng nhập đã bị thu hồi do mật khẩu thay đổi. Vui lòng đăng nhập lại.",
        )

    return user


async def get_current_user(request: Request) -> Dict[str, Any]:
    return authenticate_token(extract_token_from_request(request, allow_query=False))


async def get_current_user_or_query(request: Request) -> Dict[str, Any]:
    """Authenticates EventSource/SSE requests via Cookie, Bearer header, or ?token=."""
    return authenticate_token(extract_token_from_request(request, allow_query=True))


async def get_optional_current_user(request: Request) -> Dict[str, Any]:
    """Returns authenticated user if valid token present, else Guest Learner fallback."""
    token = extract_token_from_request(request, allow_query=False)
    if token:
        try:
            return authenticate_token(token)
        except HTTPException:
            pass

    return {
        "id": GUEST_USER_ID,
        "email": "guest@chatjpt.local",
        "full_name": "Guest Learner",
        "username": "guest",
        "status": "ACTIVE",
    }
