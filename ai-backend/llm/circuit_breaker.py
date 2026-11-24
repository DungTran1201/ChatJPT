"""Scoped LLM Model Circuit Breaker / Quota Cooldown Tracker.

Isolates 429 RESOURCE_EXHAUSTED cooldowns by `(user_scope, model_name)` so one user's
exhausted BYOK key does not block other users or system keys, while preserving
backward-compatible classmethod APIs for existing callers and tests.
"""

import logging
import re
import threading
import time
from typing import Dict, Optional, Tuple

logger = logging.getLogger("ai_chan.agent")

_GLOBAL_SCOPE = "__global__"


class ScopedModelQuotaTracker:
    """Thread-safe per-scope 429 cooldown tracker."""

    _lock = threading.Lock()
    _cooldowns: Dict[Tuple[str, str], float] = {}

    @classmethod
    def _scope(cls, user_id: Optional[str]) -> str:
        return user_id if user_id else _GLOBAL_SCOPE

    @classmethod
    def is_rate_limit_error(cls, error_str: str) -> bool:
        low = (error_str or "").lower()
        return any(
            marker in low
            for marker in ("429", "resource_exhausted", "too many requests", "rate_limit", "rate limit")
        )

    @classmethod
    def record_quota_exhausted(
        cls,
        model_name: str,
        retry_delay_seconds: float = 1800.0,
        user_id: Optional[str] = None,
    ) -> None:
        if not model_name:
            return
        key = (cls._scope(user_id), model_name)
        with cls._lock:
            cls._cooldowns[key] = time.time() + max(1.0, float(retry_delay_seconds))
        logger.warning(
            "[CircuitBreaker] Model '%s' (scope=%s) marked quota-exhausted (429). Cooldown active for %ds.",
            model_name,
            key[0],
            int(retry_delay_seconds),
        )

    @classmethod
    def is_available(cls, model_name: str, user_id: Optional[str] = None) -> bool:
        if not model_name:
            return True
        now = time.time()
        scope = cls._scope(user_id)
        with cls._lock:
            cooldown_until = cls._cooldowns.get((scope, model_name), 0.0)
            if scope != _GLOBAL_SCOPE:
                global_until = cls._cooldowns.get((_GLOBAL_SCOPE, model_name), 0.0)
                cooldown_until = max(cooldown_until, global_until)
        if now < cooldown_until:
            remaining = int(cooldown_until - now)
            logger.info(
                "[CircuitBreaker] Skipping '%s' (scope=%s, cooldown %ds remaining).",
                model_name,
                scope,
                remaining,
            )
            return False
        return True

    @classmethod
    def parse_retry_delay(cls, error_str: str, default_seconds: float = 1800.0) -> float:
        text = error_str or ""
        m = re.search(r'retryDelay[\'"]?\s*:\s*[\'"]?(\d+)s?', text)
        if m:
            return float(m.group(1))
        h_m = re.search(r"retry in\s+(\d+)h(\d+)m", text)
        if h_m:
            return float(int(h_m.group(1)) * 3600 + int(h_m.group(2)) * 60)
        return default_seconds

    @classmethod
    def clear(cls) -> None:
        with cls._lock:
            cls._cooldowns.clear()


# Backward-compatible alias
ModelQuotaTracker = ScopedModelQuotaTracker
