"""Modular attachment storage: FileSecurityValidator, TextExtractor, LocalAttachmentStorage."""

import hashlib
import io
import logging
import mimetypes
import os
import re
import struct
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import filetype

from src.core.config import settings

logger = logging.getLogger("chatjpt.storage")

BLOCKED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".sh", ".bash", ".ps1", ".vbs", ".msi",
    ".dll", ".so", ".com", ".scr", ".pif", ".jar", ".app", ".dmg",
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"}

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".json",
    ".yaml", ".yml", ".xml", ".sql", ".rs", ".go", ".java", ".c",
    ".cpp", ".h", ".hpp", ".cs", ".rb", ".toml", ".ini", ".env",
}

TEXT_DOC_EXTENSIONS = {".txt", ".md", ".csv", ".rtf"}
BINARY_OFFICE_EXTENSIONS = {".docx", ".xlsx", ".pptx"}
DOC_EXTENSIONS = {".pdf"} | TEXT_DOC_EXTENSIONS | BINARY_OFFICE_EXTENSIONS


class FileSecurityValidator:
    """Sanitizes filenames, sniffs magic bytes, blocks executables, and classifies MIME/category."""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        if not filename:
            return "unnamed_file"
        clean = os.path.basename(filename.replace("\\", "/"))
        clean = re.sub(r"[\x00-\x1f\x7f]", "", clean)
        clean = re.sub(r'[<>:"/\\|?*]', "_", clean)
        clean = clean.strip(". ")
        if not clean:
            return "unnamed_file"
        if len(clean) > 200:
            stem, ext = os.path.splitext(clean)
            clean = stem[:180] + ext
        return clean

    @staticmethod
    def classify(content_bytes: bytes, filename: str) -> Tuple[str, str]:
        _, ext = os.path.splitext(filename.lower())
        if ext in BLOCKED_EXTENSIONS:
            raise ValueError(f"Tệp thực thi hoặc script '{ext}' bị chặn vì lý do bảo mật an toàn hệ thống.")

        if content_bytes.startswith(b"MZ") or content_bytes.startswith(b"\x7fELF"):
            raise ValueError("Phát hiện định dạng tệp thực thi nhị phân bị chặn (Binary Executable Signature).")

        kind = filetype.guess(content_bytes)
        detected_mime = kind.mime if kind else None

        if not detected_mime:
            guessed, _ = mimetypes.guess_type(filename)
            detected_mime = guessed

        if not detected_mime:
            if ext in CODE_EXTENSIONS or ext in {".txt", ".md", ".csv"}:
                detected_mime = "text/plain"
            else:
                detected_mime = "application/octet-stream"

        if detected_mime.startswith("image/") or ext in IMAGE_EXTENSIONS:
            category = "image"
        elif ext in CODE_EXTENSIONS or detected_mime in {
            "application/json", "application/javascript", "text/javascript",
            "text/x-python", "text/html", "text/css", "application/xml", "text/xml",
        }:
            category = "code"
        elif detected_mime == "application/pdf" or ext in DOC_EXTENSIONS:
            category = "document"
        elif detected_mime in {
            "application/zip", "application/x-tar", "application/gzip", "application/x-7z-compressed"
        } or ext in {".zip", ".tar", ".gz", ".7z"}:
            category = "archive"
        elif detected_mime.startswith("audio/"):
            category = "audio"
        elif detected_mime.startswith("video/"):
            category = "video"
        else:
            try:
                content_bytes[:1024].decode("utf-8")
                category = "document"
                if detected_mime == "application/octet-stream":
                    detected_mime = "text/plain"
            except UnicodeDecodeError:
                category = "other"

        return detected_mime, category


class TextExtractor:
    """Strategy-based text extraction from plain text, code, and PDFs (skips binary ZIP office files)."""

    MAX_TEXT_CHARS = 100000

    @classmethod
    def extract(
        cls,
        content_bytes: bytes,
        category: str,
        mime_type: str,
        filename: str,
    ) -> Optional[str]:
        low_name = (filename or "").lower()
        _, ext = os.path.splitext(low_name)

        if ext in BINARY_OFFICE_EXTENSIONS:
            return None

        if mime_type == "application/pdf" or ext == ".pdf":
            return cls._extract_pdf(content_bytes)

        if category in ("code", "document") and (
            mime_type.startswith("text/")
            or mime_type in ("application/json", "application/xml", "application/javascript")
            or ext in (TEXT_DOC_EXTENSIONS | CODE_EXTENSIONS)
        ):
            try:
                return content_bytes.decode("utf-8", errors="replace")[: cls.MAX_TEXT_CHARS]
            except Exception:
                return None

        return None

    @classmethod
    def _extract_pdf(cls, content_bytes: bytes) -> Optional[str]:
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(content_bytes))
            pages_text = []
            for idx in range(min(len(reader.pages), 30)):
                page_str = reader.pages[idx].extract_text() or ""
                if page_str.strip():
                    pages_text.append(f"--- Trang {idx + 1} ---\n{page_str.strip()}")
            full_pdf_text = "\n\n".join(pages_text)
            return full_pdf_text[: cls.MAX_TEXT_CHARS] if full_pdf_text else None
        except Exception:
            return None


