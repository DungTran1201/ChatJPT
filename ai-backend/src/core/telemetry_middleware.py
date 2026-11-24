"""Pure ASGI Telemetry Middleware (non-buffering SSE-safe, BR-019, NFR-020)."""

import asyncio
import time
from http.cookies import SimpleCookie
from typing import Any, Callable, Optional

from src.core.security import decode_access_token
from src.core.telemetry import metric_logger


def _extract_user_id_from_scope(scope: dict) -> Optional[str]:
    token: Optional[str] = None
    headers = scope.get("headers") or []
    cookie_header = ""
    auth_header = ""
    for raw_k, raw_v in headers:
        k = raw_k.decode("latin-1").lower()
        if k == "cookie":
            cookie_header = raw_v.decode("latin-1")
        elif k == "authorization":
            auth_header = raw_v.decode("latin-1")

    if cookie_header:
        cookie = SimpleCookie()
        try:
            cookie.load(cookie_header)
            if "access_token" in cookie:
                token = cookie["access_token"].value
        except Exception:
            pass

    if not token and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()

    if not token:
        return None
    try:
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            return str(payload["sub"])
    except Exception:
        pass
    return None


class TelemetryMiddleware:
    """Pure ASGI middleware measuring latency and status codes without buffering SSE streams."""

    def __init__(self, app: Any):
        self.app = app

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path") or ""
        if (
            path.startswith("/api/v1/resources/stream")
            or path in ("/api/v1/health", "/docs", "/openapi.json", "/")
            or not path.startswith("/api/v1")
            or "/messages/stream" in path
        ):
            await self.app(scope, receive, send)
            return

        method: str = scope.get("method") or "GET"
        start_time = time.perf_counter()
        status_code = 500
        error_code: Optional[str] = None

        async def send_wrapper(message: dict) -> None:
            nonlocal status_code
            if message.get("type") == "http.response.start":
                status_code = int(message.get("status", 500))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            status_code = 500
            error_code = "UNHANDLED_EXCEPTION"
            raise
        finally:
            latency_ms = (time.perf_counter() - start_time) * 1000
            user_id = _extract_user_id_from_scope(scope)
            self._schedule_metric_write(
                endpoint=path,
                method=method,
                status_code=status_code,
                latency_ms=latency_ms,
                user_id=user_id,
                error_code=error_code,
            )

    @staticmethod
    def _schedule_metric_write(
        *,
        endpoint: str,
        method: str,
        status_code: int,
        latency_ms: float,
        user_id: Optional[str],
        error_code: Optional[str],
    ) -> None:
        async def _persist() -> None:
            try:
                await asyncio.to_thread(
                    metric_logger.log_metric,
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    latency_ms=latency_ms,
                    user_id=user_id,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    error_code=error_code,
                )
            except Exception:
                pass

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_persist())
        except RuntimeError:
            try:
                metric_logger.log_metric(
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    latency_ms=latency_ms,
                    user_id=user_id,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    error_code=error_code,
                )
            except Exception:
                pass
