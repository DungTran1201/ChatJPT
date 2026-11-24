"""Chat Agent Orchestrator — Multi-provider failover, LangGraph workflow, and streaming engine."""

import asyncio
import logging
import os
from typing import Any, AsyncGenerator, Dict, List, Optional, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import END, StateGraph

from llm.circuit_breaker import ScopedModelQuotaTracker
from llm.message_builder import build_langchain_messages, extract_text_content
from src.services.provider_registry import provider_registry, redact_secrets_from_text

logger = logging.getLogger("ai_chan.agent")

_CANDIDATE_POOLS: Dict[str, List[str]] = {
    "gemini": [
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-flash-lite-latest",
    ],
    "google": [
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-flash-lite-latest",
    ],
    "groq": [
        "llama-3.3-70b-versatile",
        "mixtral-8x7b-32768",
    ],
    "openai": [
        "gpt-4o-mini",
        "gpt-4o",
    ],
    "anthropic": [
        "claude-3-5-haiku",
        "claude-3-7-sonnet",
    ],
    "ollama": [
        "qwen2.5-0.5b-cpu",
        "qwen2.5-1.5b-cpu",
        "llama3",
    ],
    "offline": ["offline-semantic-cache"],
}


class EnvKeyLoader:
    """Dynamically loads LLM provider keys and defaults from application settings / environment."""

    @staticmethod
    def get_config() -> Dict[str, Any]:
        try:
            from src.core.config import settings

            gemini_key = (settings.GEMINI_API_KEY or "").strip()
            openai_key = (settings.OPENAI_API_KEY or "").strip()
            anthropic_key = (settings.ANTHROPIC_API_KEY or "").strip()
            groq_key = (settings.GROQ_API_KEY or "").strip()
            ollama_url = (settings.OLLAMA_BASE_URL or "http://localhost:11434").strip()
            default_prov = (settings.DEFAULT_LLM_PROVIDER or "gemini").lower().strip()
            default_mod = (settings.DEFAULT_LLM_MODEL or "gemini-3.5-flash-lite").strip()
        except Exception:
            gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
            openai_key = os.getenv("OPENAI_API_KEY", "").strip()
            anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
            groq_key = os.getenv("GROQ_API_KEY", "").strip()
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
            default_prov = os.getenv("DEFAULT_LLM_PROVIDER", "gemini").lower().strip()
            default_mod = os.getenv("DEFAULT_LLM_MODEL", "gemini-3.5-flash-lite").strip()

        gemini_key = gemini_key or os.getenv("GEMINI_API_KEY", "").strip()
        openai_key = openai_key or os.getenv("OPENAI_API_KEY", "").strip()
        if default_mod in ("gemini-1.5-flash", "gemini-2.5-flash"):
            default_mod = "gemini-3.5-flash-lite"

        return {
            "gemini_api_key": gemini_key,
            "openai_api_key": openai_key,
            "anthropic_api_key": anthropic_key,
            "groq_api_key": groq_key,
            "ollama_base_url": ollama_url,
            "default_provider": default_prov,
            "default_model": default_mod,
        }

    @classmethod
    def get_available_providers(cls) -> List[str]:
        cfg = cls.get_config()
        mapping = [
            ("gemini", cfg["gemini_api_key"]),
            ("openai", cfg["openai_api_key"]),
            ("anthropic", cfg["anthropic_api_key"]),
            ("groq", cfg["groq_api_key"]),
        ]
        return [name for name, val in mapping if val]


class AgentChatState(TypedDict, total=False):
    """LangGraph state representation for chat message workflow."""

    messages: Sequence[BaseMessage]
    prompt: str
    history: List[Dict[str, Any]]
    target_model: str
    user_id: Optional[str]
    active_provider: str
    response_text: str
    error: Optional[str]
    failover_triggered: bool
    final_model: str