class LocalAttachmentStorage:
    """Local filesystem adapter with path-traversal enforcement and atomic writes."""

    def __init__(self, base_dir: Optional[Path] = None):
        self._explicit_base = base_dir

    def get_base_dir(self) -> Path:
        if self._explicit_base is not None:
            base = self._explicit_base.resolve()
        elif settings.UPLOAD_DIR and settings.UPLOAD_DIR.strip():
            base = Path(settings.UPLOAD_DIR.strip()).resolve()
        else:
            base = Path(__file__).resolve().parent.parent.parent / "database" / "uploads"
        base.mkdir(parents=True, exist_ok=True)
        return base

    def resolve_safe_path(self, storage_path: str) -> Path:
        base_dir = self.get_base_dir()
        clean_rel = storage_path.lstrip("/\\")
        resolved = (base_dir / clean_rel).resolve()
        base_resolved = base_dir.resolve()
        try:
            resolved.relative_to(base_resolved)
        except ValueError:
            raise ValueError(f"Phát hiện truy cập đường dẫn tệp không an toàn (Path Traversal): {storage_path}")
        return resolved

    def save(self, _user_id: str, raw_filename: str, content_bytes: bytes) -> Dict[str, Any]:
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(content_bytes) > max_bytes:
            raise ValueError(
                f"Dung lượng tệp ({len(content_bytes) / (1024 * 1024):.1f} MB) vượt quá giới hạn tối đa cho phép ({settings.MAX_FILE_SIZE_MB} MB)."
            )
        if len(content_bytes) == 0:
            raise ValueError("Tệp tải lên rỗng (0 bytes).")

        clean_filename = FileSecurityValidator.sanitize_filename(raw_filename)
        mime_type, category = FileSecurityValidator.classify(content_bytes, clean_filename)
        checksum = hashlib.sha256(content_bytes).hexdigest()
        att_id = f"att_{uuid.uuid4().hex}"

        now = datetime.now(timezone.utc)
        rel_folder = f"{now.year}/{now.month:02d}"
        rel_path = f"{rel_folder}/{att_id}.dat"

        target_folder = self.get_base_dir() / rel_folder
        target_folder.mkdir(parents=True, exist_ok=True)
        target_file = target_folder / f"{att_id}.dat"
        tmp_file = target_folder / f".{att_id}.tmp"
        try:
            tmp_file.write_bytes(content_bytes)
            os.replace(tmp_file, target_file)
        finally:
            if tmp_file.exists():
                try:
                    tmp_file.unlink()
                except Exception:
                    pass

        extracted = TextExtractor.extract(content_bytes, category, mime_type, clean_filename)
        img_w, img_h = self._parse_image_dimensions(content_bytes, category)

        return {
            "id": att_id,
            "filename": clean_filename,
            "file_size": len(content_bytes),
            "mime_type": mime_type,
            "category": category,
            "storage_path": rel_path.replace("\\", "/"),
            "checksum_sha256": checksum,
            "status": "READY",
            "extracted_text": extracted,
            "image_width": img_w,
            "image_height": img_h,
        }

    def read_bytes(self, storage_path: str) -> bytes:
        path = self.resolve_safe_path(storage_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Tệp không tồn tại trên hệ thống lưu trữ: {storage_path}")
        return path.read_bytes()

    def delete(self, storage_path: str) -> bool:
        try:
            path = self.resolve_safe_path(storage_path)
            if path.exists() and path.is_file():
                path.unlink()
                return True
        except Exception as err:
            logger.warning("Could not delete attachment file '%s': %s", storage_path, err)
        return False

    @staticmethod
    def _parse_image_dimensions(content_bytes: bytes, category: str) -> Tuple[Optional[int], Optional[int]]:
        if category == "image" and len(content_bytes) > 24 and content_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            try:
                w, h = struct.unpack(">II", content_bytes[16:24])
                return int(w), int(h)
            except Exception:
                return None, None
        return None, None


default_storage = LocalAttachmentStorage()
