"""Conversation CRUD API schemas."""

from typing import Optional
from pydantic import BaseModel, Field
from src.models.v1.conversation import DEFAULT_CONVERSATION_TITLE


class CreateConversationRequest(BaseModel):
    title: Optional[str] = DEFAULT_CONVERSATION_TITLE


class UpdateConversationRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
