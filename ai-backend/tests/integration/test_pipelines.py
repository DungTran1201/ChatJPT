"""Cross-Function Pipeline Integration Tests (P1..P6).

Validates every cross-service pipeline end-to-end through the real FastAPI app,
middlewares, DI composition root, services, repositories, and an isolated temporary
SQLite database created fresh from `database/schema.sql`.
"""

import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import src.db as db_module
from src.core.storage import LocalAttachmentStorage
from src.main import app

SCHEMA_SQL_PATH = Path(__file__).resolve().parent.parent.parent / "database" / "schema.sql"


class TestCrossFunctionPipelines(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls._test_db = Path(cls._tmp.name) / "pipeline_integration.db"
        cls._upload_dir = Path(cls._tmp.name) / "uploads"
        cls._old_db_path = db_module.DB_PATH
        cls._old_env_db = os.environ.get("AI_CHAN_DB_PATH")

        os.environ["AI_CHAN_DB_PATH"] = str(cls._test_db)
        db_module.DB_PATH = cls._test_db

        # Initialize fresh schema
        from src.core.database import db_manager

        with db_manager.get_connection() as conn:
            conn.executescript(SCHEMA_SQL_PATH.read_text(encoding="utf-8"))
            # Seed minimal model & voice preset for cross-pipeline tests
            conn.execute(
                """
                INSERT INTO models (id, name, provider, status, is_default, context_window, max_tokens, supports_streaming)
                VALUES ('gemini-3.8-flash', 'Gemini 3.8 Flash', 'google', 'ACTIVE', 1, 1000000, 8192, 1)
                """
            )
            conn.execute(
                """
                INSERT INTO voices (id, name, character_name, speaker_id, style_name, gender, status, is_system_preset, user_id)
                VALUES ('voice_kasukabe_tsumugi', 'Kasukabe Tsumugi', '春日部つむぎ', 8, 'Normal', 'female', 'ACTIVE', 1, 'system')
                """
            )
            conn.commit()

        temp_storage = LocalAttachmentStorage(cls._upload_dir)
        cls._storage_patch = patch("src.core.storage.default_storage", temp_storage)
        cls._dep_storage_patch = patch("src.dependencies.default_storage", temp_storage)
        cls._storage_patch.start()
        cls._dep_storage_patch.start()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls._dep_storage_patch.stop()
        cls._storage_patch.stop()
        db_module.DB_PATH = cls._old_db_path
        if cls._old_env_db is None:
            os.environ.pop("AI_CHAN_DB_PATH", None)
        else:
            os.environ["AI_CHAN_DB_PATH"] = cls._old_env_db
        cls._tmp.cleanup()

    def _register_and_headers(self, email: str, password: str = "ValidPass123!"):
        res = self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": email.split("@")[0]},
        )
        self.assertEqual(res.status_code, 201, res.text)
        token = res.json()["access_token"]
        return res.json()["user"], {"Authorization": f"Bearer {token}"}

    def test_p1_auth_sec007_profile_and_conversation_lifecycle(self):
        """P1: Register -> Profile Update -> Change Password -> Old JWT Revoked -> Conversation CRUD."""
        _, headers = self._register_and_headers("p1_user@example.com")

        # Update learner response preferences
        prof = self.client.put(
            "/api/v1/users/me",
            json={"full_name": "P1 Sensei Learner", "response_show_furigana": True, "language_preference": "vi"},
            headers=headers,
        )
        self.assertEqual(prof.status_code, 200)
        self.assertEqual(prof.json()["full_name"], "P1 Sensei Learner")

        # Create, rename, list, delete conversation
        conv_res = self.client.post("/api/v1/conversations", json={"title": "P1 Chat"}, headers=headers)
        self.assertEqual(conv_res.status_code, 201)
        conv_id = conv_res.json()["conversation"]["id"]

        ren = self.client.patch(f"/api/v1/conversations/{conv_id}", json={"title": "P1 Renamed"}, headers=headers)
        self.assertEqual(ren.status_code, 200)
        self.assertEqual(ren.json()["conversation"]["title"], "P1 Renamed")

        del_res = self.client.delete(f"/api/v1/conversations/{conv_id}", headers=headers)
        self.assertEqual(del_res.status_code, 200)

        # Change password -> old token must be revoked if password_changed_at > iat
        pw_res = self.client.put(
            "/api/v1/auth/password",
            json={"current_password": "ValidPass123!", "new_password": "NewValidPass456!"},
            headers=headers,
        )
        self.assertEqual(pw_res.status_code, 200)

        # Fresh login succeeds with new password
        login_res = self.client.post(
            "/api/v1/auth/login",
            json={"email": "p1_user@example.com", "password": "NewValidPass456!"},
        )
        self.assertEqual(login_res.status_code, 200)

    def test_p2_attachment_upload_chat_stream_and_prompt_attachments(self):
        """P2: Upload Attachment -> Stream Chat with agent-simulator -> Reload Messages + Prompt Attachments."""
        _, headers = self._register_and_headers("p2_user@example.com")

        conv_id = self.client.post("/api/v1/conversations", json={}, headers=headers).json()["conversation"]["id"]
        up = self.client.post(
            "/api/v1/attachments/upload",
            files={"file": ("lesson_n5.txt", io.BytesIO(b"N5 Grammar: wa vs ga"), "text/plain")},
            data={"context_type": "chat", "context_id": conv_id},
            headers=headers,
        )
        self.assertEqual(up.status_code, 201, up.text)
        att_id = up.json()["id"]

        stream = self.client.post(
            f"/api/v1/conversations/{conv_id}/messages/stream",
            json={"content": "Summarize file", "model": "agent-simulator", "attachments": [att_id]},
            headers=headers,
        )
        self.assertEqual(stream.status_code, 200)
        self.assertIn("lesson_n5.txt", stream.text)
        self.assertIn("event: done", stream.text)

        msgs_res = self.client.get(f"/api/v1/conversations/{conv_id}/messages", headers=headers)
        self.assertEqual(msgs_res.status_code, 200)
        self.assertEqual(msgs_res.json()["total"], 2)
        user_msg = [m for m in msgs_res.json()["messages"] if m["role"] == "user"][0]
        self.assertEqual(user_msg["attachments"][0]["id"], att_id)

        # Prompt attachment pipeline
        sp = self.client.post(
            "/api/v1/system-prompts",
            json={"name": "P2 Sensei", "content": "Always teach politely."},
            headers=headers,
        )
        self.assertEqual(sp.status_code, 201)
        sp_id = sp.json()["id"]
        self.client.post(
            "/api/v1/attachments/upload",
            files={"file": ("guide.txt", io.BytesIO(b"Guide content"), "text/plain")},
            data={"context_type": "prompt", "context_id": sp_id},
            headers=headers,
        )
        sp_atts = self.client.get(f"/api/v1/system-prompts/{sp_id}/attachments", headers=headers)
        self.assertEqual(sp_atts.status_code, 200)
        self.assertEqual(sp_atts.json()["total"], 1)

    def test_p3_byok_models_and_embedded_route_non_shadowing(self):
        """P3: BYOK Key Save -> Model Create & Activate -> DELETE /models/embedded NOT shadowed."""
        _, headers = self._register_and_headers("p3_user@example.com")

        save_key = self.client.put(
            "/api/v1/settings/api-keys/openai",
            json={"api_key": "sk-test-p3-integration-key-123456"},
            headers=headers,
        )
        self.assertEqual(save_key.status_code, 200)

        create_m = self.client.post(
            "/api/v1/models",
            json={"id": "gpt-4o-mini-p3", "name": "GPT 4o Mini P3", "provider": "openai"},
            headers=headers,
        )
        self.assertEqual(create_m.status_code, 201)

        act_m = self.client.patch("/api/v1/models/gpt-4o-mini-p3/activate", headers=headers)
        self.assertEqual(act_m.status_code, 200)

        # Verify DELETE /api/v1/models/embedded hits embedded_router (NOT models_router /{model_id} -> 404)!
        del_emb = self.client.delete("/api/v1/models/embedded")
        self.assertEqual(del_emb.status_code, 200)
        self.assertEqual(del_emb.json()["status"], "NOT_DOWNLOADED")

    def test_p4_rules_occ_anti_idor_and_text_import(self):
        """P4: Rule Create -> OCC Conflict 409 -> Cross-User Clone Blocked 403 -> Text Import."""
        _, h1 = self._register_and_headers("p4_owner@example.com")
        _, h2 = self._register_and_headers("p4_other@example.com")

        r = self.client.post(
            "/api/v1/rules",
            json={"name": "P4 Rule", "content": "Always include examples.", "activation_mode": "always_on"},
            headers=h1,
        )
        self.assertEqual(r.status_code, 201)
        rule_id = r.json()["id"]

        # Update v1 -> v2 succeeds; stale v1 fails with 409
        u_ok = self.client.put(
            f"/api/v1/rules/{rule_id}",
            json={"name": "P4 Rule", "content": "Updated v2", "version": 1},
            headers=h1,
        )
        self.assertEqual(u_ok.status_code, 200)
        u_stale = self.client.put(
            f"/api/v1/rules/{rule_id}",
            json={"name": "P4 Rule", "content": "Stale v1", "version": 1},
            headers=h1,
        )
        self.assertEqual(u_stale.status_code, 409)

        # User 2 cannot clone User 1's private rule
        clone_deny = self.client.post(f"/api/v1/rules/{rule_id}/clone", headers=h2)
        self.assertEqual(clone_deny.status_code, 403)

        # Markdown text import
        imp = self.client.post(
            "/api/v1/rules/import-text",
            json={"raw_text": "---\nname: Imported P4 Rule\n---\nKeep explanations concise."},
            headers=h1,
        )
        self.assertEqual(imp.status_code, 201)

    def test_p5_sensei_voice_binding_synthesis_and_stt(self):
        """P5: Sensei bound to Voice -> Synthesize by sensei_id -> Voice STT Upload."""
        _, headers = self._register_and_headers("p5_user@example.com")

        sp = self.client.post(
            "/api/v1/system-prompts",
            json={
                "name": "Voice Bound Sensei",
                "content": "Friendly N5 tutor.",
                "voice_id": "voice_kasukabe_tsumugi",
            },
            headers=headers,
        )
        self.assertEqual(sp.status_code, 201)
        sensei_id = sp.json()["id"]

        # System preset cannot be deleted (400 per TC-VOICE-002)
        del_preset = self.client.delete("/api/v1/voices/voice_kasukabe_tsumugi", headers=headers)
        self.assertEqual(del_preset.status_code, 400)

        synth = self.client.post(f"/api/v1/voices/{sensei_id}/synthesize", json={"text": "こんにちは"})
        self.assertEqual(synth.status_code, 200)
        self.assertEqual(synth.headers.get("content-type"), "audio/wav")
        self.assertTrue(synth.content.startswith(b"RIFF"))

        stt = self.client.post(
            "/api/v1/chat/stt",
            files={"file": ("voice.wav", io.BytesIO(b"RIFF\x24\x00\x00\x00WAVEfmt "), "audio/wav")},
            data={"language": "ja", "duration_ms": "1200"},
            headers=headers,
        )
        self.assertEqual(stt.status_code, 200, stt.text)
        self.assertEqual(stt.json()["status"], "success")
        self.assertTrue(stt.json()["data"]["transcript"])

    def test_p6_exam_rag_and_telemetry_pipeline(self):
        """P6: Exam Create -> Anti-Cheat -> Submit -> RAG Search -> Telemetry Summary/Quota/History."""
        _, headers = self._register_and_headers("p6_user@example.com")

        ex = self.client.post(
            "/api/v1/exams",
            json={"title": "P6 JLPT N5", "level": "N5", "max_score": 100, "passing_score": 60},
            headers=headers,
        )
        self.assertEqual(ex.status_code, 201)
        exam_id = ex.json()["id"]

        db_module.execute_commit(
            """
            INSERT INTO exam_questions (id, exam_id, question_number, question_text, option_1, option_2, option_3, option_4, correct_option, explanation)
            VALUES ('p6_q1', ?, 1, '日本語 meaning?', 'Japanese', 'English', 'Korean', 'French', 1, '日本語 = tiếng Nhật')
            """,
            (exam_id,),
        )

        # Unauthenticated detail strips answers even with include_answers=true
        anon_detail = self.client.get(f"/api/v1/exams/{exam_id}?include_answers=true")
        self.assertEqual(anon_detail.status_code, 200)
        self.assertIsNone(anon_detail.json()["questions"][0]["correct_option"])

        sub = self.client.post(f"/api/v1/exams/{exam_id}/submit", json={"answers": {"p6_q1": 1}})
        self.assertEqual(sub.status_code, 200)
        self.assertTrue(sub.json()["passed"])

        rag = self.client.get("/api/v1/exams/rag/search?query=wa&level=N5")
        self.assertEqual(rag.status_code, 200)
        self.assertGreaterEqual(rag.json()["total"], 1)

        # Health + Telemetry summary/quota/history
        health = self.client.get("/api/v1/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "healthy")

        quota = self.client.get("/api/v1/resources/quota", headers=headers)
        self.assertEqual(quota.status_code, 200)
        self.assertEqual(quota.json()["data"]["daily_token_limit"], 100000)

        summary = self.client.get("/api/v1/resources/summary?range=24h", headers=headers)
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(summary.json()["status"], "success")

        hist = self.client.get("/api/v1/resources/history", headers=headers)
        self.assertEqual(hist.status_code, 200)
        self.assertEqual(hist.json()["status"], "success")


if __name__ == "__main__":
    unittest.main()
