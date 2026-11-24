"""Telemetry & Quota Repository — atomic quota upserts and SQL-aggregated KPI summaries."""

from typing import Any, Dict, List, Tuple
from src.repositories.base import BaseSQLiteRepository


class TelemetryRepository(BaseSQLiteRepository):
    """Data access layer for user_quotas and api_metric_logs."""

    def get_or_create_quota(
        self,
        user_id: str,
        *,
        now_str: str,
        next_midnight_str: str,
        default_limit: int = 100000,
    ) -> Dict[str, Any]:
        """Atomically ensures a quota row exists and resets it if past midnight UTC."""
        with self._db.transaction() as uow:
            uow.execute(
                """
                INSERT OR IGNORE INTO user_quotas (user_id, daily_token_limit, daily_tokens_used, reset_at)
                VALUES (?, ?, 0, ?)
                """,
                (user_id, default_limit, next_midnight_str),
            )
            quota = uow.query_one(
                "SELECT user_id, daily_token_limit, daily_tokens_used, reset_at FROM user_quotas WHERE user_id = ?",
                (user_id,),
            )
            if quota and quota.get("reset_at") and quota["reset_at"] <= now_str:
                uow.execute(
                    """
                    UPDATE user_quotas
                    SET daily_tokens_used = 0, reset_at = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (next_midnight_str, user_id),
                )
                quota["daily_tokens_used"] = 0
                quota["reset_at"] = next_midnight_str
        return quota or {
            "user_id": user_id,
            "daily_token_limit": default_limit,
            "daily_tokens_used": 0,
            "reset_at": next_midnight_str,
        }

    def consume_quota_atomic(
        self,
        user_id: str,
        tokens: int,
        *,
        now_str: str,
        next_midnight_str: str,
        default_limit: int = 100000,
    ) -> Dict[str, Any]:
        """Atomically creates/resets quota and adds consumed tokens in one transaction."""
        with self._db.transaction() as uow:
            uow.execute(
                """
                INSERT OR IGNORE INTO user_quotas (user_id, daily_token_limit, daily_tokens_used, reset_at)
                VALUES (?, ?, 0, ?)
                """,
                (user_id, default_limit, next_midnight_str),
            )
            quota = uow.query_one(
                "SELECT reset_at FROM user_quotas WHERE user_id = ?",
                (user_id,),
            )
            if quota and quota.get("reset_at") and quota["reset_at"] <= now_str:
                uow.execute(
                    """
                    UPDATE user_quotas
                    SET daily_tokens_used = ?, reset_at = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (tokens, next_midnight_str, user_id),
                )
            else:
                uow.execute(
                    """
                    UPDATE user_quotas
                    SET daily_tokens_used = daily_tokens_used + ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (tokens, user_id),
                )
            updated = uow.query_one(
                "SELECT user_id, daily_token_limit, daily_tokens_used, reset_at FROM user_quotas WHERE user_id = ?",
                (user_id,),
            )
        return updated or {
            "user_id": user_id,
            "daily_token_limit": default_limit,
            "daily_tokens_used": tokens,
            "reset_at": next_midnight_str,
        }

    def insert_metric(self, record: Dict[str, Any]) -> None:
        self._db.execute_commit(
            """
            INSERT INTO api_metric_logs (
                id, user_id, endpoint, method, status_code,
                latency_ms, ttft_ms, model_name, provider,
                prompt_tokens, completion_tokens, total_tokens, error_code
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["user_id"],
                record["endpoint"],
                record["method"],
                record["status_code"],
                record["latency_ms"],
                record["ttft_ms"],
                record["model_name"],
                record["provider"],
                record["prompt_tokens"],
                record["completion_tokens"],
                record["total_tokens"],
                record["error_code"],
            ),
        )

    def aggregate_metrics(self, user_id: str, since_time: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Runs SQL aggregations + fetches only the latest 30 points for trend charting."""
        agg = self._db.query_one(
            """
            SELECT
                COUNT(*) AS total_requests,
                COALESCE(AVG(latency_ms), 0.0) AS avg_latency_ms,
                COALESCE(AVG(ttft_ms), 0.0) AS avg_ttft_ms,
                COALESCE(SUM(total_tokens), 0) AS total_tokens,
                COALESCE(SUM(prompt_tokens), 0) AS prompt_tokens,
                COALESCE(SUM(completion_tokens), 0) AS completion_tokens,
                COALESCE(SUM(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 ELSE 0 END), 0) AS s2xx,
                COALESCE(SUM(CASE WHEN status_code >= 400 AND status_code < 500 THEN 1 ELSE 0 END), 0) AS s4xx,
                COALESCE(SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END), 0) AS s5xx,
                COALESCE(SUM(CASE WHEN LOWER(COALESCE(provider, '')) LIKE '%google%' OR LOWER(COALESCE(provider, '')) LIKE '%gemini%' THEN total_tokens ELSE 0 END), 0) AS tok_google,
                COALESCE(SUM(CASE WHEN LOWER(COALESCE(provider, '')) LIKE '%openai%' OR LOWER(COALESCE(provider, '')) LIKE '%gpt%' THEN total_tokens ELSE 0 END), 0) AS tok_openai,
                COALESCE(SUM(CASE WHEN LOWER(COALESCE(provider, '')) LIKE '%anthropic%' OR LOWER(COALESCE(provider, '')) LIKE '%claude%' THEN total_tokens ELSE 0 END), 0) AS tok_anthropic,
                COALESCE(SUM(CASE WHEN NOT (
                    LOWER(COALESCE(provider, '')) LIKE '%google%' OR LOWER(COALESCE(provider, '')) LIKE '%gemini%'
                    OR LOWER(COALESCE(provider, '')) LIKE '%openai%' OR LOWER(COALESCE(provider, '')) LIKE '%gpt%'
                    OR LOWER(COALESCE(provider, '')) LIKE '%anthropic%' OR LOWER(COALESCE(provider, '')) LIKE '%claude%'
                ) THEN total_tokens ELSE 0 END), 0) AS tok_other
            FROM api_metric_logs
            WHERE user_id = ? AND created_at >= ?
            """,
            (user_id, since_time),
        ) or {}

        recent_desc = self._db.query_all(
            """
            SELECT created_at, latency_ms, ttft_ms, total_tokens
            FROM api_metric_logs
            WHERE user_id = ? AND created_at >= ?
            ORDER BY created_at DESC, rowid DESC
            LIMIT 30
            """,
            (user_id, since_time),
        )
        recent_desc.reverse()
        return agg, recent_desc

    def list_history(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        return self._db.query_all(
            """
            SELECT * FROM api_metric_logs
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset),
        )
