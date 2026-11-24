"""API v1 Router Registry — mounts all sub-routers in collision-free order."""

from fastapi import APIRouter

from src.api.v1.api_keys import api_keys_router
from src.api.v1.attachments import attachments_router
from src.api.v1.auth import auth_router
from src.api.v1.chat import chat_router
from src.api.v1.conversations import conv_router
from src.api.v1.embedded_model import embedded_router
from src.api.v1.exams import exams_router
from src.api.v1.models import models_router
from src.api.v1.prompts import prompts_router
from src.api.v1.resources import resources_router
from src.api.v1.rules import rules_router
from src.api.v1.users import users_router
from src.api.v1.voices import voices_router
from src.core.database import db_manager
from src.schemas.v1.health import HealthResponse

api_router = APIRouter()


@api_router.get("/health", response_model=HealthResponse)
async def health_check():
    db_ok = db_manager.check_connection()
    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        service="ai-backend",
        version="1.0.0",
        details={
            "service": "ai-backend",
            "database": "sqlite_connected" if db_ok else "sqlite_disconnected",
        },
    )


# Mount sub-routers for ChatJPT Core.
# IMPORTANT: embedded_router MUST be mounted BEFORE models_router so literal paths
# like DELETE /models/embedded are never shadowed by DELETE /models/{model_id}.
api_router.include_router(auth_router)
api_router.include_router(conv_router)
api_router.include_router(chat_router)
api_router.include_router(users_router)
api_router.include_router(embedded_router)
api_router.include_router(models_router)
api_router.include_router(resources_router)
api_router.include_router(prompts_router)
api_router.include_router(rules_router)
api_router.include_router(attachments_router)
api_router.include_router(api_keys_router)
api_router.include_router(voices_router)
api_router.include_router(exams_router)
