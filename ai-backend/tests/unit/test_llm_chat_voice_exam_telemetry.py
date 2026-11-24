"""Unit tests for LLM Orchestrator, PromptBuilder, STT, Embedded/Cache, VoiceVox, Exams, Telemetry."""

import asyncio
import tempfile
import unittest
from pathlib import Path

from llm.circuit_breaker import ScopedModelQuotaTracker
from llm.message_builder import build_langchain_messages
from src.core.database import DatabaseManager
from src.core.exceptions import ForbiddenError
from src.core.storage import LocalAttachmentStorage
from src.core.telemetry import MetricLogger, QuotaManager, SSEConnectionManager
from src.repositories.embedded_repo import EmbeddedRepository
from src.repositories.exam_repo import ExamRepository
from src.repositories.telemetry_repo import TelemetryRepository
from src.schemas.v1.exams import ExamCreateRequest, ExamSubmissionRequest
from src.services.embedded_model_service import EmbeddedModelService, resolve_embedded_weight_path
from src.services.exam_service import ExamService
from src.services.offline_responder import OfflineSenseiResponder
from src.services.prompt_builder import PedagogicalPromptBuilder
from src.services.semantic_cache_service import SemanticCacheService
from src.services.stt_service import HeuristicSTTFallbackProvider, STTService, detect_audio_mime
from src.services.voicevox_service import AcousticFallbackTTSProvider, TTSProvider, VoicevoxService

SCHEMA_SQL_PATH = Path(__file__).resolve().parent.parent.parent / "database" / "schema.sql"


def _init_temp_db(tmp_dir: str) -> DatabaseManager:
    db_path = Path(tmp_dir) / "engine_unit.db"
    db = DatabaseManager(db_path=db_path)
    with db.get_connection() as conn:
        conn.executescript(SCHEMA_SQL_PATH.read_text(encoding="utf-8"))
        conn.commit()
    return db


class _FakeRealTTSProvider(TTSProvider):
    is_fallback = False

    def __init__(self, should_succeed: bool = True):
        self.should_succeed = should_succeed
        self.calls = 0

    def synthesize(self, **kwargs):
        self.calls += 1
        return b"RIFFfakewavdata" if self.should_succeed else None


class TestLLMAndPromptBuilderAndSTT(unittest.TestCase):
    def tearDown(self):
        ScopedModelQuotaTracker.clear()

    def test_scoped_circuit_breaker_isolates_users(self):
        ScopedModelQuotaTracker.clear()
        ScopedModelQuotaTracker.record_quota_exhausted("gemini-3.8-flash", 60, user_id="user-a")
        self.assertFalse(ScopedModelQuotaTracker.is_available("gemini-3.8-flash", user_id="user-a"))
        self.assertTrue(ScopedModelQuotaTracker.is_available("gemini-3.8-flash", user_id="user-b"))

    def test_message_builder_sliding_window_and_4arg_attachment_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            storage = LocalAttachmentStorage(base_dir=Path(tmp))
            meta = storage.save("u1", "notes.txt", b"Japanese particle wa vs ga lesson")

            from unittest.mock import patch

            with patch("src.core.storage.default_storage", storage), patch(
                "src.core.attachment_storage.read_attachment_bytes", storage.read_bytes
            ):
                history = [{"role": "user", "content": f"h{i}"} for i in range(30)]
                msgs = build_langchain_messages(
                    "Explain this",
                    history,
                    attachments=[
                        {
                            "filename": meta["filename"],
                            "mime_type": meta["mime_type"],
                            "category": meta["category"],
                            "storage_path": meta["storage_path"],
                            "extracted_text": None,  # force fallback extraction path
                        }
                    ],
                )
                self.assertEqual(len(msgs), 22)
                self.assertIn("Japanese particle wa vs ga lesson", msgs[-1].content)

    def test_pedagogical_prompt_builder_trilingual_and_always_on_rules(self):
        builder = PedagogicalPromptBuilder()
        prompt = builder.build(
            user={"language_preference": "en", "response_show_furigana": 1, "response_show_translation": 1},
            sensei_row={"name": "Sakura Sensei", "japanese_level": "N4", "content": "Be warm and clear."},
            active_rules=[{"name": "No slang", "content": "Stick to polite desu/masu form."}],
        )
        self.assertIn("Sakura Sensei", prompt)
        self.assertIn("ALWAYS-ON RULES", prompt)
        self.assertIn("Stick to polite desu/masu form.", prompt)
        self.assertIn("ENGLISH", prompt)

    def test_stt_chain_fallback_and_mime_detection(self):
        self.assertEqual(detect_audio_mime("clip.wav"), "audio/wav")
        self.assertEqual(detect_audio_mime("clip.ogg"), "audio/ogg")
        stt = STTService(providers=[HeuristicSTTFallbackProvider()])
        res = asyncio.run(stt.transcribe(audio_bytes=b"1234", filename="voice.wav", language_hint="vi"))
        self.assertEqual(res.detected_language, "vi")
        self.assertEqual(res.engine_used, "heuristic_stt_fallback")


