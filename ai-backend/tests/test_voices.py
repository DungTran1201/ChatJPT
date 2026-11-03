import unittest
import sys
import uuid
from pathlib import Path
from fastapi.testclient import TestClient

# Add src and parent to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.main import app
from src.core.security import hash_password, create_access_token
from src.db import execute_commit, query_one
from src.services.voicevox_service import voicevox_service

class TestVoicesAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.user_id = str(uuid.uuid4())
        self.email = f"voice_test_{uuid.uuid4().hex[:8]}@example.com"
        self.hashed_pw = hash_password("ValidSecret123!")

        execute_commit(
            "INSERT INTO users (id, email, full_name, hashed_password, status) VALUES (?, ?, 'Voice Tester', ?, 'ACTIVE')",
            (self.user_id, self.email, self.hashed_pw)
        )
        self.token = create_access_token(self.user_id, self.email)
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def tearDown(self):
        # Cleanup custom test voices and user
        execute_commit("DELETE FROM voices WHERE user_id = ?", (self.user_id,))
        execute_commit("DELETE FROM users WHERE id = ?", (self.user_id,))

    def test_engine_status(self):
        """TC-VOICE-003: Check VoiceVox local engine status endpoint."""
        resp = self.client.get("/api/v1/voices/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("engine_available", data)
        self.assertIn("engine_url", data)
        self.assertIn("cached_audio_count", data)

    def test_list_voices_and_filters(self):
        """TC-VOICE-001: List voices with filtering and search."""
        # 1. List all
        resp = self.client.get("/api/v1/voices")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(data["total"], 14)

        # 2. Filter by gender = female
        resp_female = self.client.get("/api/v1/voices?gender=female")
        self.assertEqual(resp_female.status_code, 200)
        data_female = resp_female.json()
        self.assertTrue(all(item["gender"] == "female" for item in data_female["items"]))

        # 3. Search keyword
        resp_search = self.client.get("/api/v1/voices?q=Tsumugi")
        self.assertEqual(resp_search.status_code, 200)
        data_search = resp_search.json()
        self.assertGreaterEqual(data_search["total"], 1)

    def test_get_voice_detail(self):
        """TC-VOICE-001: Get voice by ID."""
        resp = self.client.get("/api/v1/voices/voice_kasukabe_tsumugi")
        self.assertEqual(resp.status_code, 200)
        voice = resp.json()
        self.assertEqual(voice["id"], "voice_kasukabe_tsumugi")
        self.assertEqual(voice["speaker_id"], 8)

        # Not found
        resp_404 = self.client.get("/api/v1/voices/voice_non_existent_999")
        self.assertEqual(resp_404.status_code, 404)

    def test_create_update_and_delete_custom_voice(self):
        """TC-VOICE-002: Create, update acoustic parameters, and delete custom voice."""
        # 1. Create custom voice
        create_payload = {
            "name": "Custom Test Sensei Voice",
            "character_name": "テスト先生",
            "speaker_id": 8,
            "style_name": "Energetic",
            "gender": "female",
            "speed_scale": 1.15,
            "pitch_scale": 0.05,
            "intonation_scale": 1.2,
            "volume_scale": 1.0,
            "sample_text": "テストメッセージです。"
        }
        create_resp = self.client.post("/api/v1/voices", json=create_payload, headers=self.headers)
        self.assertEqual(create_resp.status_code, 201)
        created_voice = create_resp.json()
        voice_id = created_voice["id"]
        self.assertEqual(created_voice["speed_scale"], 1.15)

        # 2. Update acoustic parameters
        update_payload = {
            "speed_scale": 1.25,
            "pitch_scale": -0.05
        }
        update_resp = self.client.put(f"/api/v1/voices/{voice_id}", json=update_payload, headers=self.headers)
        self.assertEqual(update_resp.status_code, 200)
        updated_voice = update_resp.json()
        self.assertEqual(updated_voice["speed_scale"], 1.25)
        self.assertEqual(updated_voice["pitch_scale"], -0.05)

        # 3. Boundary validation rejection (BR-040: speed > 2.0)
        invalid_resp = self.client.put(f"/api/v1/voices/{voice_id}", json={"speed_scale": 3.5}, headers=self.headers)
        self.assertEqual(invalid_resp.status_code, 422)

        # 4. Cannot delete system preset
        del_preset_resp = self.client.delete("/api/v1/voices/voice_kasukabe_tsumugi", headers=self.headers)
        self.assertEqual(del_preset_resp.status_code, 400)

        # 5. Delete custom voice
        del_resp = self.client.delete(f"/api/v1/voices/{voice_id}", headers=self.headers)
        self.assertEqual(del_resp.status_code, 200)

    def test_audio_synthesis_and_fallback(self):
        """TC-VOICE-005 & TC-VOICE-006: Audio synthesis pipeline and fallback WAV."""
        # 1. Adhoc synthesis
        synth_payload = {
            "text": "こんにちは！一緒に勉強しましょう。",
            "speaker_id": 8,
            "speed_scale": 1.0,
            "pitch_scale": 0.0
        }
        resp = self.client.post("/api/v1/voices/synthesize", json=synth_payload)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("content-type"), "audio/wav")
        audio_content = resp.content
        self.assertTrue(audio_content.startswith(b"RIFF"), "Should be a valid WAV file starting with RIFF")
        self.assertGreater(len(audio_content), 1000)

        # 2. Synthesis by voice_id
        resp_id = self.client.post(
            "/api/v1/voices/voice_kasukabe_tsumugi/synthesize",
            json={"text": "はじめまして。"}
        )
        self.assertEqual(resp_id.status_code, 200)
        self.assertEqual(resp_id.headers.get("content-type"), "audio/wav")
        self.assertTrue(resp_id.content.startswith(b"RIFF"))

    def test_sensei_voice_binding(self):
        """TC-VOICE-004: Sensei Guidance voice binding."""
        # Create a Sensei with voice_id
        sensei_payload = {
            "name": "Test Voice Sensei",
            "content": "You are an AI Sensei with VoiceVox voice.",
            "japanese_level": "N3",
            "voice_id": "voice_kasukabe_tsumugi"
        }
        create_resp = self.client.post("/api/v1/system-prompts", json=sensei_payload, headers=self.headers)
        self.assertEqual(create_resp.status_code, 201)
        created_sensei = create_resp.json()
        self.assertEqual(created_sensei["voice_id"], "voice_kasukabe_tsumugi")

        # Update Sensei with a different voice
        update_resp = self.client.put(
            f"/api/v1/system-prompts/{created_sensei['id']}",
            json={
                "name": "Test Voice Sensei Updated",
                "content": "Updated persona instructions.",
                "voice_id": "voice_shikoku_metan_sweet"
            },
            headers=self.headers
        )
        self.assertEqual(update_resp.status_code, 200)
        updated_sensei = update_resp.json()
        self.assertEqual(updated_sensei["voice_id"], "voice_shikoku_metan_sweet")

        # Cleanup sensei
        execute_commit("DELETE FROM system_prompts WHERE id = ?", (created_sensei["id"],))

if __name__ == "__main__":
    unittest.main()
