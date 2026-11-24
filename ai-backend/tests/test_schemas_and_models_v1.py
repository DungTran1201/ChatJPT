"""Unit checks for extracted src.models.v1 and src.schemas.v1 layers."""

import sys
import unittest
from pathlib import Path
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models.v1 import (
    AIModelEntity,
    AttachmentEntity,
    ExamEntity,
    ExamQuestionEntity,
    MessageModel,
    ReferenceMaterialEntity,
    SystemPromptEntity,
    UserModel,
    UserPreferencesModel,
    UserQuotaEntity,
)
from src.schemas.v1 import (
    AttachmentResponse,
    CapabilityResponse,
    ExamCreateRequest,
    ExamDetailResponse,
    ExamSummaryResponse,
    HealthResponse,
    ProviderKeyStatusResponse,
    ReferenceMaterialCreateRequest,
    ReferenceMaterialItem,
    RuleCreateRequest,
    STTResult,
    SystemPromptCreateRequest,
    SystemPromptDetailResponse,
    TextFileImportRequest,
)


class TestSchemasAndModelsV1(unittest.TestCase):
    def test_backward_compat_shims_resolve_same_classes(self):
        from src.schemas.api import ProviderKeyStatusResponse as LegacyProviderKeyStatusResponse
        from src.schemas.attach import AttachmentResponse as LegacyAttachmentResponse
        from src.services.rule_service import RuleCreateRequest as ServiceRuleCreateRequest
        from src.services.text_import_service import TextFileImportRequest as ServiceTextImportRequest
        from src.services.stt_service import STTResult as ServiceSTTResult
        from src.api.v1.router import HealthResponse as RouterHealthResponse

        self.assertIs(LegacyProviderKeyStatusResponse, ProviderKeyStatusResponse)
        self.assertIs(LegacyAttachmentResponse, AttachmentResponse)
        self.assertIs(ServiceRuleCreateRequest, RuleCreateRequest)
        self.assertIs(ServiceTextImportRequest, TextFileImportRequest)
        self.assertIs(ServiceSTTResult, STTResult)
        self.assertIs(RouterHealthResponse, HealthResponse)

    def test_user_row_mapping_handles_nulls_and_booleans(self):
        row = {
            "id": "u1",
            "email": "test@example.com",
            "response_show_translation": None,
            "response_show_furigana": 0,
            "bg_opacity": None,
            "created_at": None,
        }
        prefs = UserPreferencesModel.from_user_row(row)
        self.assertTrue(prefs.response_show_translation)
        self.assertFalse(prefs.response_show_furigana)
        self.assertEqual(prefs.bg_opacity, 90)

        login_dict = UserModel.from_user_row(row).to_login_dict()
        self.assertIn("discord_id", login_dict)
        self.assertNotIn("password_changed_at", login_dict)
        self.assertFalse(login_dict["response_show_furigana"])

        profile_dict = UserModel.from_user_row(row, blank_missing_text=True).to_profile_dict()
        self.assertNotIn("discord_id", profile_dict)
        self.assertEqual(profile_dict["full_name"], "")

    def test_entity_row_mappers_handle_partial_and_null_rows(self):
        ai_model = AIModelEntity.from_model_row(
            {"id": "m1", "name": "Model 1", "provider": "google", "context_window": None, "max_tokens": None},
            has_api_key=True,
        )
        self.assertEqual(ai_model.context_window, 128000)
        self.assertEqual(ai_model.max_tokens, 4096)
        self.assertTrue(ai_model.supports_streaming)

        att = AttachmentEntity.from_attachment_row(
            {"id": "a1", "filename": "note.txt", "extracted_text": "x" * 250}
        )
        att_resp = AttachmentResponse.from_entity(att)
        self.assertEqual(att_resp.download_url, "/api/v1/attachments/a1/download")
        self.assertTrue(att_resp.extracted_text_preview.endswith("..."))

        sp = SystemPromptEntity.from_prompt_row(
            {"id": "sp1", "user_id": "u1", "name": "Sakura", "content": "Hi", "created_at": None, "updated_at": None}
        )
        sp_detail = SystemPromptDetailResponse.from_entity(sp)
        self.assertEqual(sp_detail.created_at, "")
        self.assertEqual(sp_detail.updated_at, "")

        exam = ExamEntity.from_exam_row(
            {"id": "e1", "title": "JLPT N5", "level": "N5", "total_questions": None, "is_system_preset": None}
        )
        self.assertEqual(exam.total_questions, 0)
        self.assertTrue(exam.is_system_preset)
        q = ExamQuestionEntity.from_question_row(
            {
                "id": "q1",
                "section": "Vocab",
                "question_number": 1,
                "question_text": "?",
                "option_1": "a",
                "option_2": "b",
                "option_3": "c",
                "option_4": "d",
                "correct_option": 2,
            },
            include_answers=False,
        )
        detail = ExamDetailResponse.from_entities(exam, [q])
        self.assertIsNone(detail.questions[0].correct_option)

        mat = ReferenceMaterialEntity.from_material_row(
            {"id": "m1", "title": "Guide", "category": "JLPT_N5", "description": None, "external_url": "/local.pdf"},
            compute_size_display=True,
        )
        mat_item = ReferenceMaterialItem.from_entity(mat)
        self.assertEqual(mat_item.size_display, "Tài liệu")

        quota = UserQuotaEntity.from_quota_row("u1", {"daily_token_limit": 1000, "daily_tokens_used": 850})
        q_dict = quota.to_status_dict()
        self.assertEqual(q_dict["percent_used"], 85.0)
        self.assertTrue(q_dict["warning_80"])

        enriched = MessageModel.enrich_messages_with_attachments(
            [{"id": "msg1", "content": "hello", "audio_attachment_id": "att9"}],
            [{"id": "att9", "message_id": "msg1", "filename": "v.webm"}],
        )
        self.assertEqual(enriched[0]["audio_url"], "/api/v1/attachments/att9/view")
        self.assertEqual(len(enriched[0]["attachments"]), 1)

    def test_pydantic_v2_schema_validators(self):
        with self.assertRaises(ValidationError):
            RuleCreateRequest(name="  ", content="ok")
        with self.assertRaises(ValidationError):
            RuleCreateRequest(name="r", content="ok", activation_mode="glob", glob_patterns=["../secret"])
        with self.assertRaises(ValidationError):
            SystemPromptCreateRequest(name="  ", content="ok")
        with self.assertRaises(ValidationError):
            ExamCreateRequest(title="Bad Exam", level="N99")
        with self.assertRaises(ValidationError):
            ReferenceMaterialCreateRequest(title="Bad URL", category="JLPT_N5", external_url="ftp://x.test")

    def test_fastapi_app_has_single_capabilities_route(self):
        from src.main import app

        cap_routes = [
            r for r in app.routes
            if getattr(r, "path", None) == "/api/v1/attachments/capabilities"
        ]
        self.assertEqual(len(cap_routes), 1)


if __name__ == "__main__":
    unittest.main()
