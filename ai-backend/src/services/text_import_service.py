"""
Unified Text File Import Service for ChatJPT
Supports importing text files (.md, .markdown, .txt, .rst, .json, .yaml, .yml, .toml, .xml, .csv)
into Rules Library and System Prompts Library.
"""

import os
import re
import json
import uuid
import yaml
import logging
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from fastapi import HTTPException, status

from src.db import query_one, execute_commit
from src.services.rule_service import (
    RuleService,
    RuleCreateRequest,
    RuleResponse
)

logger = logging.getLogger("text_import_service")

# Allowlisted text file extensions (lowercase)
ALLOWED_TEXT_EXTENSIONS = {
    ".md",
    ".markdown",
    ".txt",
    ".rst",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".xml",
    ".csv"
}

# 5 MB maximum file size limit
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024

def split_frontmatter_and_body(content: str) -> Tuple[Optional[str], str]:
    """Splits YAML frontmatter (if present) from markdown/text body."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[1].strip(), parts[2].strip()
    return None, content


class TextFileImportRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255, description="Tên tệp gốc kèm phần mở rộng")
    content: str = Field(..., min_length=1, description="Toàn bộ nội dung văn bản thuần túy của tệp")
    target: Optional[str] = Field(default=None, description="Mục tiêu nhập: 'rule' hoặc 'prompt'")
    override_name: Optional[str] = Field(default=None, max_length=100, description="Tên hiển thị tùy chỉnh ghi đè")
    name: Optional[str] = Field(default=None, max_length=100, description="Tên hiển thị tùy chỉnh")
    override_description: Optional[str] = Field(default=None, max_length=500, description="Mô tả tóm tắt tùy chỉnh ghi đè")
    description: Optional[str] = Field(default=None, max_length=500, description="Mô tả tóm tắt")
    activation_mode: Optional[str] = Field(default=None, description="Chế độ kích hoạt cho Rule")
    glob_patterns: Optional[List[str]] = Field(default_factory=list, description="Danh sách glob patterns")
    tags: Optional[List[str]] = Field(default_factory=list, description="Danh sách tags cho Rule")
    priority: Optional[int] = Field(default=None, ge=0, le=100, description="Mức độ ưu tiên cho Rule")


class TextImportService:
    @classmethod
    def validate_and_decode_bytes(cls, filename: str, content_bytes: bytes) -> str:
        cls.validate_file_extension(filename)
        cls.validate_file_size(len(content_bytes))
        # Check for binary signatures (null bytes or ELF/PE magic)
        sample = content_bytes[:4096]
        if b"\x00" in sample:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tệp có dấu hiệu chứa dữ liệu nhị phân hoặc không thể giải mã văn bản thuần túy."
            )
        return cls.decode_and_normalize_text(content_bytes)

    @staticmethod
    def validate_file_extension(filename: str) -> str:
        base, ext = os.path.splitext(filename or "")
        ext_lower = ext.lower()
        if not ext_lower or ext_lower not in ALLOWED_TEXT_EXTENSIONS:
            allowed_list = sorted(list(ALLOWED_TEXT_EXTENSIONS))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Phần mở rộng tệp '{ext}' không được hỗ trợ. Chỉ chấp nhận các định dạng văn bản: {', '.join(allowed_list)}."
            )
        return ext_lower

    @staticmethod
    def validate_file_size(content_bytes_len: int) -> None:
        if content_bytes_len > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Dung lượng tệp vượt quá giới hạn tối đa cho phép là 5 MB."
            )

    @staticmethod
    def decode_and_normalize_text(raw_bytes: bytes) -> str:
        if not raw_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tệp rỗng hoặc không có dữ liệu để nhập."
            )

        text = None
        for enc in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                text = raw_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể giải mã tệp văn bản. Tệp phải ở định dạng mã hóa UTF-8 hợp lệ."
            )

        text = text.lstrip("\ufeff")
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        if not normalized.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nội dung tệp rỗng hoặc chỉ chứa khoảng trắng."
            )

        return normalized

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
    def import_rule(
        cls,
        user_id: str,
        filename: str,
        content: str,
        override_name: Optional[str] = None,
        override_desc: Optional[str] = None,
        activation_mode: str = "always_on",
        glob_patterns: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        priority: Optional[int] = None
    ) -> RuleResponse:
        meta_dict, body, suggested = cls.extract_title_and_frontmatter(filename, content)
        rule_name = (override_name or (meta_dict.get("name") if meta_dict else None) or suggested).strip()
        if not rule_name:
            rule_name = "Imported Rule"
        rule_name = rule_name[:100]

        description = override_desc or (meta_dict.get("description") if meta_dict else None)
        if description:
            description = str(description).strip()[:500]

        final_content = body.strip() or content.strip()

        act_mode = (
            activation_mode
            if activation_mode and activation_mode != "always_on"
            else ((meta_dict.get("activation_mode") if meta_dict else None) or activation_mode or "always_on")
        )
        globs = glob_patterns or (meta_dict.get("glob_patterns") if meta_dict else None) or []
        tgs = tags or (meta_dict.get("tags") if meta_dict else None) or []
        prio = priority if priority is not None else ((meta_dict.get("priority") if meta_dict else None) or 50)

        create_req = RuleCreateRequest(
            name=rule_name,
            description=description,
            content=final_content,
            activation_mode=act_mode,
            glob_patterns=globs,
            tags=tgs,
            priority=prio
        )
        return RuleService.create_rule(user_id=user_id, req=create_req)

    @classmethod
    def import_system_prompt(
        cls,
        user_id: str,
        filename: str,
        content: str,
        override_name: Optional[str] = None,
        override_desc: Optional[str] = None
    ) -> Dict[str, Any]:
        meta_dict, body, suggested = cls.extract_title_and_frontmatter(filename, content)
        prompt_name = (override_name or (meta_dict.get("name") if meta_dict else None) or suggested).strip()
        if not prompt_name:
            prompt_name = "Imported Prompt"
        prompt_name = prompt_name[:100]

        description = override_desc or (meta_dict.get("description") if meta_dict else None)
        if description:
            description = str(description).strip()[:500]

        final_content = body.strip() or content.strip()

        existing = query_one(
            "SELECT id FROM system_prompts WHERE user_id = ? AND name = ? COLLATE NOCASE",
            (user_id, prompt_name)
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"System Prompt mang tên '{prompt_name}' đã tồn tại trong tài khoản của bạn."
            )

        new_id = str(uuid.uuid4())
        sql = "INSERT INTO system_prompts (id, user_id, name, description, content) VALUES (?, ?, ?, ?, ?)"
        execute_commit(sql, (new_id, user_id, prompt_name, description, final_content))

        row = query_one(
            "SELECT id, user_id, name, description, content, created_at, updated_at FROM system_prompts WHERE id = ?",
            (new_id,)
        )
        return dict(row)
