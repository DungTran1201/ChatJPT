"""Canonical v1 API request & response schemas."""

from src.schemas.v1.health import HealthResponse
from src.schemas.v1.auth import RegisterRequest, LoginRequest, UserProfileResponse
from src.schemas.v1.users import (
    UpdateProfileRequest,
    UpdateAvatarRequest,
    ChangeEmailRequest,
    ChangePasswordRequest,
    UpdatePreferencesRequest,
)
from src.schemas.v1.conversations import (
    CreateConversationRequest,
    UpdateConversationRequest,
)
from src.schemas.v1.chat import MessageStreamRequest, STTResult
from src.schemas.v1.models import (
    SetDefaultModelRequest,
    CreateModelRequest,
    UpdateModelRequest,
    ModelResponse,
    ModelSearchResponse,
)
from src.schemas.v1.resources import QuotaStatusData, ResourceHistoryData
from src.schemas.v1.prompts import (
    SystemPromptBaseRequest,
    SystemPromptCreateRequest,
    SystemPromptUpdateRequest,
    SystemPromptSummaryResponse,
    SystemPromptListResponse,
    SystemPromptDetailResponse,
)
from src.schemas.v1.rules import (
    RuleBaseRequest,
    RuleCreateRequest,
    RuleUpdateRequest,
    RuleStatusUpdateRequest,
    RuleResponse,
    PaginatedRuleResponse,
    ProjectRuleBindingRequest,
)
from src.schemas.v1.text_import import TextFileImportRequest
from src.schemas.v1.attachments import (
    AttachmentResponse,
    AttachmentListResponse,
    ModelCapability,
    CapabilityResponse,
)
from src.schemas.v1.api_keys import (
    ProviderKeyStatusResponse,
    SetApiKeyRequest,
    TestApiKeyRequest,
    TestApiKeyResponse,
    UpdateSystemEnvRequest,
)
from src.schemas.v1.embedded_model import DownloadRequest, LearnRequest
from src.schemas.v1.voices import (
    VoiceSummaryResponse,
    VoiceListResponse,
    VoiceEngineStatusResponse,
    VoiceCreateRequest,
    VoiceUpdateRequest,
    SynthesisRequest,
)
from src.schemas.v1.exams import (
    ExamQuestionSummary,
    ExamSummaryResponse,
    ExamDetailResponse,
    ExamListResponse,
    ExamCreateRequest,
    ExamUpdateRequest,
    ExamSubmissionRequest,
    QuestionResultItem,
    ExamSubmissionResult,
    ReferenceMaterialItem,
    ReferenceMaterialListResponse,
    ReferenceMaterialCreateRequest,
)

__all__ = [
    "HealthResponse",
    "RegisterRequest",
    "LoginRequest",
    "UserProfileResponse",
    "UpdateProfileRequest",
    "UpdateAvatarRequest",
    "ChangeEmailRequest",
    "ChangePasswordRequest",
    "UpdatePreferencesRequest",
    "CreateConversationRequest",
    "UpdateConversationRequest",
    "MessageStreamRequest",
    "STTResult",
    "SetDefaultModelRequest",
    "CreateModelRequest",
    "UpdateModelRequest",
    "ModelResponse",
    "ModelSearchResponse",
    "QuotaStatusData",
    "ResourceHistoryData",
    "SystemPromptBaseRequest",
    "SystemPromptCreateRequest",
    "SystemPromptUpdateRequest",
    "SystemPromptSummaryResponse",
    "SystemPromptListResponse",
    "SystemPromptDetailResponse",
    "RuleBaseRequest",
    "RuleCreateRequest",
    "RuleUpdateRequest",
    "RuleStatusUpdateRequest",
    "RuleResponse",
    "PaginatedRuleResponse",
    "ProjectRuleBindingRequest",
    "TextFileImportRequest",
    "AttachmentResponse",
    "AttachmentListResponse",
    "ModelCapability",
    "CapabilityResponse",
    "ProviderKeyStatusResponse",
    "SetApiKeyRequest",
    "TestApiKeyRequest",
    "TestApiKeyResponse",
    "UpdateSystemEnvRequest",
    "DownloadRequest",
    "LearnRequest",
    "VoiceSummaryResponse",
    "VoiceListResponse",
    "VoiceEngineStatusResponse",
    "VoiceCreateRequest",
    "VoiceUpdateRequest",
    "SynthesisRequest",
    "ExamQuestionSummary",
    "ExamSummaryResponse",
    "ExamDetailResponse",
    "ExamListResponse",
    "ExamCreateRequest",
    "ExamUpdateRequest",
    "ExamSubmissionRequest",
    "QuestionResultItem",
    "ExamSubmissionResult",
    "ReferenceMaterialItem",
    "ReferenceMaterialListResponse",
    "ReferenceMaterialCreateRequest",
]
