"""Exam & Reference Material Repository — isolates SQL on exams, exam_questions, reference_materials."""

from typing import Any, Dict, List, Optional
from src.repositories.base import BaseSQLiteRepository

_UPDATABLE_EXAM_FIELDS = (
    "title",
    "description",
    "level",
    "category",
    "year",
    "duration_minutes",
    "passing_score",
    "max_score",
    "drive_folder_url",
    "status",
)


class ExamRepository(BaseSQLiteRepository):
    """Data access layer for JLPT mock exams, questions, and reference materials."""

    # ------------------------------------------------------------------
    # Exams & Questions
    # ------------------------------------------------------------------
    def list_exams_with_counts(
        self,
        *,
        level: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Single-query exam listing with question counts (eliminates N+1 query)."""
        sql = """
            SELECT e.*, COALESCE(q.actual_q_count, e.total_questions, 0) AS actual_q_count
            FROM exams e
            LEFT JOIN (
                SELECT exam_id, COUNT(*) AS actual_q_count
                FROM exam_questions
                GROUP BY exam_id
            ) q ON e.id = q.exam_id
            WHERE e.status != 'ARCHIVED'
        """
        params: List[Any] = []

        if level:
            sql += " AND e.level = ?"
            params.append(level.upper())
        if category:
            sql += " AND e.category = ?"
            params.append(category.upper())
        if search and search.strip():
            s_term = f"%{search.strip()}%"
            sql += " AND (e.title LIKE ? OR e.description LIKE ?)"
            params.extend([s_term, s_term])

        sql += (
            " ORDER BY CASE e.level WHEN 'N5' THEN 1 WHEN 'N4' THEN 2 WHEN 'N3' THEN 3 "
            "WHEN 'N2' THEN 4 WHEN 'N1' THEN 5 ELSE 6 END ASC, e.created_at ASC"
        )
        return self._db.query_all(sql, tuple(params))

    def get_exam_by_id(self, exam_id: str) -> Optional[Dict[str, Any]]:
        return self._db.query_one("SELECT * FROM exams WHERE id = ?", (exam_id,))

    def list_questions(self, exam_id: str) -> List[Dict[str, Any]]:
        return self._db.query_all(
            "SELECT * FROM exam_questions WHERE exam_id = ? ORDER BY question_number ASC",
            (exam_id,),
        )

    def create_exam(self, record: Dict[str, Any]) -> Dict[str, Any]:
        with self._db.transaction() as uow:
            uow.execute(
                """
                INSERT INTO exams (
                    id, title, description, level, category, year,
                    duration_minutes, total_questions, passing_score, max_score,
                    drive_folder_url, status, is_system_preset, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, 0, ?)
                """,
                (
                    record["id"],
                    record["title"],
                    record.get("description"),
                    record["level"],
                    record["category"],
                    record["year"],
                    record["duration_minutes"],
                    record["passing_score"],
                    record["max_score"],
                    record.get("drive_folder_url"),
                    record["status"],
                    record["user_id"],
                ),
            )
            created = uow.query_one("SELECT * FROM exams WHERE id = ?", (record["id"],))
        return created or {}

    def update_exam(self, exam_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        clauses: List[str] = []
        params: List[Any] = []
        for field in _UPDATABLE_EXAM_FIELDS:
            if field in updates and updates[field] is not None:
                clauses.append(f"{field} = ?")
                params.append(updates[field])
        if not clauses:
            return self.get_exam_by_id(exam_id)

        params.append(exam_id)
        with self._db.transaction() as uow:
            uow.execute(
                f"UPDATE exams SET {', '.join(clauses)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                tuple(params),
            )
            return uow.query_one("SELECT * FROM exams WHERE id = ?", (exam_id,))

    def delete_exam(self, exam_id: str) -> None:
        self._db.execute_commit("DELETE FROM exams WHERE id = ?", (exam_id,))

    # ------------------------------------------------------------------
    # Reference Materials
    # ------------------------------------------------------------------
    def list_materials(
        self,
        *,
        category: Optional[str] = None,
        level: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM reference_materials WHERE 1=1"
        params: List[Any] = []
        if category:
            sql += " AND category = ?"
            params.append(category.upper())
        if level:
            sql += " AND (level = ? OR level = 'ALL')"
            params.append(level.upper())
        if search and search.strip():
            s_term = f"%{search.strip()}%"
            sql += " AND (title LIKE ? OR description LIKE ? OR tags LIKE ?)"
            params.extend([s_term, s_term, s_term])
        sql += " ORDER BY is_pinned DESC, created_at ASC"
        return self._db.query_all(sql, tuple(params))

    def get_material_by_id(self, material_id: str) -> Optional[Dict[str, Any]]:
        return self._db.query_one("SELECT * FROM reference_materials WHERE id = ?", (material_id,))

    def create_material(self, record: Dict[str, Any]) -> Dict[str, Any]:
        with self._db.transaction() as uow:
            uow.execute(
                """
                INSERT INTO reference_materials (
                    id, title, description, category, level, source_type,
                    external_url, author, file_type, tags, is_pinned, is_system_preset, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    record["id"],
                    record["title"],
                    record.get("description"),
                    record["category"],
                    record["level"],
                    record["source_type"],
                    record.get("external_url"),
                    record.get("author"),
                    record["file_type"],
                    record.get("tags"),
                    1 if record.get("is_pinned") else 0,
                    record["user_id"],
                ),
            )
            created = uow.query_one("SELECT * FROM reference_materials WHERE id = ?", (record["id"],))
        return created or {}

    def delete_material(self, material_id: str) -> None:
        self._db.execute_commit("DELETE FROM reference_materials WHERE id = ?", (material_id,))
