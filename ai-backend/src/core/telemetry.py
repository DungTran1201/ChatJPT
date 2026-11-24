"""Real-time Telemetry SSE Manager, Daily Quota Manager, and Metric Logger."""

import asyncio
import json
import uuid
import weakref
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from src.models.v1.resource import UserQuotaEntity
from src.repositories.telemetry_repo import TelemetryRepository

_DELTA_MAP = {
    "1h": timedelta(hours=1),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


class SSEConnectionManager:
    """Manages bounded per-user EventSource SSE queues safely across event loops."""

    def __init__(self, max_queue_size: int = 100):
        self._max_queue_size = max_queue_size
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._locks: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Lock]" = weakref.WeakKeyDictionary()

    def _get_lock(self) -> asyncio.Lock:
        loop = asyncio.get_running_loop()
        lock = self._locks.get(loop)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[loop] = lock
        return lock

    async def connect(self, user_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=self._max_queue_size)
        async with self._get_lock():
            self._subscribers.setdefault(user_id, set()).add(queue)
        return queue

    async def disconnect(self, user_id: str, queue: asyncio.Queue) -> None:
        async with self._get_lock():
            if user_id in self._subscribers:
                self._subscribers[user_id].discard(queue)
                if not self._subscribers[user_id]:
                    del self._subscribers[user_id]

    async def broadcast(self, user_id: Optional[str], event: str, data: dict) -> None:
        payload = f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        targets: List[asyncio.Queue] = []

        async with self._get_lock():
            if user_id and user_id in self._subscribers:
                targets.extend(list(self._subscribers[user_id]))
            if "*" in self._subscribers:
                targets.extend(list(self._subscribers["*"]))

        for q in targets:
            try:
                if q.full():
                    try:
                        q.get_nowait()  # drop oldest stale telemetry event to protect slow clients
                    except asyncio.QueueEmpty:
                        pass
                q.put_nowait(payload)
            except Exception:
                pass


class QuotaManager:
    """Manages daily token quota, 80% warnings, and 100% enforcement (BR-020)."""

    def __init__(self, repo: Optional[TelemetryRepository] = None):
        self._repo = repo or TelemetryRepository()

    @staticmethod
    def _now_and_next_midnight() -> Tuple[str, str]:
        now = datetime.now(timezone.utc)
        next_day = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return now.strftime("%Y-%m-%d %H:%M:%S"), next_day.strftime("%Y-%m-%d %H:%M:%S")

    def get_quota(self, user_id: str) -> Dict[str, Any]:
        now_str, next_midnight = self._now_and_next_midnight()
        return self._repo.get_or_create_quota(user_id, now_str=now_str, next_midnight_str=next_midnight)

    def check(self, user_id: str, estimated_tokens: int = 1000) -> Tuple[bool, int, int, bool]:
        quota = self.get_quota(user_id)
        current_used = int(quota["daily_tokens_used"])
        limit = int(quota["daily_token_limit"])
        is_allowed = (current_used + estimated_tokens) <= limit
        warning_80 = current_used >= (0.8 * limit)
        return is_allowed, current_used, limit, warning_80

    def consume(self, user_id: str, tokens: int) -> Dict[str, Any]:
        now_str, next_midnight = self._now_and_next_midnight()
        return self._repo.consume_quota_atomic(
            user_id,
            tokens,
            now_str=now_str,
            next_midnight_str=next_midnight,
        )

    # Backward-compatible classmethod facade
    @classmethod
    def get_or_create_quota(cls, user_id: str) -> Dict[str, Any]:
        return quota_manager.get_quota(user_id)

    @classmethod
    def check_quota(cls, user_id: str, estimated_tokens: int = 1000) -> Tuple[bool, int, int, bool]:
        return quota_manager.check(user_id, estimated_tokens=estimated_tokens)

    @classmethod
    def consume_quota(cls, user_id: str, tokens: int) -> Dict[str, Any]:
        return quota_manager.consume(user_id, tokens)