class TestEmbeddedCacheVoicesExamsTelemetry(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = _init_temp_db(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_embedded_path_traversal_blocked_and_cache_no_poisoning(self):
        with self.assertRaises(ValueError):
            resolve_embedded_weight_path("../../database/app", Path(self.tmp.name))

        emb_repo = EmbeddedRepository(self.db)
        cache_svc = SemanticCacheService(repo=emb_repo)

        generic_text, should_cache_generic = OfflineSenseiResponder.synthesize("random unmatched topic xyz123")
        self.assertFalse(should_cache_generic)
        self.assertTrue(generic_text)

        cache_svc.synthesize_offline("random unmatched topic xyz123")
        self.assertIsNone(cache_svc.lookup_entry("random unmatched topic xyz123"))

        cache_svc.synthesize_offline("luyện tập kaiwa nhà hàng")
        self.assertIsNotNone(cache_svc.lookup_entry("luyện tập kaiwa nhà hàng", threshold=0.40))

    def test_voicevox_never_caches_fallback_beep_but_caches_real_tts(self):
        failing_real = _FakeRealTTSProvider(should_succeed=False)
        svc = VoicevoxService(providers=[failing_real, AcousticFallbackTTSProvider()])
        wav1 = svc.synthesize("こんにちは", speaker_id=8)
        self.assertTrue(wav1.startswith(b"RIFF"))
        self.assertEqual(len(svc._audio_cache), 0)  # fallback MUST NOT be cached

        # Once real engine recovers, synthesis succeeds and gets cached
        failing_real.should_succeed = True
        wav2 = svc.synthesize("こんにちは", speaker_id=8)
        self.assertEqual(wav2, b"RIFFfakewavdata")
        self.assertEqual(len(svc._audio_cache), 1)
        wav3 = svc.synthesize("こんにちは", speaker_id=8)
        self.assertEqual(wav3, b"RIFFfakewavdata")
        self.assertEqual(failing_real.calls, 2)  # served from LRU cache on 3rd call

    def test_exam_anti_cheat_and_grading(self):
        exam_repo = ExamRepository(self.db)
        svc = ExamService(exam_repo)
        self.db.execute_commit(
            "INSERT INTO users (id, email, full_name, hashed_password, status) VALUES ('u1', 'u1@e.com', 'U1', 'h', 'ACTIVE')"
        )
        created = svc.create_exam(
            ExamCreateRequest(title="N5 Quiz", level="N5", max_score=100, passing_score=50),
            current_user={"id": "u1", "email": "u1@e.com"},
        )
        self.db.execute_commit(
            """
            INSERT INTO exam_questions (id, exam_id, question_number, question_text, option_1, option_2, option_3, option_4, correct_option, explanation)
            VALUES ('q1', ?, 1, '天気 reading?', 'てんき', 'げんき', 'でんき', 'べんき', 1, '天気 = てんき')
            """,
            (created.id,),
        )

        # Guest cannot bypass anti-cheat with include_answers=True
        guest_detail = svc.get_exam_detail(created.id, include_answers=True, current_user={"id": "guest_user"})
        self.assertIsNone(guest_detail.questions[0].correct_option)

        # Owner of custom exam CAN view answers
        owner_detail = svc.get_exam_detail(created.id, include_answers=True, current_user={"id": "u1", "email": "u1@e.com"})
        self.assertEqual(owner_detail.questions[0].correct_option, 1)

        # Non-owner cannot delete
        with self.assertRaises(ForbiddenError):
            svc.delete_exam(created.id, current_user={"id": "u2", "email": "u2@e.com"})

        # Out-of-range answer rejected as wrong; valid answer scores 100%
        bad_sub = svc.submit_exam(created.id, ExamSubmissionRequest(answers={"q1": 99}))
        self.assertFalse(bad_sub.passed)
        ok_sub = svc.submit_exam(created.id, ExamSubmissionRequest(answers={"q1": 1}))
        self.assertTrue(ok_sub.passed)
        self.assertEqual(ok_sub.score, 100)

    def test_telemetry_sql_aggregation_and_atomic_quota(self):
        self.db.execute_commit(
            "INSERT INTO users (id, email, full_name, hashed_password, status) VALUES ('tu1', 't@e.com', 'T', 'h', 'ACTIVE')"
        )
        repo = TelemetryRepository(self.db)
        qm = QuotaManager(repo)
        logger = MetricLogger(SSEConnectionManager(), repo, qm)

        qm.consume("tu1", 1500)
        allowed, used, limit, warn80 = qm.check("tu1", estimated_tokens=500)
        self.assertTrue(allowed)
        self.assertEqual(used, 1500)
        self.assertEqual(limit, 100000)
        self.assertFalse(warn80)

        logger.log_metric("/api/v1/chat", "POST", 200, 120.0, user_id="tu1", ttft_ms=40.0, provider="google", total_tokens=100)
        logger.log_metric("/api/v1/chat", "POST", 429, 10.0, user_id="tu1", provider="openai", total_tokens=50)
        summary = logger.get_metrics_summary("tu1", "24h")
        self.assertEqual(summary["total_requests"], 2)
        self.assertEqual(summary["status_counts"]["2xx"], 1)
        self.assertEqual(summary["status_counts"]["4xx"], 1)
        self.assertEqual(summary["tokens_by_provider"]["google"], 100)
        self.assertEqual(summary["tokens_by_provider"]["openai"], 50)
        self.assertEqual(len(summary["recent_trend"]), 2)


if __name__ == "__main__":
    unittest.main()
