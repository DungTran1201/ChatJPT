import os
import re
import json
import time
import uuid
import asyncio
import logging
import base64
from typing import TypedDict, Sequence, Optional, List, Dict, Any, AsyncGenerator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END

logger = logging.getLogger("ai_chan.agent")

def extract_text_content(content: Any) -> str:
    """Safely normalizes response content from string, list of blocks, or AIMessage."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
        return "".join(parts)
    return str(content) if content is not None else ""

class EnvKeyLoader:
    """Dynamically loads and validates LLM provider keys and configurations from .env."""
    
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

        # Fallback to os.getenv if empty
        gemini_key = gemini_key or os.getenv("GEMINI_API_KEY", "").strip()
        openai_key = openai_key or os.getenv("OPENAI_API_KEY", "").strip()

        # Modern Gemini model alias upgrade
        if default_mod in ["gemini-1.5-flash", "gemini-2.5-flash"]:
            default_mod = "gemini-3.5-flash-lite"

        return {
            "gemini_api_key": gemini_key,
            "openai_api_key": openai_key,
            "anthropic_api_key": anthropic_key,
            "groq_api_key": groq_key,
            "ollama_base_url": ollama_url,
            "default_provider": default_prov,
            "default_model": default_mod
        }

    @classmethod
    def get_available_providers(cls) -> List[str]:
        cfg = cls.get_config()
        available = []
        if cfg["gemini_api_key"]:
            available.append("gemini")
        if cfg["openai_api_key"]:
            available.append("openai")
        if cfg["anthropic_api_key"]:
            available.append("anthropic")
        if cfg["groq_api_key"]:
            available.append("groq")
        return available

class AgentChatState(TypedDict):
    """LangGraph state representation for chat message workflow."""
    messages: Sequence[BaseMessage]
    prompt: str
    history: List[Dict[str, Any]]
    target_model: str
    active_provider: str
    response_text: str
    error: Optional[str]
    failover_triggered: bool
    final_model: str

class ModelQuotaTracker:
    """Tracks rate limits and 429 RESOURCE_EXHAUSTED cooldowns per model."""
    _cooldowns: Dict[str, float] = {}

    @classmethod
    def record_quota_exhausted(cls, model_name: str, retry_delay_seconds: float = 1800.0):
        if not model_name:
            return
        cls._cooldowns[model_name] = time.time() + retry_delay_seconds
        logger.warning(
            f"[CircuitBreaker] Model '{model_name}' marked as quota exhausted (429 RESOURCE_EXHAUSTED). "
            f"Cooldown active for {int(retry_delay_seconds)}s."
        )

    @classmethod
    def is_available(cls, model_name: str) -> bool:
        if not model_name:
            return True
        cooldown_until = cls._cooldowns.get(model_name, 0.0)
        if time.time() < cooldown_until:
            remaining = int(cooldown_until - time.time())
            logger.info(f"[CircuitBreaker] Skipping '{model_name}' (429 cooldown active: {remaining}s remaining).")
            return False
        return True

    @classmethod
    def parse_retry_delay(cls, error_str: str, default_seconds: float = 1800.0) -> float:
        m = re.search(r'retryDelay[\'"]?\s*:\s*[\'"]?(\d+)s?', error_str)
        if m:
            return float(m.group(1))
        h_m = re.search(r'retry in\s+(\d+)h(\d+)m', error_str)
        if h_m:
            hours = int(h_m.group(1))
            minutes = int(h_m.group(2))
            return float(hours * 3600 + minutes * 60)
        return default_seconds

class LangChainModelFactory:
    """Factory creating LangChain Chat Model instances based on .env configuration."""

    @staticmethod
    def detect_provider_for_model(model_name: Optional[str]) -> str:
        """Determines the provider ID based on model identifier prefix or name."""
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
    def get_candidate_models(provider: str, target_model: Optional[str] = None) -> List[str]:
        provider = provider.lower().strip()
        if provider in ("gemini", "google"):
            pool = [
                target_model,
                "gemini-3.8-flash",
                "gemini-3.5-flash-lite",
                "gemini-3.5-flash",
                "gemini-flash-lite-latest"
            ]
        elif provider == "groq":
            pool = [
                target_model,
                "llama-3.3-70b-versatile",
                "mixtral-8x7b-32768"
            ]
        elif provider == "openai":
            pool = [
                target_model,
                "gpt-4o-mini",
                "gpt-4o"
            ]
        elif provider == "anthropic":
            pool = [
                target_model,
                "claude-3-5-haiku",
                "claude-3-7-sonnet"
            ]
        elif provider == "ollama":
            pool = [
                target_model,
                "qwen2.5-0.5b-cpu",
                "qwen2.5-1.5b-cpu",
                "llama3"
            ]
        elif provider == "offline":
            return ["offline-semantic-cache"]
        else:
            pool = [target_model] if target_model else []

        candidates = []
        for m in pool:
            if m and m not in candidates and ModelQuotaTracker.is_available(m):
                candidates.append(m)

        if not candidates and target_model:
            candidates.append(target_model)
        return candidates

    @staticmethod
    def create_model(provider: str, model_name: Optional[str] = None, user_id: Optional[str] = None):
        cfg = EnvKeyLoader.get_config()
        provider = provider.lower().strip()
        if provider == "google":
            provider = "gemini"

        # Resolve effective key: User Personal Key > System .env Default
        effective_key = None
        try:
            from src.services.credential_service import CredentialService
            effective_key = CredentialService.get_effective_key(user_id, provider)
        except Exception:
            pass

        if provider == "gemini":
            key = effective_key or cfg["gemini_api_key"]
            if key:
                from langchain_google_genai import ChatGoogleGenerativeAI
                target = model_name or cfg["default_model"] or "gemini-3.8-flash"
                if target in ["gemini-1.5-flash", "gemini-2.5-flash"]:
                    target = "gemini-3.5-flash-lite"
                return ChatGoogleGenerativeAI(
                    model=target,
                    google_api_key=key,
                    temperature=0.7,
                    timeout=15.0,
                    max_retries=1
                )
        elif provider == "groq":
            key = effective_key or cfg["groq_api_key"]
            if key:
                try:
                    from langchain_groq import ChatGroq
                    target = model_name or "llama-3.3-70b-versatile"
                    return ChatGroq(
                        model=target,
                        api_key=key,
                        temperature=0.7,
                        timeout=20.0
                    )
                except Exception as e:
                    logger.warning(f"Failed to initialize ChatGroq: {e}")
        elif provider == "openai":
            key = effective_key or cfg["openai_api_key"]
            if key:
                from langchain_openai import ChatOpenAI
                target = model_name or "gpt-4o-mini"
                return ChatOpenAI(
                    model=target,
                    api_key=key,
                    temperature=0.7,
                    timeout=25.0
                )
        elif provider == "anthropic":
            key = effective_key or cfg["anthropic_api_key"]
            if key:
                try:
                    from langchain_anthropic import ChatAnthropic
                    target = model_name or "claude-3-5-haiku"
                    return ChatAnthropic(
                        model=target,
                        api_key=key,
                        temperature=0.7,
                        timeout=25.0
                    )
                except Exception as e:
                    logger.warning(f"Failed to initialize ChatAnthropic: {e}")
        elif provider == "ollama":
            ollama_url = cfg["ollama_base_url"] or "http://localhost:11434"
            target = model_name or "qwen2.5-0.5b-cpu"
            ollama_model_tag = "qwen2.5:0.5b" if "qwen2.5-0.5b" in target else ("qwen2.5:1.5b" if "qwen2.5-1.5b" in target else target)
            try:
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    base_url=f"{ollama_url.rstrip('/')}/v1",
                    api_key="ollama",
                    model=ollama_model_tag,
                    temperature=0.7,
                    timeout=6.0,
                    max_retries=0
                )
            except Exception as e:
                logger.warning(f"Could not connect to Ollama ({ollama_url}): {e}")
        return None

def build_langchain_messages(
    prompt: str,
    history: List[Dict[str, Any]],
    system_instruction: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None
) -> List[BaseMessage]:
    """Constructs a sliding window of max 20 messages (INV-04) formatted for LangChain with optional custom system instruction and multimodal attachments."""
    default_instruction = (
        "Bạn là AI-Chan, trợ lý ảo thông minh và thân thiện. "
        "Hãy trả lời chính xác, hữu ích, hỗ trợ định dạng Markdown và mã nguồn chuẩn khi cần."
    )
    instruction = system_instruction.strip() if system_instruction and system_instruction.strip() else default_instruction
    messages: List[BaseMessage] = [SystemMessage(content=instruction)]
    
    # 20 most recent messages context window
    recent_history = history[-20:] if len(history) > 20 else history
    for item in recent_history:
        role = item.get("role", "")
        content = item.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    # Process attachments for the current turn
    image_parts: List[Dict[str, Any]] = []
    text_attachment_blocks: List[str] = []

    if attachments:
        from src.core.attachment_storage import read_attachment_bytes, extract_text_from_file
        for att in attachments:
            m_type = (att.get("mime_type") or "").lower()
            fname = att.get("filename") or att.get("original_name") or "tệp"
            storage_path = att.get("storage_path")
            
            # 1. Image modalities (PNG, JPEG, WebP, GIF)
            if m_type.startswith("image/"):
                if storage_path:
                    try:
                        raw_bytes = read_attachment_bytes(storage_path)
                        b64_str = base64.b64encode(raw_bytes).decode("utf-8")
                        image_parts.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{m_type};base64,{b64_str}"
                            }
                        })
                    except Exception as err:
                        logger.warning(f"Không thể nạp dữ liệu ảnh {fname} ({storage_path}): {err}")

            # 2. Text / Code / CSV / JSON / PDF text extraction
            ext_text = att.get("extracted_text")
            if not ext_text and storage_path and not m_type.startswith("image/"):
                try:
                    ext_text = extract_text_from_file(storage_path, m_type)
                except Exception as err:
                    logger.warning(f"Không thể trích xuất văn bản từ {fname}: {err}")

            if ext_text and ext_text.strip():
                text_attachment_blocks.append(
                    f"\n\n--- [Tài liệu đính kèm: {fname} (MIME: {m_type})] ---\n"
                    f"{ext_text.strip()}\n"
                    f"--- [Hết tài liệu: {fname}] ---"
                )

    combined_text = prompt
    if text_attachment_blocks:
        combined_text = combined_text + "".join(text_attachment_blocks)

    if image_parts:
        content_parts: List[Dict[str, Any]] = [{"type": "text", "text": combined_text}]
        content_parts.extend(image_parts)
        messages.append(HumanMessage(content=content_parts))
    else:
        messages.append(HumanMessage(content=combined_text))

    return messages


def extract_math_expression(text: str) -> Optional[str]:
    """Extracts a mathematical expression from prompt if calculation is requested."""
    triggers = ["tính", "calculate", "phép tính", "kết quả của", "bằng bao nhiêu", "math", "giải"]
    has_trigger = any(trig in text.lower() for trig in triggers)
    cleaned = text
    for trig in triggers:
        cleaned = re.sub(re.escape(trig), " ", cleaned, flags=re.IGNORECASE)
    
    matches = re.findall(r'[\d\.\s\+\-\*\/\(\)\%]{3,}', cleaned)
    for cand in matches:
        cand_str = cand.strip(" .?,;:=!@#$^&_`~")
        if any(c.isdigit() for c in cand_str) and any(op in cand_str for op in ['+', '-', '*', '/', '%']):
            return cand_str
            
    if has_trigger:
        matches_all = re.findall(r'[\d\.\s\+\-\*\/\(\)\%]+', text)
        for cand in matches_all:
            cand_str = cand.strip(" .?,;:=!@#$^&_`~")
            if any(c.isdigit() for c in cand_str) and any(op in cand_str for op in ['+', '-', '*', '/', '%']):
                return cand_str
    return None


def is_datetime_query(text: str) -> bool:
    """Checks if prompt asks for current date/time info."""
    low = text.lower()
    return any(p in low for p in [
        "mấy giờ", "ngày mấy", "hôm nay là ngày", "thời gian hiện tại", 
        "ngày giờ hiện tại", "what time is it", "current date", "current time"
    ])


def is_convert_units_query(text: str) -> Optional[Dict[str, Any]]:
    """Checks if prompt asks for unit conversion."""
    low = text.lower()
    m = re.search(r'(?:đổi|chuyển đổi|convert)\s+([0-9\.]+)\s*([a-zA-Z_]+)\s*(?:sang|to|thành)\s*([a-zA-Z_]+)', low)
    if m:
        try:
            return {
                "value": float(m.group(1)),
                "from_unit": m.group(2).strip(),
                "to_unit": m.group(3).strip()
            }
        except Exception:
            return None
    return None


class ChatAgentOrchestrator:
    """Stateful Chat Agent orchestrator powered by LangChain and LangGraph."""

    def __init__(self):
        self.workflow = self._build_graph()

    def _build_graph(self):
        """Constructs the LangGraph StateGraph workflow with failover routing."""
        builder = StateGraph(AgentChatState)

        def context_node(state: AgentChatState) -> Dict[str, Any]:
            msgs = build_langchain_messages(state["prompt"], state["history"])
            return {"messages": msgs, "error": None, "failover_triggered": False}

        def primary_node(state: AgentChatState) -> Dict[str, Any]:
            cfg = EnvKeyLoader.get_config()
            primary_prov = cfg["default_provider"] if cfg["default_provider"] in ["gemini", "openai"] else "gemini"
            target_model = state.get("target_model")
            user_id = state.get("user_id")
            candidates = LangChainModelFactory.get_candidate_models(primary_prov, target_model)
            for cand_model in candidates:
                model = LangChainModelFactory.create_model(primary_prov, cand_model, user_id=user_id)
                if not model:
                    continue
                try:
                    resp = model.invoke(state["messages"])
                    clean_text = extract_text_content(resp.content)
                    return {
                        "response_text": clean_text,
                        "final_model": getattr(model, "model_name", cand_model),
                        "active_provider": primary_prov,
                        "error": None
                    }
                except Exception as exc:
                    err_str = str(exc)
                    logger.warning(f"Primary model {cand_model} failed in primary_node: {exc}. Trying next candidate...")
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "Too Many Requests" in err_str:
                        delay = ModelQuotaTracker.parse_retry_delay(err_str)
                        ModelQuotaTracker.record_quota_exhausted(cand_model, delay)
                    continue
            return {
                "error": f"All models for provider {primary_prov} failed.",
                "failover_triggered": True
            }

        def fallback_node(state: AgentChatState) -> Dict[str, Any]:
            # Failover logic: if gemini failed, try openai, or vice-versa (BR-005)
            fallback_prov = "openai" if state.get("active_provider") == "gemini" else "gemini"
            fallback_candidates = LangChainModelFactory.get_candidate_models(fallback_prov)
            user_id = state.get("user_id")
            for fb_cand in fallback_candidates:
                model = LangChainModelFactory.create_model(fallback_prov, fb_cand, user_id=user_id)
                if not model:
                    continue
                try:
                    resp = model.invoke(state["messages"])
                    clean_text = extract_text_content(resp.content)
                    return {
                        "response_text": clean_text,
                        "final_model": getattr(model, "model_name", fb_cand),
                        "active_provider": fallback_prov,
                        "error": None
                    }
                except Exception as exc:
                    err_str = str(exc)
                    logger.error(f"Fallback model {fb_cand} ({fallback_prov}) failed: {exc}")
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "Too Many Requests" in err_str:
                        delay = ModelQuotaTracker.parse_retry_delay(err_str)
                        ModelQuotaTracker.record_quota_exhausted(fb_cand, delay)
                    continue

            return {"error": f"Fallback provider {fallback_prov} also failed.", "active_provider": "failed"}

        builder.add_node("context_prep", context_node)
        builder.add_node("primary_model", primary_node)
        builder.add_node("fallback_model", fallback_node)

        builder.set_entry_point("context_prep")
        builder.add_edge("context_prep", "primary_model")

        def route_after_primary(state: AgentChatState) -> str:
            if state.get("failover_triggered"):
                return "fallback_model"
            return END

        builder.add_conditional_edges("primary_model", route_after_primary)
        builder.add_edge("fallback_model", END)

        return builder.compile()

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
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Asynchronously streams token chunks with automatic failover (SSE compatible), multi-model continuity, and offline semantic cache."""
        cfg = EnvKeyLoader.get_config()
        messages = build_langchain_messages(prompt, history, system_instruction=system_instruction, attachments=attachments)
        
        target_model = model_override or cfg["default_model"] or "gemini-3.8-flash"
        initial_prov = LangChainModelFactory.detect_provider_for_model(target_model)

        # 0.1 DIRECT IN-PROJECT EMBEDDED MODEL ROUTING (FR-061)
        if target_model == "qwen2.5-0.5b-embedded" or "embedded" in str(target_model).lower():
            logger.info("Yêu cầu mô hình trực tiếp nhúng trong dự án: %s", target_model)
            from src.services.embedded_model_service import EmbeddedModelService
            try:
                for chunk in EmbeddedModelService.generate_stream(prompt=prompt, history=history, model_id=target_model):
                    yield {"token": chunk, "status": "streaming"}
                    await asyncio.sleep(0.01)

                yield {
                    "status": "done",
                    "model": target_model,
                    "provider": "ollama",
                    "embedded": True
                }
                return
            except Exception as e:
                logger.warning("Lỗi mô hình nhúng: %s.", e)
                yield {"status": "error", "message": str(e)}
                return

        # 0. DIRECT OFFLINE SEMANTIC CACHE ROUTING
        if target_model == "offline-semantic-cache" or initial_prov == "offline":
            logger.info("Yêu cầu chế độ Offline Semantic Cache trực tiếp.")
            from src.services.semantic_cache_service import SemanticCacheService
            match = SemanticCacheService.lookup(prompt, threshold=0.48)
            if match:
                full_text = match["response_text"]
                is_cached = True
            else:
                full_text = SemanticCacheService.synthesize_offline_response(prompt)
                is_cached = False

            words = full_text.split(" ")
            for idx, word in enumerate(words):
                chunk_word = word + (" " if idx < len(words) - 1 else "")
                yield {"token": chunk_word, "status": "streaming"}
                await asyncio.sleep(0.015)

            yield {
                "status": "done",
                "model": "offline-semantic-cache",
                "provider": "ollama",
                "cached": is_cached
            }
            return

        # Format tools if provided
        formatted_tools = []
        if tools:
            for t in tools:
                formatted_tools.append({
                    "type": "function",
                    "function": {
                        "name": t["id"],
                        "description": t.get("description", ""),
                        "parameters": t.get("input_schema", {"type": "object", "properties": {}})
                    }
                })

        # 1. BUILD ORDERED PROVIDER CHAIN FOR AUTO-FAILOVER
        provider_chain = [initial_prov]
        for p in ["groq", "gemini", "openai", "anthropic", "ollama"]:
            if p not in provider_chain:
                provider_chain.append(p)

        stream_started = False
        last_failed_model = None
        has_switched_model = False

        for prov in provider_chain:
            candidates = LangChainModelFactory.get_candidate_models(prov, target_model=target_model if prov == initial_prov else None)
            for cand_model in candidates:
                # If we had a previous failure and are now switching models, notify the user via failover event
                if last_failed_model and cand_model != last_failed_model and not stream_started:
                    yield {
                        "status": "failover",
                        "from_model": last_failed_model,
                        "to_model": cand_model,
                        "reason": f"Mô hình '{last_failed_model}' không khả dụng hoặc đã hết hạn ngạch truy cập (HTTP 429). Hệ thống tự động chuyển tiếp sang '{cand_model}' mà không mất ngữ cảnh.",
                        "message": f"Chuyển tiếp mô hình: {cand_model}"
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
                        logger.warning(f"Could not bind tools to {cand_model}: {b_err}")

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
                            "failover": has_switched_model
                        }
                        return
                except Exception as exc:
                    err_str = str(exc)
                    logger.warning(f"Mô hình '{cand_model}' ({prov}) thất bại: {exc}")
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "Too Many Requests" in err_str or "rate_limit" in err_str.lower():
                        delay = ModelQuotaTracker.parse_retry_delay(err_str)
                        ModelQuotaTracker.record_quota_exhausted(cand_model, delay)
                    if stream_started:
                        yield {"status": "error", "message": f"Stream gián đoạn: {exc}"}
                        return
                    last_failed_model = cand_model
                    continue

        # 2. EXTREME FALLBACK: OFFLINE SEMANTIC CACHE
        logger.info("Tất cả nhà cung cấp đám mây/cục bộ không khả dụng -> Kích hoạt Bộ Nhớ Đệm Ngữ Nghĩa (Offline Semantic Cache).")
        yield {
            "status": "failover",
            "from_model": last_failed_model or target_model,
            "to_model": "offline-semantic-cache",
            "reason": "Các mô hình trực tuyến chưa được cấu hình khóa hoặc đã hết hạn ngạch. Hệ thống chuyển sang Bộ Nhớ Đệm Ngữ Nghĩa Ngoại Tuyến (Offline Semantic Cache).",
            "message": "Chuyển tiếp sang Offline Semantic Cache"
        }

        from src.services.semantic_cache_service import SemanticCacheService
        match = SemanticCacheService.lookup(prompt, threshold=0.48)
        if match:
            full_text = match["response_text"]
            is_cached = True
        else:
            full_text = SemanticCacheService.synthesize_offline_response(prompt)
            is_cached = False

        words = full_text.split(" ")
        for idx, word in enumerate(words):
            chunk_word = word + (" " if idx < len(words) - 1 else "")
            yield {"token": chunk_word, "status": "streaming"}
            await asyncio.sleep(0.015)

        yield {
            "status": "done",
            "model": "offline-semantic-cache",
            "provider": "ollama",
            "cached": is_cached,
            "failover": True
        }

# Global singleton instance
chat_agent = ChatAgentOrchestrator()
