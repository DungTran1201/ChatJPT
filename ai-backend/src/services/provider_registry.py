"""Unified Provider Registry + Strategy + Factory + SSRF Guard.

Single source of truth for LLM and Search provider metadata, alias resolution,
secret redaction, connectivity health probes, and LangChain chat model instantiation.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx

from src.core.config import settings
from src.core.secret_vault import mask_secret

logger = logging.getLogger("chatjpt.provider_registry")

ProbeFunc = Callable[[str, Optional[str]], Awaitable[None]]


def redact_secrets_from_text(text: str, secrets: Optional[List[Optional[str]]] = None) -> str:
    """Removes sensitive keys, Authorization tokens, and given secrets from strings."""
    if not text:
        return ""
    result = text
    if secrets:
        for s in secrets:
            if s and len(s) >= 4 and s in result:
                result = result.replace(s, f"[REDACTED_SECRET_{mask_secret(s)}]")
    result = re.sub(r"(AIzaSy[A-Za-z0-9_-]{30,45})", "[REDACTED_GEMINI_KEY]", result)
    result = re.sub(r"(sk-[A-Za-z0-9_-]{20,60})", "[REDACTED_API_KEY]", result)
    result = re.sub(r"(gsk_[A-Za-z0-9_-]{20,60})", "[REDACTED_GROQ_KEY]", result)
    result = re.sub(r"(Bearer\s+[A-Za-z0-9_.-]+)", "Bearer [REDACTED_TOKEN]", result, flags=re.IGNORECASE)
    return result


def validate_ollama_url(raw_url: str) -> str:
    """SSRF Guard: restricts Ollama base URLs to http(s) and allowlisted hosts."""
    url = (raw_url or "").strip().rstrip("/")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("URL Ollama không hợp lệ. Phải bắt đầu bằng http:// hoặc https:// kèm hostname hợp lệ.")
    host = parsed.hostname.lower()
    if host not in settings.ollama_allowed_hosts:
        raise ValueError(
            f"Hostname '{host}' không nằm trong danh mục OLLAMA_ALLOWED_HOSTS được phép (chống SSRF)."
        )
    return url


# ==============================================================================
# PROVIDER CONNECTIVITY PROBE STRATEGIES
# ==============================================================================

async def _probe_google(api_key: str, model_id: Optional[str] = None) -> None:
    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(
        model=model_id or "gemini-3.5-flash-lite",
        google_api_key=api_key,
        timeout=15.0,
        max_retries=0,
    )
    await llm.ainvoke("ping")


async def _probe_openai(api_key: str, model_id: Optional[str] = None) -> None:
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=model_id or "gpt-4o-mini",
        api_key=api_key,
        timeout=15.0,
        max_retries=0,
    )
    await llm.ainvoke("ping")


async def _probe_anthropic(api_key: str, model_id: Optional[str] = None) -> None:
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json={
                "model": model_id or "claude-3-7-sonnet-20250219",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "ping"}],
            },
        )
        if resp.status_code in (401, 403):
            raise ValueError(f"Khóa Anthropic không hợp lệ hoặc không có quyền (HTTP {resp.status_code}).")
        if resp.status_code >= 500:
            raise ValueError(f"Dịch vụ Anthropic gặp lỗi máy chủ (HTTP {resp.status_code}).")


async def _probe_groq(api_key: str, _model_id: Optional[str] = None) -> None:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get("https://api.groq.com/openai/v1/models", headers=headers)
        if resp.status_code in (401, 403):
            raise ValueError(f"Khóa Groq không hợp lệ hoặc đã hết hạn (HTTP {resp.status_code}).")
        if resp.status_code >= 400:
            raise ValueError(f"Groq trả về mã lỗi không mong đợi (HTTP {resp.status_code}).")


async def _probe_ollama(base_url: str, _model_id: Optional[str] = None) -> None:
    safe_url = validate_ollama_url(base_url)
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{safe_url}/api/tags")
        if resp.status_code != 200:
            raise ValueError(f"Ollama trả về mã trạng thái không mong đợi: HTTP {resp.status_code}")


async def _probe_brave(api_key: str, _model_id: Optional[str] = None) -> None:
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key,
    }
    async with httpx.AsyncClient(timeout=8.0) as client:
        resp = await client.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": "test", "count": 1},
            headers=headers,
        )
        if resp.status_code in (401, 403):
            raise ValueError(f"Khóa Brave Search không hợp lệ (HTTP {resp.status_code}).")
        if resp.status_code >= 400:
            raise ValueError(f"Brave Search trả về lỗi HTTP {resp.status_code}.")


async def _probe_serpapi(api_key: str, _model_id: Optional[str] = None) -> None:
    async with httpx.AsyncClient(timeout=8.0) as client:
        resp = await client.get("https://serpapi.com/account", params={"api_key": api_key})
        if resp.status_code in (401, 403):
            raise ValueError(f"Khóa SerpAPI không hợp lệ (HTTP {resp.status_code}).")
        if resp.status_code >= 400:
            raise ValueError(f"SerpAPI trả về lỗi HTTP {resp.status_code}.")


# ==============================================================================
# PROVIDER SPEC & REGISTRY
# ==============================================================================

@dataclass(frozen=True)
class ProviderSpec:
    id: str
    name: str
    category: str
    env_var: str
    description: str
    doc_url: str
    placeholder: str
    is_secret: bool = True
    aliases: Tuple[str, ...] = field(default_factory=tuple)
    env_aliases: Tuple[str, ...] = field(default_factory=tuple)
    default_model: Optional[str] = None
    probe: Optional[ProbeFunc] = None

    def to_metadata_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "id": self.id,
            "aliases": list(self.aliases),
            "name": self.name,
            "category": self.category,
            "env_var": self.env_var,
            "description": self.description,
            "doc_url": self.doc_url,
            "placeholder": self.placeholder,
            "is_secret": self.is_secret,
        }
        if self.default_model:
            data["default_model"] = self.default_model
        return data


class ProviderRegistry:
    """Open-Closed table-driven registry for LLM & Search providers."""

    def __init__(self, specs: List[ProviderSpec]):
        self._specs: Dict[str, ProviderSpec] = {s.id: s for s in specs}
        self._alias_map: Dict[str, str] = {}
        for s in specs:
            self._alias_map[s.id] = s.id
            for alias in s.aliases:
                self._alias_map[alias.lower()] = s.id

    def canonicalize(self, provider: Optional[str]) -> Optional[str]:
        if not provider:
            return None
        return self._alias_map.get(provider.lower().strip())

    def get(self, provider: str) -> Optional[ProviderSpec]:
        canon = self.canonicalize(provider)
        return self._specs.get(canon) if canon else None

    def all_specs(self) -> List[ProviderSpec]:
        return list(self._specs.values())

    @property
    def allowlisted_env_vars(self) -> set:
        return {s.env_var for s in self._specs.values()}

    def as_supported_dict(self) -> Dict[str, Dict[str, Any]]:
        return {sid: spec.to_metadata_dict() for sid, spec in self._specs.items()}

    async def probe(self, provider: str, api_key: str, model_id: Optional[str] = None) -> None:
        spec = self.get(provider)
        if not spec or not spec.probe:
            raise ValueError(f"Nhà cung cấp '{provider}' không hỗ trợ kiểm tra kết nối.")
        await spec.probe(api_key, model_id)

    def create_chat_model(
        self,
        provider: str,
        api_key: str,
        model_name: Optional[str] = None,
    ) -> Optional[Any]:
        """Factory creating a configured LangChain ChatModel for the given canonical provider."""
        canon = self.canonicalize(provider)
        if not canon or not api_key:
            return None

        if canon == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI

            target = model_name or settings.DEFAULT_LLM_MODEL or "gemini-3.8-flash"
            if target in ("gemini-1.5-flash", "gemini-2.5-flash"):
                target = "gemini-3.5-flash-lite"
            return ChatGoogleGenerativeAI(
                model=target,
                google_api_key=api_key,
                temperature=0.7,
                timeout=15.0,
                max_retries=1,
            )

        if canon == "groq":
            try:
                from langchain_groq import ChatGroq

                return ChatGroq(
                    model=model_name or "llama-3.3-70b-versatile",
                    api_key=api_key,
                    temperature=0.7,
                    timeout=20.0,
                )
            except Exception as err:
                logger.warning("Failed to initialize ChatGroq: %s", err)
                return None

        if canon == "openai":
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                model=model_name or "gpt-4o-mini",
                api_key=api_key,
                temperature=0.7,
                timeout=25.0,
            )

        if canon == "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic

                return ChatAnthropic(
                    model=model_name or "claude-3-5-haiku",
                    api_key=api_key,
                    temperature=0.7,
                    timeout=25.0,
                )
            except Exception as err:
                logger.warning("Failed to initialize ChatAnthropic: %s", err)
                return None

        if canon == "ollama":
            try:
                safe_url = validate_ollama_url(api_key)
                target = model_name or "qwen2.5-0.5b-cpu"
                if "qwen2.5-0.5b" in target:
                    tag = "qwen2.5:0.5b"
                elif "qwen2.5-1.5b" in target:
                    tag = "qwen2.5:1.5b"
                else:
                    tag = target
                from langchain_openai import ChatOpenAI

                return ChatOpenAI(
                    base_url=f"{safe_url}/v1",
                    api_key="ollama",
                    model=tag,
                    temperature=0.7,
                    timeout=6.0,
                    max_retries=0,
                )
            except Exception as err:
                logger.warning("Could not initialize Ollama model: %s", err)
                return None

        return None


provider_registry = ProviderRegistry(
    [
        ProviderSpec(
            id="google",
            aliases=("gemini",),
            env_aliases=("GOOGLE_API_KEY",),
            name="Google Gemini",
            category="LLM",
            env_var="GEMINI_API_KEY",
            description="API Key truy cập các mô hình Google Gemini (Gemini 3.5 Flash, 3.8 Flash, Flash Lite...)",
            doc_url="https://aistudio.google.com/app/apikey",
            placeholder="AIzaSy...",
            is_secret=True,
            default_model="gemini-3.5-flash-lite",
            probe=_probe_google,
        ),
        ProviderSpec(
            id="openai",
            name="OpenAI",
            category="LLM",
            env_var="OPENAI_API_KEY",
            description="API Key truy cập OpenAI GPT-4o, GPT-4o Mini và mô hình dự phòng (failover)",
            doc_url="https://platform.openai.com/api-keys",
            placeholder="sk-proj-...",
            is_secret=True,
            default_model="gpt-4o-mini",
            probe=_probe_openai,
        ),
        ProviderSpec(
            id="anthropic",
            aliases=("claude",),
            name="Anthropic Claude",
            category="LLM",
            env_var="ANTHROPIC_API_KEY",
            description="API Key truy cập các mô hình Claude 3.5 / 3.7 Sonnet từ Anthropic",
            doc_url="https://console.anthropic.com/settings/keys",
            placeholder="sk-ant-...",
            is_secret=True,
            default_model="claude-3-7-sonnet",
            probe=_probe_anthropic,
        ),
        ProviderSpec(
            id="groq",
            name="Groq Cloud",
            category="LLM",
            env_var="GROQ_API_KEY",
            description="API Key truy cập dịch vụ suy luận siêu tốc Groq (Llama 3.3 70B Versatile...)",
            doc_url="https://console.groq.com/keys",
            placeholder="gsk_...",
            is_secret=True,
            default_model="llama-3.3-70b-versatile",
            probe=_probe_groq,
        ),
        ProviderSpec(
            id="ollama",
            name="Ollama Local Service",
            category="LLM",
            env_var="OLLAMA_BASE_URL",
            description="URL endpoint máy chủ Ollama chạy trên máy tính cục bộ hoặc mạng LAN (mặc định: http://localhost:11434)",
            doc_url="https://ollama.com",
            placeholder="http://localhost:11434",
            is_secret=False,
            default_model="llama3",
            probe=_probe_ollama,
        ),
        ProviderSpec(
            id="brave",
            aliases=("brave_search",),
            name="Brave Search API",
            category="SEARCH",
            env_var="BRAVE_SEARCH_API_KEY",
            description="API Key tìm kiếm web độc lập bảo vệ quyền riêng tư cho Tool Tìm Kiếm Web",
            doc_url="https://brave.com/search/api/",
            placeholder="BSA...",
            is_secret=True,
            probe=_probe_brave,
        ),
        ProviderSpec(
            id="serpapi",
            name="SerpAPI (Google Search)",
            category="SEARCH",
            env_var="SERPAPI_API_KEY",
            description="API Key tìm kiếm dữ liệu web Google / Bing / Yahoo thông qua SerpAPI adapter",
            doc_url="https://serpapi.com/manage-api-key",
            placeholder="...",
            is_secret=True,
            probe=_probe_serpapi,
        ),
    ]
)

SUPPORTED_PROVIDERS = provider_registry.as_supported_dict()
ALLOWLISTED_SYSTEM_ENV_VARS = provider_registry.allowlisted_env_vars
canonicalize_provider = provider_registry.canonicalize
