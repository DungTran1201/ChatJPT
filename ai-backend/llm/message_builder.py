"""LangChain Message Builder — sliding context window (INV-04) & multimodal attachments."""

import base64
import logging
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

logger = logging.getLogger("ai_chan.agent")

DEFAULT_SYSTEM_INSTRUCTION = (
    "Bạn là AI-Chan, trợ lý ảo thông minh và thân thiện. "
    "Hãy trả lời chính xác, hữu ích, hỗ trợ định dạng Markdown và mã nguồn chuẩn khi cần."
)


def extract_text_content(content: Any) -> str:
    """Safely normalizes response content from string, list of blocks, or AIMessage."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
        return "".join(parts)
    return str(content) if content is not None else ""


def build_langchain_messages(
    prompt: str,
    history: List[Dict[str, Any]],
    system_instruction: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
) -> List[BaseMessage]:
    """Constructs a sliding window of max 20 messages (INV-04) with optional multimodal attachments."""
    instruction = (
        system_instruction.strip()
        if system_instruction and system_instruction.strip()
        else DEFAULT_SYSTEM_INSTRUCTION
    )
    messages: List[BaseMessage] = [SystemMessage(content=instruction)]

    recent_history = history[-20:] if len(history) > 20 else history
    for item in recent_history:
        role = item.get("role", "")
        content = item.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    image_parts: List[Dict[str, Any]] = []
    text_attachment_blocks: List[str] = []

    if attachments:
        from src.core.attachment_storage import extract_text_from_file, read_attachment_bytes

        for att in attachments:
            m_type = (att.get("mime_type") or "").lower()
            fname = att.get("filename") or att.get("original_name") or "tệp"
            category = att.get("category") or "document"
            storage_path = att.get("storage_path") or att.get("stored_path")

            # 1. Image modalities
            if m_type.startswith("image/") and storage_path:
                try:
                    raw_bytes = read_attachment_bytes(storage_path)
                    b64_str = base64.b64encode(raw_bytes).decode("utf-8")
                    image_parts.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{m_type};base64,{b64_str}"},
                        }
                    )
                except Exception as err:
                    logger.warning("Không thể nạp dữ liệu ảnh %s (%s): %s", fname, storage_path, err)

            # 2. Text / Code / CSV / JSON / PDF text extraction (fixed 4-arg call with raw bytes)
            ext_text = att.get("extracted_text")
            if not ext_text and storage_path and not m_type.startswith("image/"):
                try:
                    raw_bytes = read_attachment_bytes(storage_path)
                    ext_text = extract_text_from_file(raw_bytes, category, m_type, fname)
                except Exception as err:
                    logger.warning("Không thể trích xuất văn bản từ %s: %s", fname, err)

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
