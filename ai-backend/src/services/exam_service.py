"""Exam & Reference Material Application Service (SRP, DIP, Anti-Cheat, Safe File Serving)."""

import json
import logging
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from src.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from src.core.security import is_admin_user
from src.models.v1.exam import ExamEntity, ExamQuestionEntity, ReferenceMaterialEntity
from src.repositories.exam_repo import ExamRepository
from src.schemas.v1.exams import (
    ExamCreateRequest,
    ExamDetailResponse,
    ExamListResponse,
    ExamSubmissionRequest,
    ExamSubmissionResult,
    ExamSummaryResponse,
    ExamUpdateRequest,
    QuestionResultItem,
    ReferenceMaterialCreateRequest,
    ReferenceMaterialItem,
    ReferenceMaterialListResponse,
)
from src.services.rag_exam_service import RagExamService

logger = logging.getLogger("exam_service")

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
MATERIALS_DIR = DATA_DIR / "reference_materials"


def _is_safe_http_url(url: Optional[str]) -> bool:
    if not url:
        return False
    parsed = urlparse(url.strip())
    return parsed.scheme in ("http", "https") and bool(parsed.hostname)


def _is_authenticated_owner_or_admin(owner_id: Optional[str], current_user: Optional[Dict[str, Any]]) -> bool:
    if not current_user:
        return False
    uid = current_user.get("id")
    if not uid or uid in ("guest_user", "system"):
        return False
    if is_admin_user(current_user):
        return True
    return bool(owner_id and owner_id == uid)


