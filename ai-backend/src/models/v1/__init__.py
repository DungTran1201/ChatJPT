"""Canonical v1 domain entities & persistence models."""

from src.models.v1.base import DomainModel
from src.models.v1.user import (
    EMAIL_REGEX,
    USERNAME_REGEX,
    HEX_COLOR_REGEX,
    ACCENT_COLOR_PRESETS,
    UserStatus,
    ThemePreference,
    LanguagePreference,
    UiFontSize,
    BilingualMode,
    UserPreferencesModel,
    UserStatsModel,
    UserModel,
)
from src.models.v1.conversation import (
    DEFAULT_CONVERSATION_TITLE,
    MessageRole,
    MessageStatus,
    ConversationModel,
    MessageModel,
)
from src.models.v1.ai_model import (
    VALID_LLM_PROVIDERS,
    ModelStatus,
    AIModelEntity,
)
from src.models.v1.attachment import (
    ALLOWED_ATTACHMENT_CATEGORIES,
    SUPPORTED_ATTACHMENT_MIME_TYPES,
    AttachmentStatus,
    AttachmentEntity,
)
from src.models.v1.prompt import SystemPromptEntity
from src.models.v1.rule import (
    VALID_ACTIVATION_MODES,
    VALID_RULE_STATUSES,
    RuleScope,
    RuleActivationMode,
    RuleStatus,
    RuleEntity,
)
from src.models.v1.api_key import (
    KeySource,
    KeyValidationStatus,
    ProviderCategory,
    UserApiKeyEntity,
)
from src.models.v1.embedded_model import (
    DEFAULT_EMBEDDED_MODEL_ID,
    EmbeddedDownloadStatus,
    EmbeddedModelEntity,
    SemanticCacheEntry,
)
from src.models.v1.voice import (
    DEFAULT_VOICE_SPEAKER_ID,
    DEFAULT_VOICE_SAMPLE_TEXT,
    VoiceGender,
    VoiceStatus,
    VoiceEntity,
)
from src.models.v1.exam import (
    VALID_EXAM_LEVELS,
    VALID_MATERIAL_CATEGORIES,
    ExamStatus,
    ExamQuestionEntity,
    ExamEntity,
    ReferenceMaterialEntity,
)
from src.models.v1.resource import (
    UserQuotaEntity,
    ApiMetricLogEntity,
)

__all__ = [
    "DomainModel",
    "EMAIL_REGEX",
    "USERNAME_REGEX",
    "HEX_COLOR_REGEX",
    "ACCENT_COLOR_PRESETS",
    "UserStatus",
    "ThemePreference",
    "LanguagePreference",
    "UiFontSize",
    "BilingualMode",
    "UserPreferencesModel",
    "UserStatsModel",
    "UserModel",
    "DEFAULT_CONVERSATION_TITLE",
    "MessageRole",
    "MessageStatus",
    "ConversationModel",
    "MessageModel",
    "VALID_LLM_PROVIDERS",
    "ModelStatus",
    "AIModelEntity",
    "ALLOWED_ATTACHMENT_CATEGORIES",
    "SUPPORTED_ATTACHMENT_MIME_TYPES",
    "AttachmentStatus",
    "AttachmentEntity",
    "SystemPromptEntity",
    "VALID_ACTIVATION_MODES",
    "VALID_RULE_STATUSES",
    "RuleScope",
    "RuleActivationMode",
    "RuleStatus",
    "RuleEntity",
    "KeySource",
    "KeyValidationStatus",
    "ProviderCategory",
    "UserApiKeyEntity",
    "DEFAULT_EMBEDDED_MODEL_ID",
    "EmbeddedDownloadStatus",
    "EmbeddedModelEntity",
    "SemanticCacheEntry",
    "DEFAULT_VOICE_SPEAKER_ID",
    "DEFAULT_VOICE_SAMPLE_TEXT",
    "VoiceGender",
    "VoiceStatus",
    "VoiceEntity",
    "VALID_EXAM_LEVELS",
    "VALID_MATERIAL_CATEGORIES",
    "ExamStatus",
    "ExamQuestionEntity",
    "ExamEntity",
    "ReferenceMaterialEntity",
    "UserQuotaEntity",
    "ApiMetricLogEntity",
]
