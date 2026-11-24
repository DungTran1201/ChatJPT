"""Atomic .env file adapter with allowlist & newline-injection protection."""

import logging
import os
import re
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Set

from src.core.config import settings
from src.services.provider_registry import ALLOWLISTED_SYSTEM_ENV_VARS

logger = logging.getLogger("chatjpt.env_file_store")


class EnvFileStore:
    """Safely updates allowlisted environment variables in .env using atomic replace."""

    def __init__(
        self,
        env_path: Optional[Path] = None,
        allowlisted_vars: Optional[Set[str]] = None,
    ):
        self._explicit_path = env_path
        self._allowlisted = allowlisted_vars or ALLOWLISTED_SYSTEM_ENV_VARS

    def resolve_env_path(self) -> Path:
        if self._explicit_path is not None:
            return self._explicit_path
        backend_dir = Path(__file__).resolve().parent.parent.parent
        env_file = backend_dir / ".env"
        if env_file.exists():
            return env_file
        root_env = backend_dir.parent / ".env"
        if root_env.exists():
            return root_env
        return env_file

    def update_variable(self, env_var: str, new_value: str) -> Dict[str, Any]:
        env_var_clean = (env_var or "").strip().upper()
        if env_var_clean not in self._allowlisted:
            raise ValueError(
                f"Biến '{env_var_clean}' không nằm trong danh mục biến toàn cục được phép cập nhật."
            )

        raw_val = new_value or ""
        if "\n" in raw_val or "\r" in raw_val or "\x00" in raw_val:
            raise ValueError("Giá trị biến môi trường không được chứa ký tự xuống dòng hoặc ký tự điều khiển.")
        val_clean = raw_val.strip()

        env_file = self.resolve_env_path()
        bak_file = env_file.with_suffix(".env.bak")
        lines = []
        if env_file.exists():
            shutil.copy2(env_file, bak_file)
            with open(env_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

        key_pattern = re.compile(rf"^\s*{re.escape(env_var_clean)}\s*=", re.IGNORECASE)
        found = False
        new_lines = []
        for line in lines:
            if key_pattern.match(line):
                new_lines.append(f"{env_var_clean}={val_clean}\n")
                found = True
            else:
                new_lines.append(line)

        if not found:
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines.append("\n")
            new_lines.append(f"{env_var_clean}={val_clean}\n")

        tmp_file = env_file.with_name(f".env.{uuid.uuid4().hex[:8]}.tmp")
        try:
            with open(tmp_file, "w", encoding="utf-8") as tf:
                tf.writelines(new_lines)
                tf.flush()
                os.fsync(tf.fileno())
            os.replace(tmp_file, env_file)
        finally:
            if tmp_file.exists():
                try:
                    tmp_file.unlink()
                except Exception:
                    pass

        if hasattr(settings, env_var_clean):
            setattr(settings, env_var_clean, val_clean)
        os.environ[env_var_clean] = val_clean

        logger.info("System environment variable %s safely updated via atomic write.", env_var_clean)
        return {
            "env_var": env_var_clean,
            "restart_required": True,
            "message": (
                f"Đã cập nhật {env_var_clean} vào .env thành công. "
                "Vui lòng khởi động lại dịch vụ backend/demo để áp dụng toàn diện cho các tiến trình phụ thuộc."
            ),
        }
