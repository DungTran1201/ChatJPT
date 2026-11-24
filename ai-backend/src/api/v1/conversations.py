"""Thin HTTP router for Conversations endpoints (/api/v1/conversations)."""

from fastapi import APIRouter, Depends, status

from src.core.security import get_current_user
from src.dependencies import get_conversation_service
from src.schemas.v1.conversations import (
    CreateConversationRequest,
    UpdateConversationRequest,
)
from src.services.conversation_service import ConversationService

conv_router = APIRouter(prefix="/conversations", tags=["Conversations"])


@conv_router.get("/")
@conv_router.get("", include_in_schema=False)
async def list_conversations(
    current_user: dict = Depends(get_current_user),
    conv_service: ConversationService = Depends(get_conversation_service),
):
    return conv_service.list_conversations(current_user["id"])


@conv_router.post("/", status_code=status.HTTP_201_CREATED)
@conv_router.post("", status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_conversation(
    req: CreateConversationRequest,
    current_user: dict = Depends(get_current_user),
    conv_service: ConversationService = Depends(get_conversation_service),
):
    return conv_service.create_conversation(current_user["id"], req)


@conv_router.get("/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    conv_service: ConversationService = Depends(get_conversation_service),
):
    return conv_service.get_messages(
        conversation_id,
        current_user["id"],
        limit=limit,
        offset=offset,
    )


@conv_router.patch("/{conversation_id}")
async def rename_conversation(
    conversation_id: str,
    req: UpdateConversationRequest,
    current_user: dict = Depends(get_current_user),
    conv_service: ConversationService = Depends(get_conversation_service),
):
    return conv_service.rename_conversation(conversation_id, current_user["id"], req)


@conv_router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    conv_service: ConversationService = Depends(get_conversation_service),
):
    conv_service.delete_conversation(conversation_id, current_user["id"])
    return None
