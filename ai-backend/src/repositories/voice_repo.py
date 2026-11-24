"""Voice Repository — isolates all SQL on the voices table."""

from typing import Any, Dict, List, Optional
from src.repositories.base import BaseSQLiteRepository

_UPDATABLE_VOICE_FIELDS = (
    "name",
    "character_name",
    "speaker_id",
    "style_name",
    "gender",
    "description",
    "speed_scale",
    "pitch_scale",
    "intonation_scale",
    "volume_scale",
    "sample_text",
    "avatar_url",
    "status",
)


class VoiceRepository(BaseSQLiteRepository):
    """Data access layer for VoiceVox character voice profiles."""

    def list_filtered(
        self,
        *,
        gender: Optional[str] = None,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM voices WHERE 1=1"
        params: List[Any] = []

        if gender:
            sql += " AND gender = ?"
            params.append(gender.lower())

        if status_filter:
            sql += " AND status = ?"
            params.append(status_filter.upper())

        if search and search.strip():
            sql += " AND (name LIKE ? OR character_name LIKE ? OR description LIKE ?)"
            pattern = f"%{search.strip()}%"
            params.extend([pattern, pattern, pattern])

        sql += " ORDER BY is_system_preset DESC, character_name ASC, speaker_id ASC"
        return self._db.query_all(sql, tuple(params))

    def get_by_id(self, voice_id: str) -> Optional[Dict[str, Any]]:
        return self._db.query_one("SELECT * FROM voices WHERE id = ?", (voice_id,))

    def create(self, record: Dict[str, Any]) -> Dict[str, Any]:
        with self._db.transaction() as uow:
            uow.execute(
                """
                INSERT INTO voices (
                    id, name, character_name, speaker_id, style_name, gender, description,
                    speed_scale, pitch_scale, intonation_scale, volume_scale,
                    sample_text, avatar_url, status, is_system_preset, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    record["id"],
                    record["name"],
                    record["character_name"],
                    record["speaker_id"],
                    record["style_name"],
                    record["gender"],
                    record["description"],
                    record["speed_scale"],
                    record["pitch_scale"],
                    record["intonation_scale"],
                    record["volume_scale"],
                    record["sample_text"],
                    record["avatar_url"],
                    record["status"],
                    record["user_id"],
                ),
            )
            created = uow.query_one("SELECT * FROM voices WHERE id = ?", (record["id"],))
        return created or {}

    def update(self, voice_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        set_clauses: List[str] = []
        params: List[Any] = []
        for key in _UPDATABLE_VOICE_FIELDS:
            if key in updates and updates[key] is not None:
                set_clauses.append(f"{key} = ?")
                params.append(updates[key])

        if not set_clauses:
            return self.get_by_id(voice_id)

        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        params.append(voice_id)
        with self._db.transaction() as uow:
            uow.execute(f"UPDATE voices SET {', '.join(set_clauses)} WHERE id = ?", tuple(params))
            return uow.query_one("SELECT * FROM voices WHERE id = ?", (voice_id,))

    def delete(self, voice_id: str) -> None:
        self._db.execute_commit("DELETE FROM voices WHERE id = ?", (voice_id,))
