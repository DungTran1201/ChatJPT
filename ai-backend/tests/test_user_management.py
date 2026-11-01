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

class TestUserManagementAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.user_id = str(uuid.uuid4())
        self.email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        self.password = "ValidSecret123!"
        self.hashed_pw = hash_password(self.password)
        
        # Insert test user
        execute_commit(
            """
            INSERT INTO users (id, email, full_name, hashed_password, status, theme_preference, language_preference)
            VALUES (?, ?, 'Nguyen Van Test', ?, 'ACTIVE', 'DARK', 'vi')
            """,
            (self.user_id, self.email, self.hashed_pw)
        )
        
        # Token and cookies
        self.token = create_access_token(self.user_id, self.email)
        self.cookies = {"access_token": self.token}

    def tearDown(self):
        # Cleanup
        execute_commit("DELETE FROM users WHERE id = ?", (self.user_id,))

    def test_get_profile_and_stats(self):
        response = self.client.get("/api/v1/users/me", cookies=self.cookies)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("user", data)
        self.assertIn("stats", data)
        self.assertEqual(data["user"]["email"], self.email)
        self.assertEqual(data["user"]["full_name"], "Nguyen Van Test")
        self.assertIn("total_conversations", data["stats"])
        self.assertIn("total_messages", data["stats"])

    def test_update_profile_success(self):
        new_username = f"user_{uuid.uuid4().hex[:6]}"
        response = self.client.patch(
            "/api/v1/users/me/profile",
            json={
                "full_name": "Test Updated",
                "username": new_username,
                "bio": "Developer and AI researcher",
                "phone_number": "0987654321"
            },
            cookies=self.cookies
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user"]["full_name"], "Test Updated")
        self.assertEqual(data["user"]["username"], new_username)
        self.assertEqual(data["user"]["bio"], "Developer and AI researcher")
        self.assertEqual(data["user"]["phone_number"], "0987654321")

    def test_update_profile_personalization_fields(self):
        # Test personalization attributes (age, occupation, interests, japanese_level, learning_goal)
        response = self.client.patch(
            "/api/v1/users/me/profile",
            json={
                "full_name": "Yamada Taro",
                "age": 26,
                "occupation": "Software Engineer",
                "interests": "Anime, Manga, Tokyo Travel, Tech",
                "japanese_level": "N3",
                "learning_goal": "Kaiwa fluency for working in Tokyo"
            },
            cookies=self.cookies
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        user = data["user"]
        self.assertEqual(user["full_name"], "Yamada Taro")
        self.assertEqual(user["age"], 26)
        self.assertEqual(user["occupation"], "Software Engineer")
        self.assertEqual(user["interests"], "Anime, Manga, Tokyo Travel, Tech")
        self.assertEqual(user["japanese_level"], "N3")
        self.assertEqual(user["learning_goal"], "Kaiwa fluency for working in Tokyo")

        # Verify via GET /api/v1/users/me
        get_res = self.client.get("/api/v1/users/me", cookies=self.cookies)
        self.assertEqual(get_res.status_code, 200)
        get_user = get_res.json()["user"]
        self.assertEqual(get_user["age"], 26)
        self.assertEqual(get_user["occupation"], "Software Engineer")
        self.assertEqual(get_user["interests"], "Anime, Manga, Tokyo Travel, Tech")
        self.assertEqual(get_user["japanese_level"], "N3")
        self.assertEqual(get_user["learning_goal"], "Kaiwa fluency for working in Tokyo")

    def test_update_profile_invalid_age_rejected(self):
        # Age exceeds upper bound 120
        res1 = self.client.patch(
            "/api/v1/users/me/profile",
            json={"age": 150},
            cookies=self.cookies
        )
        self.assertEqual(res1.status_code, 422)

        # Age below lower bound 1
        res2 = self.client.patch(
            "/api/v1/users/me/profile",
            json={"age": 0},
            cookies=self.cookies
        )
        self.assertEqual(res2.status_code, 422)

    def test_update_profile_invalid_username(self):
        # Username with invalid characters or too short
        response = self.client.patch(
            "/api/v1/users/me/profile",
            json={"username": "ab"},
            cookies=self.cookies
        )
        self.assertEqual(response.status_code, 422)

    def test_update_avatar(self):
        avatar_url = "https://example.com/avatars/test.png"
        response = self.client.patch(
            "/api/v1/users/me/avatar",
            json={"avatar_url": avatar_url},
            cookies=self.cookies
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["avatar_url"], avatar_url)

    def test_change_email_wrong_password(self):
        response = self.client.post(
            "/api/v1/users/me/change-email",
            json={
                "new_email": "new_email@example.com",
                "current_password": "WrongPassword!"
            },
            cookies=self.cookies
        )
        self.assertEqual(response.status_code, 401)

    def test_change_email_success(self):
        new_email = f"new_{uuid.uuid4().hex[:8]}@example.com"
        response = self.client.post(
            "/api/v1/users/me/change-email",
            json={
                "new_email": new_email,
                "current_password": self.password
            },
            cookies=self.cookies
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["email"], new_email)

    def test_change_password_success(self):
        new_pw = "BrandNewPassword2026!"
        response = self.client.post(
            "/api/v1/users/me/change-password",
            json={
                "current_password": self.password,
                "new_password": new_pw
            },
            cookies=self.cookies
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.json())
        # Verify cookie is updated
        self.assertIn("access_token", response.cookies)

    def test_change_password_same_password_rejected(self):
        response = self.client.post(
            "/api/v1/users/me/change-password",
            json={
                "current_password": self.password,
                "new_password": self.password
            },
            cookies=self.cookies
        )
        self.assertEqual(response.status_code, 422)

    def test_update_preferences(self):
        # Test full UI customization update with ja, bg_dim, and custom hex color (FR-020, UC-015)
        response = self.client.patch(
            "/api/v1/users/me/preferences",
            json={
                "theme_preference": "LIGHT",
                "language_preference": "ja",
                "custom_bg_url": "https://images.unsplash.com/photo-japan-bg",
                "bg_opacity": 80,
                "bg_blur": 16,
                "bg_dim": 35,
                "accent_color": "#ff007f",
                "ui_font_size": "large"
            },
            cookies=self.cookies
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["theme_preference"], "LIGHT")
        self.assertEqual(data["language_preference"], "ja")
        self.assertEqual(data["custom_bg_url"], "https://images.unsplash.com/photo-japan-bg")
        self.assertEqual(data["bg_opacity"], 80)
        self.assertEqual(data["bg_blur"], 16)
        self.assertEqual(data["bg_dim"], 35)
        self.assertEqual(data["accent_color"], "#ff007f")
        self.assertEqual(data["ui_font_size"], "large")

        # Verify profile reflects updated preferences
        prof_res = self.client.get("/api/v1/users/me", cookies=self.cookies)
        self.assertEqual(prof_res.status_code, 200)
        user_data = prof_res.json()["user"]
        self.assertEqual(user_data["language_preference"], "ja")
        self.assertEqual(user_data["custom_bg_url"], "https://images.unsplash.com/photo-japan-bg")
        self.assertEqual(user_data["bg_opacity"], 80)
        self.assertEqual(user_data["bg_blur"], 16)
        self.assertEqual(user_data["bg_dim"], 35)
        self.assertEqual(user_data["accent_color"], "#ff007f")
        self.assertEqual(user_data["ui_font_size"], "large")

    def test_update_preferences_validation_errors(self):
        # Invalid opacity (< 20)
        res1 = self.client.patch(
            "/api/v1/users/me/preferences",
            json={"bg_opacity": 10},
            cookies=self.cookies
        )
        self.assertEqual(res1.status_code, 422)

        # Invalid blur (> 40)
        res2 = self.client.patch(
            "/api/v1/users/me/preferences",
            json={"bg_blur": 50},
            cookies=self.cookies
        )
        self.assertEqual(res2.status_code, 422)

        # Invalid bg_dim (> 100)
        res_dim = self.client.patch(
            "/api/v1/users/me/preferences",
            json={"bg_dim": 150},
            cookies=self.cookies
        )
        self.assertEqual(res_dim.status_code, 422)

        # Invalid language (e.g. fr)
        res_lang = self.client.patch(
            "/api/v1/users/me/preferences",
            json={"language_preference": "fr"},
            cookies=self.cookies
        )
        self.assertEqual(res_lang.status_code, 422)

        # Invalid accent color (neither preset nor valid hex)
        res3 = self.client.patch(
            "/api/v1/users/me/preferences",
            json={"accent_color": "neon_rainbow"},
            cookies=self.cookies
        )
        self.assertEqual(res3.status_code, 422)

        # Invalid ui_font_size
        res4 = self.client.patch(
            "/api/v1/users/me/preferences",
            json={"ui_font_size": "gigantic"},
            cookies=self.cookies
        )
        self.assertEqual(res4.status_code, 422)

if __name__ == "__main__":
    unittest.main()
