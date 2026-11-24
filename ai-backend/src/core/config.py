"""Application configuration loaded via pydantic-settings."""

from pathlib import Path
from typing import List, Set
from pydantic_settings import BaseSettings, SettingsConfigDict

_backend_dir = Path(__file__).resolve().parent.parent.parent
_env_path = str(_backend_dir / ".env") if (_backend_dir / ".env").exists() else ".env"


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "chatjpt-backend"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    SECRET_KEY: str = "insecure-default-change-me"
    AI_CHAN_SECRET_ENCRYPTION_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    COOKIE_SECURE: bool = False
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    ADMIN_EMAILS: str = ""

    DATABASE_URL: str = "sqlite:///./database/app.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM Settings
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_ALLOWED_HOSTS: str = "localhost,127.0.0.1,::1,host.docker.internal,ollama"
    DEFAULT_LLM_PROVIDER: str = "gemini"
    DEFAULT_LLM_MODEL: str = "gemini-3.5-flash-lite"

    # File Upload & Asset Settings
    MAX_FILE_SIZE_MB: int = 20
    MAX_FILES_PER_REQUEST: int = 5
    UPLOAD_DIR: str = ""

    model_config = SettingsConfigDict(
        env_file=_env_path,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def admin_emails(self) -> Set[str]:
        return {e.strip().lower() for e in self.ADMIN_EMAILS.split(",") if e.strip()}

    @property
    def ollama_allowed_hosts(self) -> Set[str]:
        return {h.strip().lower() for h in self.OLLAMA_ALLOWED_HOSTS.split(",") if h.strip()}


settings = Settings()
