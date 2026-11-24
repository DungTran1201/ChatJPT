"""Conversation & Message domain models (conversations, messages tables)."""

from enum import Enum
from typing import Any, Dict, List, Optional
from src.models.v1.base import DomainModel

DEFAULT_CONVERSATION_TITLE = "Cuộc trò chuyện mới"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageStatus(str, Enum):
    PENDING = "PENDING"
    STREAMING = "STREAMING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"
    ABORTED = "ABORTED"
    FAILED = "FAILED"


class ConversationModel(DomainModel):
    """Domain entity mirroring the conversations table."""

    id: str
    user_id: str
    title: str = DEFAULT_CONVERSATION_TITLE
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MessageModel(DomainModel):
    """Domain entity mirroring the messages table."""

    id: str
    conversation_id: str
    role: str
    content: str
    model_used: Optional[str] = None
    tokens_prompt: Optional[int] = 0
    tokens_completion: Optional[int] = 0
    source: Optional[str] = "WEB"
    status: str = MessageStatus.COMPLETED.value
    sensei_id: Optional[str] = None
    voice_id: Optional[str] = None
    audio_attachment_id: Optional[str] = None
    audio_duration_ms: Optional[int] = 0
    stt_language: Optional[str] = None
    stt_confidence: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @staticmethod
    def enrich_messages_with_attachments(
        messages: List[Dict[str, Any]],
        raw_attachments: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Attach hydrated attachment lists and audio URLs to raw message dicts."""
        att_by_msg: Dict[str, List[Dict[str, Any]]] = {}
        for att in raw_attachments:
            mid = att.get("message_id")
            if mid:
                att_by_msg.setdefault(mid, []).append(att)

        for msg in messages:
            msg["attachments"] = att_by_msg.get(msg["id"], [])
            if msg.get("audio_attachment_id"):
                msg["audio_url"] = f"/api/v1/attachments/{msg['audio_attachment_id']}/view"
                msg["stt_transcript"] = msg.get("content", "")
        return messages