class ExamService:
    """Orchestrates JLPT mock exams, interactive grading, reference materials, and RAG search."""

    def __init__(
        self,
        repo: ExamRepository,
        *,
        data_dir: Path = DATA_DIR,
        project_root: Path = PROJECT_ROOT,
    ):
        self._repo = repo
        self._data_dir = data_dir
        self._materials_dir = data_dir / "reference_materials"
        self._project_root = project_root.resolve()
        self._manifest_cache: Optional[Dict[str, Any]] = None
        self._manifest_mtime: float = -1.0

    def _load_manifest(self) -> Dict[str, Any]:
        manifest_path = self._data_dir / "download_manifest.json"
        if not manifest_path.exists():
            return {}
        try:
            mtime = manifest_path.stat().st_mtime
            if self._manifest_cache is not None and mtime == self._manifest_mtime:
                return self._manifest_cache
            with open(manifest_path, "r", encoding="utf-8") as f:
                self._manifest_cache = json.load(f)
            self._manifest_mtime = mtime
            return self._manifest_cache or {}
        except Exception as exc:
            logger.warning("Error reading download_manifest.json: %s", exc)
            return {}

    def _ensure_within_project(self, candidate: Path) -> Optional[Path]:
        try:
            resolved = candidate.resolve()
            resolved.relative_to(self._project_root)
            if resolved.exists() and resolved.is_file():
                return resolved
        except (ValueError, OSError):
            return None
        return None

    def resolve_material_file(self, mat_id: str) -> Optional[Path]:
        """Safely resolves a local physical PDF/document matching mat_id within PROJECT_ROOT."""
        clean_id = (mat_id or "").strip()
        if not clean_id or ".." in clean_id or "/" in clean_id or "\\" in clean_id:
            return None

        manifest = self._load_manifest()
        norm_mat = clean_id.replace("mat_", "")
        for lvl, items in manifest.items():
            if not isinstance(items, list):
                continue
            for item in items:
                safe_name = item.get("safe_name", "")
                stem = Path(safe_name).stem
                candidate_id = f"loc_{lvl.lower()}_{re.sub(r'[^a-zA-Z0-9]', '_', stem)[:28].strip('_').lower()}"
                if candidate_id == clean_id or norm_mat == candidate_id:
                    rel_local = item.get("local_path", "")
                    if rel_local:
                        safe_path = self._ensure_within_project(self._project_root / rel_local)
                        if safe_path:
                            return safe_path

        # Fallback exact/prefix match inside MATERIALS_DIR
        if self._materials_dir.exists():
            low_id = clean_id.lower()
            for p in self._materials_dir.rglob("*.pdf"):
                stem_slug = re.sub(r"[^a-zA-Z0-9]", "_", p.stem)[:28].strip("_").lower()
                if low_id == p.stem.lower() or (stem_slug and stem_slug in low_id):
                    safe_path = self._ensure_within_project(p)
                    if safe_path:
                        return safe_path
        return None

    # ------------------------------------------------------------------
    # Reference Materials & RAG
    # ------------------------------------------------------------------
    def list_materials(
        self,
        *,
        category: Optional[str] = None,
        level: Optional[str] = None,
        search: Optional[str] = None,
    ) -> ReferenceMaterialListResponse:
        rows = self._repo.list_materials(category=category, level=level, search=search)
        items = [
            ReferenceMaterialItem.from_entity(
                ReferenceMaterialEntity.from_material_row(
                    r,
                    default_author="Kho học liệu tiếng Nhật ChatJPT",
                    compute_size_display=True,
                )
            )
            for r in rows
        ]
        return ReferenceMaterialListResponse(total=len(items), items=items)

    def resolve_material_asset(self, material_id: str) -> Tuple[str, Any]:
        """Returns ('file', Path) or ('redirect', safe_http_url), else raises NotFoundError."""
        file_path = self.resolve_material_file(material_id)
        if file_path:
            return "file", file_path

        row = self._repo.get_material_by_id(material_id)
        if row and _is_safe_http_url(row.get("external_url")):
            return "redirect", row["external_url"].strip()
        raise NotFoundError("Không tìm thấy tệp tài liệu nội bộ")

    def create_material(
        self,
        payload: ReferenceMaterialCreateRequest,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> ReferenceMaterialItem:
        mat_id = f"mat_{uuid.uuid4().hex[:12]}"
        user_id = current_user.get("id") if current_user else "user"
        created = self._repo.create_material(
            {
                "id": mat_id,
                "title": payload.title,
                "description": payload.description,
                "category": payload.category,
                "level": payload.level or "ALL",
                "source_type": payload.source_type or "LOCAL_FILE",
                "external_url": payload.external_url,
                "author": payload.author,
                "file_type": payload.file_type or "pdf",
                "tags": payload.tags,
                "is_pinned": bool(payload.is_pinned),
                "user_id": user_id,
            }
        )
        return ReferenceMaterialItem.from_entity(
            ReferenceMaterialEntity.from_material_row(
                created,
                force_system_preset=False,
                user_id_override=user_id,
            )
        )

    def delete_material(
        self,
        material_id: str,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        existing = self._repo.get_material_by_id(material_id)
        if not existing:
            raise NotFoundError("Không tìm thấy tài liệu tham khảo")
        if existing.get("is_system_preset"):
            raise ForbiddenError("Không thể xóa tài liệu tham khảo hệ thống")
        owner_id = existing.get("user_id")
        if owner_id and owner_id not in ("user", "guest_user", "system"):
            if not _is_authenticated_owner_or_admin(owner_id, current_user):
                raise ForbiddenError("Bạn không có quyền xóa tài liệu tham khảo của người dùng khác")

        self._repo.delete_material(material_id)
        return {"message": "Đã xóa tài liệu tham khảo thành công", "id": material_id}

    def search_rag(self, *, query: str, level: Optional[str] = None, limit: int = 6) -> Dict[str, Any]:
        results = RagExamService.search_rag(query=query, level=level, limit=limit)
        return {
            "query": query,
            "level": level or "ALL",
            "total": len(results),
            "results": results,
        }

    # ------------------------------------------------------------------
    # Exams CRUD & Interactive Auto-Scoring
    # ------------------------------------------------------------------
    def list_exams(
        self,
        *,
        level: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> ExamListResponse:
        rows = self._repo.list_exams_with_counts(level=level, category=category, search=search)
        items = [
            ExamSummaryResponse.from_entity(
                ExamEntity.from_exam_row(
                    r,
                    total_questions_override=int(r.get("actual_q_count", r.get("total_questions", 0))),
                    default_is_preset=1,
                )
            )
            for r in rows
        ]
        return ExamListResponse(total=len(items), items=items)

    def get_exam_detail(
        self,
        exam_id: str,
        *,
        include_answers: bool = False,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> ExamDetailResponse:
        exam = self._repo.get_exam_by_id(exam_id)
        if not exam:
            raise NotFoundError("Không tìm thấy đề thi yêu cầu")

        # CTRL-EXAM-03 Anti-Cheat: only allow answer key exposure for custom exam owner or admin
        can_expose_answers = False
        if include_answers:
            if current_user and is_admin_user(current_user):
                can_expose_answers = True
            elif not exam.get("is_system_preset") and _is_authenticated_owner_or_admin(
                exam.get("user_id"), current_user
            ):
                can_expose_answers = True

        questions_raw = self._repo.list_questions(exam_id)
        question_entities = [
            ExamQuestionEntity.from_question_row(q, include_answers=can_expose_answers)
            for q in questions_raw
        ]
        exam_entity = ExamEntity.from_exam_row(
            exam,
            total_questions_override=len(question_entities),
            default_is_preset=1,
        )
        return ExamDetailResponse.from_entities(exam_entity, question_entities)

    def create_exam(
        self,
        payload: ExamCreateRequest,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> ExamSummaryResponse:
        exam_id = f"exam_{uuid.uuid4().hex[:12]}"
        user_id = current_user.get("id") if current_user else "user"
        created = self._repo.create_exam(
            {
                "id": exam_id,
                "title": payload.title,
                "description": payload.description,
                "level": payload.level,
                "category": payload.category or "JLPT_FULL",
                "year": payload.year or 2024,
                "duration_minutes": payload.duration_minutes or 60,
                "passing_score": payload.passing_score or 90,
                "max_score": payload.max_score or 180,
                "drive_folder_url": payload.drive_folder_url,
                "status": payload.status or "ACTIVE",
                "user_id": user_id,
            }
        )
        return ExamSummaryResponse.from_entity(
            ExamEntity.from_exam_row(
                created,
                total_questions_override=0,
                default_is_preset=0,
                user_id_override=user_id,
            )
        )

    def update_exam(
        self,
        exam_id: str,
        payload: ExamUpdateRequest,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> ExamSummaryResponse:
        existing = self._repo.get_exam_by_id(exam_id)
        if not existing:
            raise NotFoundError("Không tìm thấy đề thi cần sửa")
        if existing.get("is_system_preset") and not (current_user and is_admin_user(current_user)):
            raise ForbiddenError("Không có quyền chỉnh sửa bộ đề thi mặc định của hệ thống (BR-044)")
        owner_id = existing.get("user_id")
        if owner_id and owner_id not in ("user", "guest_user", "system"):
            if not _is_authenticated_owner_or_admin(owner_id, current_user):
                raise ForbiddenError("Bạn không có quyền chỉnh sửa đề thi của người dùng khác")

        updated = self._repo.update_exam(exam_id, payload.model_dump(exclude_unset=True)) or existing
        return ExamSummaryResponse.from_entity(ExamEntity.from_exam_row(updated, default_is_preset=0))

    def delete_exam(
        self,
        exam_id: str,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        existing = self._repo.get_exam_by_id(exam_id)
        if not existing:
            raise NotFoundError("Không tìm thấy đề thi")
        if existing.get("is_system_preset"):
            raise ForbiddenError("Không thể xóa bộ đề thi mặc định của hệ thống (BR-044)")
        owner_id = existing.get("user_id")
        if owner_id and owner_id not in ("user", "guest_user", "system"):
            if not _is_authenticated_owner_or_admin(owner_id, current_user):
                raise ForbiddenError("Bạn không có quyền xóa đề thi của người dùng khác")

        self._repo.delete_exam(exam_id)
        return {"message": "Đã xóa đề thi thành công", "id": exam_id}

    def submit_exam(self, exam_id: str, payload: ExamSubmissionRequest) -> ExamSubmissionResult:
        exam = self._repo.get_exam_by_id(exam_id)
        if not exam:
            raise NotFoundError("Không tìm thấy đề thi")

        questions = self._repo.list_questions(exam_id)
        if not questions:
            raise BadRequestError("Đề thi này hiện chưa có câu hỏi nào để chấm điểm")

        total_questions = len(questions)
        correct_count = 0
        answered_count = 0
        results: List[QuestionResultItem] = []

        for q in questions:
            q_id = q["id"]
            correct_answer = q["correct_option"]
            user_ans = payload.answers.get(q_id)
            if user_ans is not None:
                answered_count += 1
                is_correct = user_ans in (1, 2, 3, 4) and user_ans == correct_answer
            else:
                is_correct = False
            if is_correct:
                correct_count += 1

            results.append(
                QuestionResultItem(
                    question_id=q_id,
                    user_answer=user_ans,
                    correct_answer=correct_answer,
                    is_correct=is_correct,
                    explanation=q.get("explanation"),
                )
            )

        max_score = exam["max_score"] or 180
        passing_score = exam["passing_score"] or 90
        score = int(round((correct_count / total_questions) * max_score)) if total_questions > 0 else 0
        passed = score >= passing_score
        percentage = round((correct_count / total_questions) * 100, 1) if total_questions > 0 else 0.0

        feedback = self._build_feedback(score, max_score, percentage)
        return ExamSubmissionResult(
            exam_id=exam_id,
            total_questions=total_questions,
            answered_count=answered_count,
            correct_count=correct_count,
            score=score,
            max_score=max_score,
            passing_score=passing_score,
            passed=passed,
            feedback_message=feedback,
            results=results,
        )

    @staticmethod
    def _build_feedback(score: int, max_score: int, percentage: float) -> str:
        if percentage >= 90:
            return (
                f"Subarashii! (素晴らしい!) Bạn đạt {score}/{max_score} điểm ({percentage}%). "
                "Kiến thức rất vững vàng, chúc bạn tiếp tục phát huy!"
            )
        if percentage >= 70:
            return (
                f"Yoku dekimashita! (よくできました!) Bạn đạt {score}/{max_score} điểm ({percentage}%). "
                "Đã vượt qua điểm chuẩn đỗ, hãy xem lại các câu giải thích để hoàn thiện hơn."
            )
        if percentage >= 50:
            return (
                f"Mou sukoshi desu! (もう少しです!) Bạn đạt {score}/{max_score} điểm ({percentage}%). "
                "Hãy ôn luyện kỹ lại phần ngữ pháp và từ vựng qua kho tài liệu tham khảo nhé!"
            )
        return (
            f"Ganbatte kudasai! (頑張ってください!) Bạn đạt {score}/{max_score} điểm ({percentage}%). "
            "Đừng nản lòng, hãy cùng Sensei ôn tập lại từ bài học căn bản!"
        )
