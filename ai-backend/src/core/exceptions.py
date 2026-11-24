"""Domain exception hierarchy decoupling services/repositories from FastAPI HTTPException."""

from typing import Any, Dict, Optional


class DomainError(Exception):
    """Base domain exception translated to HTTP responses at the API boundary."""

    status_code: int = 500

    def __init__(
        self,
        message: str,
        *,
        error_code: Optional[str] = None,
        status_code: Optional[int] = None,
        extra: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        structured: bool = False,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        if status_code is not None:
            self.status_code = status_code
        self.extra = extra or {}
        self.headers = headers or {}
        self.structured = structured

    def to_http_detail(self) -> Any:
        """Preserves exact error payload contract expected by frontend and existing tests."""
        if self.structured or self.error_code or self.extra:
            payload: Dict[str, Any] = {"message": self.message}
            if self.error_code:
                payload["error_code"] = self.error_code
            payload.update(self.extra)
            return payload
        return self.message


class BadRequestError(DomainError):
    status_code = 400


class UnauthorizedError(DomainError):
    status_code = 401


class ForbiddenError(DomainError):
    status_code = 403


class NotFoundError(DomainError):
    status_code = 404


class ConflictError(DomainError):
    status_code = 409


class PayloadTooLargeError(DomainError):
    status_code = 413


class ValidationDomainError(DomainError):
    status_code = 422


class RateLimitExceededError(DomainError):
    status_code = 429


class QuotaExceededError(DomainError):
    status_code = 429


class ExternalServiceError(DomainError):
    status_code = 502
