from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from src.api.v1.auth import auth_router
from src.api.v1.conversations import conv_router
from src.api.v1.chat import chat_router
from src.api.v1.users import users_router
from src.api.v1.models import models_router
from src.api.v1.resources import resources_router
from src.api.v1.prompts import prompts_router
from src.api.v1.rules import rules_router
from src.api.v1.attachments import attachments_router
from src.api.v1.api_keys import api_keys_router
from src.api.v1.embedded_model import embedded_router

class HealthResponse(BaseModel):
    model_config = {"extra": "allow"}
    status: str = Field(default="healthy")
    service: Optional[str] = Field(default="ai-backend")
    version: Optional[str] = Field(default="1.0.0")
    details: Optional[Dict[str, Any]] = None

api_router = APIRouter()

# Healthcheck endpoint
@api_router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        service="ai-backend",
        version="1.0.0",
        details={
            "service": "ai-backend",
            "database": "sqlite_connected"
        }
    )

# Mount sub-routers for ChatJPT Core
api_router.include_router(auth_router)
api_router.include_router(conv_router)
api_router.include_router(chat_router)
api_router.include_router(users_router)
api_router.include_router(models_router)
api_router.include_router(resources_router)
api_router.include_router(prompts_router)
api_router.include_router(rules_router)
api_router.include_router(attachments_router)
api_router.include_router(api_keys_router)
api_router.include_router(embedded_router)
