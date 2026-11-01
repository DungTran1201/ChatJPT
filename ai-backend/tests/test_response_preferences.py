import unittest
import sys
import uuid
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.main import app
from src.core.security import hash_password, create_access_token
from src.db import execute_commit

class TestResponsePreferencesAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.user_id = str(uuid.uuid4())
        self.email = f"test_response_pref_{uuid.uuid4().hex[:8]}@example.com"
        self.hashed_pw = hash_password("ValidPassword123!")

        execute_commit(
            "INSERT INTO users (id, email, full_name, hashed_password, status) VALUES (?, ?, 'Sensei Learner', ?, 'ACTIVE')",
            (self.user_id, self.email, self.hashed_pw)
        )
        self.token = create_access_token(self.user_id, self.email)
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def tearDown(self):
        execute_commit("DELETE FROM users WHERE id = ?", (self.user_id,))

    def test_01_default_response_preferences(self):
        res = self.client.get("/api/v1/users/me", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        user = res.json()["user"]
        self.assertTrue(user["response_show_translation"])
        self.assertTrue(user["response_show_furigana"])
        self.assertTrue(user["response_highlight_grammar"])
        self.assertTrue(user["response_show_romaji"])
        self.assertTrue(user["response_grammar_breakdown"])
        self.assertTrue(user["response_audio_speech"])
        self.assertEqual(user["response_bilingual_mode"], "interlinear")

    def test_02_update_response_preferences(self):
        payload = {
            "response_show_translation": False,
            "response_show_furigana": False,
            "response_highlight_grammar": False,
            "response_show_romaji": False,
            "response_grammar_breakdown": False,
            "response_audio_speech": False,
            "response_bilingual_mode": "parallel",
        }
        res = self.client.patch("/api/v1/users/me/preferences", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["response_show_translation"])
        self.assertFalse(data["response_show_furigana"])
        self.assertFalse(data["response_highlight_grammar"])
        self.assertFalse(data["response_show_romaji"])
        self.assertFalse(data["response_grammar_breakdown"])
        self.assertFalse(data["response_audio_speech"])
        self.assertEqual(data["response_bilingual_mode"], "parallel")

        # Verify persistent in GET /users/me
        get_res = self.client.get("/api/v1/users/me", headers=self.headers)
        self.assertEqual(get_res.status_code, 200)
        user = get_res.json()["user"]
        self.assertFalse(user["response_show_translation"])
        self.assertEqual(user["response_bilingual_mode"], "parallel")

    def test_03_invalid_bilingual_mode_422(self):
        payload = {"response_bilingual_mode": "invalid_mode"}
        res = self.client.patch("/api/v1/users/me/preferences", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 422)

if __name__ == "__main__":
    unittest.main()