class MetricLogger:
    """Logs API performance metrics, broadcasts real-time SSE updates, and aggregates KPIs in SQL."""

    def __init__(
        self,
        sse_mgr: SSEConnectionManager,
        repo: Optional[TelemetryRepository] = None,
        quota_mgr: Optional[QuotaManager] = None,
    ):
        self.sse_manager = sse_mgr
        self._repo = repo or TelemetryRepository()
        self._quota = quota_mgr or QuotaManager(self._repo)

    def log_metric(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        latency_ms: float,
        user_id: Optional[str] = None,
        ttft_ms: Optional[float] = None,
        model_name: Optional[str] = None,
        provider: Optional[str] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        error_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        metric_id = str(uuid.uuid4())
        log_item = {
            "id": metric_id,
            "user_id": user_id,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "latency_ms": round(latency_ms, 2),
            "ttft_ms": round(ttft_ms, 2) if ttft_ms is not None else None,
            "model_name": model_name,
            "provider": provider,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "error_code": error_code,
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._repo.insert_metric(log_item)

        if user_id:
            quota = self._quota.get_quota(user_id)
            quota_entity = UserQuotaEntity.from_quota_row(user_id, quota)
            event_payload = {
                "metric": log_item,
                "quota": {
                    "daily_tokens_used": quota_entity.daily_tokens_used,
                    "daily_token_limit": quota_entity.daily_token_limit,
                    "percent_used": quota_entity.percent_used,
                    "warning_80": quota_entity.warning_80,
                },
            }
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.sse_manager.broadcast(user_id, "metric_update", event_payload))
            except RuntimeError:
                pass

        return log_item

    def get_metrics_summary(self, user_id: str, time_range: str = "24h") -> Dict[str, Any]:
        delta = _DELTA_MAP.get(time_range, timedelta(hours=24))
        since_time = (datetime.now(timezone.utc) - delta).strftime("%Y-%m-%d %H:%M:%S")

        agg, recent_rows = self._repo.aggregate_metrics(user_id, since_time)
        total_requests = int(agg.get("total_requests") or 0)
        quota = self._quota.get_quota(user_id)
        quota_status = UserQuotaEntity.from_quota_row(user_id, quota).to_status_dict()

        if total_requests == 0:
            return {
                "time_range": time_range,
                "total_requests": 0,
                "avg_latency_ms": 0.0,
                "avg_ttft_ms": 0.0,
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "status_counts": {"2xx": 0, "4xx": 0, "5xx": 0},
                "tokens_by_provider": {"google": 0, "openai": 0, "anthropic": 0, "other": 0},
                "recent_trend": [],
                "quota_status": quota_status,
            }

        recent_trend = [
            {
                "time": r["created_at"].split(" ")[1] if " " in str(r["created_at"]) else str(r["created_at"]),
                "latency_ms": r["latency_ms"],
                "ttft_ms": r["ttft_ms"] or 0.0,
                "tokens": r["total_tokens"],
            }
            for r in recent_rows
        ]

        return {
            "time_range": time_range,
            "total_requests": total_requests,
            "avg_latency_ms": round(float(agg.get("avg_latency_ms") or 0.0), 1),
            "avg_ttft_ms": round(float(agg.get("avg_ttft_ms") or 0.0), 1),
            "total_tokens": int(agg.get("total_tokens") or 0),
            "prompt_tokens": int(agg.get("prompt_tokens") or 0),
            "completion_tokens": int(agg.get("completion_tokens") or 0),
            "status_counts": {
                "2xx": int(agg.get("s2xx") or 0),
                "4xx": int(agg.get("s4xx") or 0),
                "5xx": int(agg.get("s5xx") or 0),
            },
            "tokens_by_provider": {
                "google": int(agg.get("tok_google") or 0),
                "openai": int(agg.get("tok_openai") or 0),
                "anthropic": int(agg.get("tok_anthropic") or 0),
                "other": int(agg.get("tok_other") or 0),
            },
            "recent_trend": recent_trend,
            "quota_status": quota_status,
        }

    def get_metrics_history(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        return self._repo.list_history(user_id, limit=limit, offset=offset)


# Singleton instances
_telemetry_repo = TelemetryRepository()
sse_manager = SSEConnectionManager()
quota_manager = QuotaManager(_telemetry_repo)
metric_logger = MetricLogger(sse_manager, _telemetry_repo, quota_manager)
