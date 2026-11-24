"""Embedded Model & Semantic Cache Repository — isolates SQL on embedded_models & semantic_cache."""

from typing import Any, Dict, List, Optional
from src.repositories.base import BaseSQLiteRepository


class EmbeddedRepository(BaseSQLiteRepository):
    """Data access layer for in-project embedded models and FTS5 semantic cache."""

    # ------------------------------------------------------------------
    # Embedded Models
    # ------------------------------------------------------------------
    def get_embedded_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        return self._db.query_one(
            """
            SELECT id, name, file_path, file_size_bytes, min_ram_gb, min_avail_ram_gb,
                   min_disk_gb, min_cpu_cores, download_status, download_progress, is_active,
                   created_at, updated_at
            FROM embedded_models
            WHERE id = ?
            """,
            (model_id,),
        )

    def ensure_embedded_model(self, model_id: str, file_path: str) -> Dict[str, Any]:
        self._db.execute_commit(
            """
            INSERT OR IGNORE INTO embedded_models (
                id, name, file_path, file_size_bytes, min_ram_gb, min_avail_ram_gb,
                min_disk_gb, min_cpu_cores, download_status, download_progress, is_active
            ) VALUES (
                ?, 'Qwen 2.5 0.5B (Direct In-Project Embedded)', ?, 398000000,
                4.0, 1.5, 1.5, 2, 'NOT_DOWNLOADED', 0, 1
            )
            """,
            (model_id, file_path),
        )
        return self.get_embedded_model(model_id) or {}

    def update_download_state(
        self,
        model_id: str,
        *,
        status: str,
        progress: int,
        file_size_bytes: Optional[int] = None,
    ) -> None:
        if file_size_bytes is not None:
            self._db.execute_commit(
                """
                UPDATE embedded_models
                SET download_status = ?, download_progress = ?, file_size_bytes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, progress, file_size_bytes, model_id),
            )
        else:
            self._db.execute_commit(
                """
                UPDATE embedded_models
                SET download_status = ?, download_progress = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, progress, model_id),
            )

    def update_download_progress(self, model_id: str, progress: int) -> None:
        self._db.execute_commit(
            "UPDATE embedded_models SET download_progress = ? WHERE id = ?",
            (progress, model_id),
        )

    def sync_catalog_model_status(self, model_id: str, catalog_status: str) -> None:
        self._db.execute_commit(
            "UPDATE models SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (catalog_status, model_id),
        )

    # ------------------------------------------------------------------
    # Semantic Cache (B-tree exact + FTS5 candidate retrieval)
    # ------------------------------------------------------------------
    def get_cache_exact(self, prompt_normalized: str) -> Optional[Dict[str, Any]]:
        return self._db.query_one(
            """
            SELECT id, prompt_raw, prompt_normalized, category, response_text, keywords, hit_count
            FROM semantic_cache
            WHERE prompt_normalized = ?
            """,
            (prompt_normalized,),
        )

    def search_cache_fts(self, fts_expression: str, limit: int = 50) -> List[Dict[str, Any]]:
        return self._db.query_all(
            """
            SELECT s.id, s.prompt_raw, s.prompt_normalized, s.category, s.response_text, s.keywords, s.hit_count
            FROM semantic_cache_fts f
            JOIN semantic_cache s ON f.rowid = s.rowid
            WHERE semantic_cache_fts MATCH ?
            LIMIT ?
            """,
            (fts_expression, limit),
        )

    def search_cache_like(self, pattern: str, limit: int = 30) -> List[Dict[str, Any]]:
        return self._db.query_all(
            """
            SELECT id, prompt_raw, prompt_normalized, category, response_text, keywords, hit_count
            FROM semantic_cache
            WHERE prompt_normalized LIKE ?
            LIMIT ?
            """,
            (pattern, limit),
        )

    def increment_hit_count(self, cache_id: str) -> None:
        self._db.execute_commit(
            "UPDATE semantic_cache SET hit_count = hit_count + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (cache_id,),
        )

    def insert_cache_entry(
        self,
        *,
        cache_id: str,
        prompt_raw: str,
        prompt_normalized: str,
        category: str,
        response_text: str,
        keywords: str,
    ) -> None:
        self._db.execute_commit(
            """
            INSERT INTO semantic_cache (
                id, prompt_raw, prompt_normalized, category, response_text, keywords, similarity_score, hit_count
            ) VALUES (?, ?, ?, ?, ?, ?, 1.0, 1)
            """,
            (cache_id, prompt_raw, prompt_normalized, category, response_text, keywords),
        )

    def get_cache_stats(self) -> Dict[str, Any]:
        totals = self._db.query_one("SELECT COUNT(*) AS count, SUM(hit_count) AS total_hits FROM semantic_cache")
        total_rows = int(totals["count"]) if totals and totals.get("count") else 0
        total_hits = int(totals["total_hits"]) if totals and totals.get("total_hits") else 0

        categories = self._db.query_all(
            "SELECT category, COUNT(*) AS count FROM semantic_cache GROUP BY category ORDER BY count DESC"
        )
        top_hits = self._db.query_all(
            "SELECT id, prompt_raw, category, hit_count, updated_at FROM semantic_cache ORDER BY hit_count DESC LIMIT 10"
        )
        return {
            "total_entries": total_rows,
            "total_hits": total_hits,
            "categories": categories,
            "top_hits": top_hits,
        }
