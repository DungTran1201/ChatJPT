"""Composition Root — FastAPI Dependency Injection wiring for all repositories and services."""

from functools import lru_cache

from src.core.database import DatabaseManager, db_manager
from src.core.secret_vault import default_vault
from src.core.storage import default_storage
from src.repositories.api_key_repo import ApiKeyRepository
from src.repositories.attachment_repo import AttachmentRepository
from src.repositories.conversation_repo import ConversationRepository
from src.repositories.embedded_repo import EmbeddedRepository
from src.repositories.exam_repo import ExamRepository
from src.repositories.model_repo import ModelRepository
from src.repositories.prompt_repo import PromptRepository
from src.repositories.rule_repo import RuleRepository
from src.repositories.telemetry_repo import TelemetryRepository
from src.repositories.user_repo import UserRepository
from src.repositories.voice_repo import VoiceRepository
from src.services.attachment_service import AttachmentService
from src.services.auth_service import AuthService
from src.services.chat_service import ChatService
from src.services.conversation_service import ConversationService
from src.services.credential_service import CredentialService
from src.services.embedded_model_service import EmbeddedModelService
from src.services.env_file_store import EnvFileStore
from src.services.exam_service import ExamService
from src.services.model_service import ModelService
from src.services.prompt_builder import PedagogicalPromptBuilder
from src.services.prompt_service import PromptService
from src.services.provider_registry import provider_registry
from src.services.rule_service import RuleService
from src.services.semantic_cache_service import SemanticCacheService
from src.services.stt_service import STTService
from src.services.text_import_service import TextImportService
from src.services.user_service import UserService
from src.services.voicevox_service import VoicevoxService, voicevox_service


def get_db_manager() -> DatabaseManager:
    return db_manager


# ----------------------------------------------------------------------
# Repositories
# ----------------------------------------------------------------------
@lru_cache(maxsize=1)
def get_user_repo() -> UserRepository:
    return UserRepository(db_manager)


@lru_cache(maxsize=1)
def get_conversation_repo() -> ConversationRepository:
    return ConversationRepository(db_manager)


@lru_cache(maxsize=1)
def get_api_key_repo() -> ApiKeyRepository:
    return ApiKeyRepository(db_manager)


@lru_cache(maxsize=1)
def get_model_repo() -> ModelRepository:
    return ModelRepository(db_manager)


@lru_cache(maxsize=1)
def get_attachment_repo() -> AttachmentRepository:
    return AttachmentRepository(db_manager)


@lru_cache(maxsize=1)
def get_prompt_repo() -> PromptRepository:
    return PromptRepository(db_manager)


@lru_cache(maxsize=1)
def get_rule_repo() -> RuleRepository:
    return RuleRepository(db_manager)


@lru_cache(maxsize=1)
def get_embedded_repo() -> EmbeddedRepository:
    return EmbeddedRepository(db_manager)


@lru_cache(maxsize=1)
def get_voice_repo() -> VoiceRepository:
    return VoiceRepository(db_manager)


@lru_cache(maxsize=1)
def get_exam_repo() -> ExamRepository:
    return ExamRepository(db_manager)


@lru_cache(maxsize=1)
def get_telemetry_repo() -> TelemetryRepository:
    return TelemetryRepository(db_manager)


# ----------------------------------------------------------------------
# Services
# ----------------------------------------------------------------------
def get_auth_service() -> AuthService:
    return AuthService(get_user_repo())


def get_user_service() -> UserService:
    return UserService(get_user_repo())


def get_conversation_service() -> ConversationService:
    return ConversationService(get_conversation_repo())


def get_credential_service() -> CredentialService:
    return CredentialService(
        repo=get_api_key_repo(),
        vault=default_vault,
        env_store=EnvFileStore(),
        registry=provider_registry,
    )


def get_model_service() -> ModelService:
    return ModelService(
        repo=get_model_repo(),
        credential_service=get_credential_service(),
        registry=provider_registry,
    )


def get_attachment_service() -> AttachmentService:
    return AttachmentService(
        att_repo=get_attachment_repo(),
        conv_repo=get_conversation_repo(),
        prompt_repo=get_prompt_repo(),
        storage=default_storage,
    )


def get_prompt_service() -> PromptService:
    return PromptService(
        prompt_repo=get_prompt_repo(),
        att_repo=get_attachment_repo(),
        storage=default_storage,
    )


def get_rule_service() -> RuleService:
    return RuleService(get_rule_repo())


def get_text_import_service() -> TextImportService:
    return TextImportService(
        rule_service=get_rule_service(),
        prompt_service=get_prompt_service(),
    )


def get_stt_service() -> STTService:
    return STTService(credential_service=get_credential_service())


def get_chat_service() -> ChatService:
    return ChatService(
        conv_repo=get_conversation_repo(),
        att_repo=get_attachment_repo(),
        model_repo=get_model_repo(),
        prompt_repo=get_prompt_repo(),
        rule_repo=get_rule_repo(),
        prompt_builder=PedagogicalPromptBuilder(),
        stt_service=get_stt_service(),
        storage=default_storage,
    )


def get_semantic_cache_service() -> SemanticCacheService:
    return SemanticCacheService(repo=get_embedded_repo())


def get_embedded_model_service() -> EmbeddedModelService:
    return EmbeddedModelService(
        repo=get_embedded_repo(),
        cache_service=get_semantic_cache_service(),
    )


def get_voice_service() -> VoicevoxService:
    # Share the singleton instance so ONNX synthesizer & LRU cache stay warm across requests
    return voicevox_service


@lru_cache(maxsize=1)
def get_exam_service() -> ExamService:
    return ExamService(repo=get_exam_repo())