class LangChainModelFactory:
    """Delegates LangChain model instantiation to ProviderRegistry + CredentialService."""

    @staticmethod
    def detect_provider_for_model(model_name: Optional[str]) -> str:
        if not model_name:
            return "gemini"
        m = model_name.lower().strip()
        if "offline" in m or "cache" in m:
            return "offline"
        if "qwen" in m or "llama3" in m or "ollama" in m:
            return "ollama"
        if "llama-3.3" in m or "mixtral" in m or "groq" in m:
            return "groq"
        if "claude" in m or "anthropic" in m:
            return "anthropic"
        if "gpt" in m or "o1" in m or "o3" in m:
            return "openai"
        if "gemini" in m:
            return "gemini"
        return "gemini"

    @staticmethod
    def get_candidate_models(
        provider: str,
        target_model: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[str]:
        prov = (provider or "gemini").lower().strip()
        if prov == "offline":
            return ["offline-semantic-cache"]

        base_pool = _CANDIDATE_POOLS.get(prov, [])
        pool: List[Optional[str]] = [target_model, *base_pool] if target_model else list(base_pool)

        candidates: List[str] = []
        for m in pool:
            if m and m not in candidates and ScopedModelQuotaTracker.is_available(m, user_id=user_id):
                candidates.append(m)

        if not candidates and target_model:
            candidates.append(target_model)
        return candidates

    @staticmethod
    def create_model(
        provider: str,
        model_name: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[Any]:
        prov = (provider or "").lower().strip()
        canon = provider_registry.canonicalize(prov)
        if not canon:
            return None

        effective_key: Optional[str] = None
        try:
            from src.services.credential_service import CredentialService

            effective_key = CredentialService.get_effective_key(user_id, canon)
        except Exception:
            effective_key = None

        if not effective_key:
            cfg = EnvKeyLoader.get_config()
            fallback_map = {
                "google": cfg["gemini_api_key"],
                "openai": cfg["openai_api_key"],
                "anthropic": cfg["anthropic_api_key"],
                "groq": cfg["groq_api_key"],
                "ollama": cfg["ollama_base_url"],
            }
            effective_key = fallback_map.get(canon)

        if not effective_key:
            return None

        return provider_registry.create_chat_model(canon, effective_key, model_name=model_name)


class ChatAgentOrchestrator:
    """Stateful Chat Agent orchestrator with multi-provider failover and offline semantic cache."""

    def __init__(self):
        self.workflow = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(AgentChatState)

        def context_node(state: AgentChatState) -> Dict[str, Any]:
            msgs = build_langchain_messages(state["prompt"], state["history"])
            return {"messages": msgs, "error": None, "failover_triggered": False}

        def invoke_provider(
            provider: str,
            messages: Sequence[BaseMessage],
            target_model: Optional[str],
            user_id: Optional[str],
        ) -> Optional[Dict[str, Any]]:
            for cand_model in LangChainModelFactory.get_candidate_models(
                provider, target_model=target_model, user_id=user_id
            ):
                model = LangChainModelFactory.create_model(provider, cand_model, user_id=user_id)
                if not model:
                    continue
                try:
                    resp = model.invoke(messages)
                    return {
                        "response_text": extract_text_content(resp.content),
                        "final_model": getattr(model, "model_name", cand_model),
                        "active_provider": provider,
                        "error": None,
                    }
                except Exception as exc:
                    err_str = str(exc)
                    logger.warning("Model %s (%s) failed: %s", cand_model, provider, redact_secrets_from_text(err_str))
                    if ScopedModelQuotaTracker.is_rate_limit_error(err_str):
                        delay = ScopedModelQuotaTracker.parse_retry_delay(err_str)
                        ScopedModelQuotaTracker.record_quota_exhausted(cand_model, delay, user_id=user_id)
            return None

        def primary_node(state: AgentChatState) -> Dict[str, Any]:
            cfg = EnvKeyLoader.get_config()
            primary_prov = cfg["default_provider"] if cfg["default_provider"] in ("gemini", "openai") else "gemini"
            result = invoke_provider(
                primary_prov,
                state["messages"],
                state.get("target_model"),
                state.get("user_id"),
            )
            if result:
                return result
            return {
                "error": f"All models for provider {primary_prov} failed.",
                "failover_triggered": True,
            }

        def fallback_node(state: AgentChatState) -> Dict[str, Any]:
            fallback_prov = "openai" if state.get("active_provider") == "gemini" else "gemini"
            result = invoke_provider(fallback_prov, state["messages"], None, state.get("user_id"))
            if result:
                return result
            return {"error": f"Fallback provider {fallback_prov} also failed.", "active_provider": "failed"}

        builder.add_node("context_prep", context_node)
        builder.add_node("primary_model", primary_node)
        builder.add_node("fallback_model", fallback_node)

        builder.set_entry_point("context_prep")
        builder.add_edge("context_prep", "primary_model")
        builder.add_conditional_edges(
            "primary_model",
            lambda state: "fallback_model" if state.get("failover_triggered") else END,
        )
        builder.add_edge("fallback_model", END)
        return builder.compile()

    @staticmethod
    async def _stream_words(text: str, delay: float = 0.015) -> AsyncGenerator[Dict[str, Any], None]:
        words = text.split(" ")
        for idx, word in enumerate(words):
            chunk_word = word + (" " if idx < len(words) - 1 else "")
            yield {"token": chunk_word, "status": "streaming"}
            if delay > 0:
                await asyncio.sleep(delay)

    @staticmethod
    def _build_attachment_summary(attachments: Optional[List[Dict[str, Any]]]) -> str:
        if not attachments:
            return ""
        lines = []
        for att in attachments:
            fname = att.get("filename") or att.get("original_name") or "tệp"
            ext_text = (att.get("extracted_text") or "").strip()
            snippet = f": {ext_text[:200]}" if ext_text else ""
            lines.append(f"- `{fname}`{snippet}")
        return "\n\n**Tệp đính kèm đã tiếp nhận:**\n" + "\n".join(lines)

    async def _stream_offline_cache(
        self,
        prompt: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
        *,
        failover: bool = False,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        from src.services.semantic_cache_service import SemanticCacheService

        match = SemanticCacheService.lookup(prompt, threshold=0.48)
        if match:
            full_text = match["response_text"]
            is_cached = True
        else:
            full_text = SemanticCacheService.synthesize_offline_response(prompt)
            is_cached = False

        if attachments:
            full_text = full_text + self._build_attachment_summary(attachments)

        async for chunk_ev in self._stream_words(full_text, delay=0.01):
            yield chunk_ev

        done_ev: Dict[str, Any] = {
            "status": "done",
            "model": "offline-semantic-cache",
            "provider": "ollama",
            "cached": is_cached,
        }
        if failover:
            done_ev["failover"] = True
        yield done_ev

    async def astream_agent(
        self,
        prompt: str,
        history: List[Dict[str, Any]],
        model_override: Optional[str] = None,
        system_instruction: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Asynchronously streams token chunks with automatic multi-provider failover."""
        cfg = EnvKeyLoader.get_config()
        messages = build_langchain_messages(
            prompt,
            history,
            system_instruction=system_instruction,
            attachments=attachments,
        )

        target_model = model_override or cfg["default_model"] or "gemini-3.8-flash"
        target_lower = str(target_model).lower().strip()
        initial_prov = LangChainModelFactory.detect_provider_for_model(target_model)

        # 0.0 Deterministic Simulator Route (used by integration tests / offline attachment verification)
        if target_lower == "agent-simulator":
            sim_text = f"Đã tiếp nhận yêu cầu: \"{prompt}\".{self._build_attachment_summary(attachments)}"
            async for chunk_ev in self._stream_words(sim_text, delay=0.0):
                yield chunk_ev
            yield {"status": "done", "model": "agent-simulator", "provider": "offline", "simulated": True}
            return

        # 0.1 Direct In-Project Embedded Model Route (FR-061)
        if target_lower == "qwen2.5-0.5b-embedded" or "embedded" in target_lower:
            logger.info("Yêu cầu mô hình trực tiếp nhúng trong dự án: %s", target_model)
            from src.services.embedded_model_service import EmbeddedModelService

            try:
                chunks = await asyncio.to_thread(
                    lambda: list(
                        EmbeddedModelService.generate_stream(
                            prompt=prompt,
                            history=history,
                            model_id=target_model,
                        )
                    )
                )
                for chunk in chunks:
                    yield {"token": chunk, "status": "streaming"}
                    await asyncio.sleep(0.005)
                yield {"status": "done", "model": target_model, "provider": "ollama", "embedded": True}
                return
            except Exception as exc:
                logger.warning("Lỗi mô hình nhúng: %s", exc)
                yield {"status": "error", "message": str(exc)}
                return

        # 0.2 Direct Offline Semantic Cache Route
        if target_lower == "offline-semantic-cache" or initial_prov == "offline":
            logger.info("Yêu cầu chế độ Offline Semantic Cache trực tiếp.")
            async for ev in self._stream_offline_cache(prompt, attachments=attachments, failover=False):
                yield ev
            return

        formatted_tools = [
            {
                "type": "function",
                "function": {
                    "name": t["id"],
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
                },
            }
            for t in (tools or [])
        ]

        # 1. Ordered Provider Failover Chain
        provider_chain = [initial_prov]
        for prov in ("groq", "gemini", "openai", "anthropic", "ollama"):
            if prov not in provider_chain:
                provider_chain.append(prov)

        stream_started = False
        last_failed_model: Optional[str] = None
        has_switched_model = False

        for prov in provider_chain:
            candidates = LangChainModelFactory.get_candidate_models(
                prov,
                target_model=target_model if prov == initial_prov else None,
                user_id=user_id,
            )
            for cand_model in candidates:
                if last_failed_model and cand_model != last_failed_model and not stream_started:
                    yield {
                        "status": "failover",
                        "from_model": last_failed_model,
                        "to_model": cand_model,
                        "reason": (
                            f"Mô hình '{last_failed_model}' không khả dụng hoặc đã hết hạn ngạch truy cập (HTTP 429). "
                            f"Hệ thống tự động chuyển tiếp sang '{cand_model}' mà không mất ngữ cảnh."
                        ),
                        "message": f"Chuyển tiếp mô hình: {cand_model}",
                    }
                    has_switched_model = True

                model = LangChainModelFactory.create_model(prov, cand_model, user_id=user_id)
                if not model:
                    last_failed_model = cand_model
                    continue

                if formatted_tools and hasattr(model, "bind_tools"):
                    try:
                        model = model.bind_tools(formatted_tools)
                    except Exception as b_err:
                        logger.warning("Could not bind tools to %s: %s", cand_model, b_err)

                try:
                    final_model_name = getattr(model, "model_name", cand_model)
                    async for chunk in model.astream(messages):
                        raw_content = chunk.content if hasattr(chunk, "content") else str(chunk)
                        token_str = extract_text_content(raw_content)
                        if token_str:
                            stream_started = True
                            yield {"token": token_str, "status": "streaming"}

                    if stream_started:
                        yield {
                            "status": "done",
                            "model": final_model_name,
                            "provider": prov,
                            "failover": has_switched_model,
                        }
                        return
                except Exception as exc:
                    err_str = str(exc)
                    safe_err = redact_secrets_from_text(err_str)
                    logger.warning("Mô hình '%s' (%s) thất bại: %s", cand_model, prov, safe_err)
                    if ScopedModelQuotaTracker.is_rate_limit_error(err_str):
                        delay = ScopedModelQuotaTracker.parse_retry_delay(err_str)
                        ScopedModelQuotaTracker.record_quota_exhausted(cand_model, delay, user_id=user_id)
                    if stream_started:
                        yield {"status": "error", "message": f"Stream gián đoạn: {safe_err}"}
                        return
                    last_failed_model = cand_model
                    continue

        # 2. Extreme Fallback: Offline Semantic Cache
        logger.info("Tất cả nhà cung cấp không khả dụng -> Kích hoạt Offline Semantic Cache.")
        yield {
            "status": "failover",
            "from_model": last_failed_model or target_model,
            "to_model": "offline-semantic-cache",
            "reason": (
                "Các mô hình trực tuyến chưa được cấu hình khóa hoặc đã hết hạn ngạch. "
                "Hệ thống chuyển sang Bộ Nhớ Đệm Ngữ Nghĩa Ngoại Tuyến (Offline Semantic Cache)."
            ),
            "message": "Chuyển tiếp sang Offline Semantic Cache",
        }
        async for ev in self._stream_offline_cache(prompt, attachments=attachments, failover=True):
            yield ev


chat_agent = ChatAgentOrchestrator()
