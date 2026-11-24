"""Pure Text File Import Parser & Orchestrator (decoupled from raw SQL and HTTPException)."""

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import yaml

from src.core.exceptions import BadRequestError, PayloadTooLargeError
from src.schemas.v1.prompts import SystemPromptCreateRequest, SystemPromptDetailResponse
from src.schemas.v1.rules import RuleCreateRequest, RuleResponse
from src.schemas.v1.text_import import TextFileImportRequest
from src.services.prompt_service import PromptService
from src.services.rule_service import RuleService

ALLOWED_TEXT_EXTENSIONS = {
    ".md", ".markdown", ".txt", ".rst", ".json",
    ".yaml", ".yml", ".toml", ".xml", ".csv",
}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024


def split_frontmatter_and_body(content: str) -> Tuple[Optional[str], str]:
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[1].strip(), parts[2].strip()
    return None, content


@dataclass(frozen=True)
class ParsedTextDocument:
    filename: str
    raw_content: str
    body: str
    suggested_title: str
    frontmatter: Optional[Dict[str, Any]]


class TextImportService:
    """Validates/decodes text uploads and delegates entity persistence to domain services."""

    def __init__(
        self,
        rule_service: Optional[RuleService] = None,
        prompt_service: Optional[PromptService] = None,
    ):
        self._rule_service = rule_service
        self._prompt_service = prompt_service

    @staticmethod
    def validate_file_extension(filename: str) -> str:
        _, ext = os.path.splitext(filename or "")
        ext_lower = ext.lower()
        if not ext_lower or ext_lower not in ALLOWED_TEXT_EXTENSIONS:
            allowed_list = sorted(ALLOWED_TEXT_EXTENSIONS)
            raise BadRequestError(
                f"Phần mở rộng tệp '{ext}' không được hỗ trợ. Chỉ chấp nhận các định dạng văn bản: {', '.join(allowed_list)}."
            )
        return ext_lower

    @staticmethod
    def validate_file_size(content_bytes_len: int) -> None:
        if content_bytes_len > MAX_FILE_SIZE_BYTES:
            raise PayloadTooLargeError("Dung lượng tệp vượt quá giới hạn tối đa cho phép là 5 MB.")

    @staticmethod
    def decode_and_normalize_text(raw_bytes: bytes) -> str:
        if not raw_bytes:
            raise BadRequestError("Tệp rỗng hoặc không có dữ liệu để nhập.")

        try:
            text = raw_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw_bytes.decode("latin-1")

        normalized = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
        if not normalized.strip():
            raise BadRequestError("Nội dung tệp rỗng hoặc chỉ chứa khoảng trắng.")
        return normalized

    @classmethod
    def validate_and_decode_bytes(cls, filename: str, content_bytes: bytes) -> str:
        cls.validate_file_extension(filename)
        cls.validate_file_size(len(content_bytes))
        if b"\x00" in content_bytes[:4096]:
            raise BadRequestError("Tệp có dấu hiệu chứa dữ liệu nhị phân hoặc không thể giải mã văn bản thuần túy.")
        return cls.decode_and_normalize_text(content_bytes)

    @staticmethod
    def extract_title_and_frontmatter(filename: str, content: str) -> Tuple[Optional[dict], str, str]:
        frontmatter_text, body = split_frontmatter_and_body(content)
        meta_dict = None
        if frontmatter_text:
            try:
                parsed = yaml.safe_load(frontmatter_text)
                if isinstance(parsed, dict):
                    meta_dict = parsed
            except Exception:
                pass

        suggested_title = ""
        if meta_dict:
            suggested_title = str(meta_dict.get("name") or meta_dict.get("title") or "").strip()

        if not suggested_title:
            for line in body.split("\n"):
                stripped = line.strip()
                if stripped.startswith("#"):
                    heading_text = stripped.lstrip("#").strip()
                    if heading_text:
                        suggested_title = heading_text[:100]
                        break

        if not suggested_title:
            base_name, _ = os.path.splitext(os.path.basename(filename or "untitled"))
            suggested_title = base_name.replace("_", " ").replace("-", " ").strip()

        return meta_dict, body, suggested_title

    @classmethod
    def parse_document(cls, filename: str, content: str) -> ParsedTextDocument:
        meta_dict, body, suggested = cls.extract_title_and_frontmatter(filename, content)
        return ParsedTextDocument(
            filename=filename,
            raw_content=content,
            body=body,
            suggested_title=suggested,
            frontmatter=meta_dict,
        )

    def import_rule_instance(
        self,
        *,
        user_id: str,
        filename: str,
        content: str,
        override_name: Optional[str] = None,
        override_desc: Optional[str] = None,
        activation_mode: Optional[str] = None,
        glob_patterns: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        priority: Optional[int] = None,
    ) -> RuleResponse:
        doc = self.parse_document(filename, content)
        meta = doc.frontmatter or {}

        rule_name = (override_name or meta.get("name") or doc.suggested_title or "Imported Rule").strip()[:100]
        description = override_desc or meta.get("description")
        description = str(description).strip()[:500] if description else None
        final_content = doc.body.strip() or doc.raw_content.strip()

        act_mode = (
            activation_mode
            if activation_mode and activation_mode != "always_on"
            else (meta.get("activation_mode") or activation_mode or "always_on")
        )
        globs = glob_patterns or meta.get("glob_patterns") or []
        tgs = tags or meta.get("tags") or []
        prio = priority if priority is not None else (meta.get("priority") if meta.get("priority") is not None else 50)

        create_req = RuleCreateRequest(
            name=rule_name,
            description=description,
            content=final_content,
            activation_mode=act_mode,
            glob_patterns=globs,
            tags=tgs,
            priority=prio,
        )
        if self._rule_service is not None:
            return self._rule_service.create_rule_instance(user_id=user_id, req=create_req)
        return RuleService.create_rule(user_id=user_id, req=create_req)

    def import_prompt_instance(
        self,
        *,
        user_id: str,
        filename: str,
        content: str,
        override_name: Optional[str] = None,
        override_desc: Optional[str] = None,
    ) -> SystemPromptDetailResponse:
        doc = self.parse_document(filename, content)
        meta = doc.frontmatter or {}

        prompt_name = (override_name or meta.get("name") or doc.suggested_title or "Imported Prompt").strip()[:100]
        description = override_desc or meta.get("description")
        description = str(description).strip()[:500] if description else None
        final_content = doc.body.strip() or doc.raw_content.strip()

        create_req = SystemPromptCreateRequest(
            name=prompt_name,
            description=description,
            content=final_content,
        )
        prompt_svc = self._prompt_service
        if prompt_svc is None:
            from src.repositories.attachment_repo import AttachmentRepository
            from src.repositories.prompt_repo import PromptRepository

            prompt_svc = PromptService(PromptRepository(), AttachmentRepository())
        return prompt_svc.create_prompt(user_id=user_id, payload=create_req)

    # Backward-compatible classmethods
    @classmethod
    def import_rule(cls, **kwargs: Any) -> RuleResponse:
        return cls().import_rule_instance(**kwargs)

    @classmethod
    def import_system_prompt(cls, **kwargs: Any) -> Dict[str, Any]:
        return cls().import_prompt_instance(**kwargs).model_dump()


__all__ = [
    "ALLOWED_TEXT_EXTENSIONS",
    "MAX_FILE_SIZE_BYTES",
    "split_frontmatter_and_body",
    "ParsedTextDocument",
    "TextFileImportRequest",
    "TextImportService",
]
