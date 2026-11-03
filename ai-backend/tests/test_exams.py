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

class TestExamsAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.user_id = str(uuid.uuid4())
        self.email = f"exam_tester_{uuid.uuid4().hex[:8]}@example.com"
        self.hashed_pw = hash_password("ValidSecret123!")

        execute_commit(
            "INSERT INTO users (id, email, full_name, hashed_password, status) VALUES (?, ?, 'Exam Tester', ?, 'ACTIVE')",
            (self.user_id, self.email, self.hashed_pw)
        )
        self.token = create_access_token(self.user_id, self.email)
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def tearDown(self):
        execute_commit("DELETE FROM exams WHERE user_id = ?", (self.user_id,))
        execute_commit("DELETE FROM reference_materials WHERE user_id = ?", (self.user_id,))
        execute_commit("DELETE FROM users WHERE id = ?", (self.user_id,))

    def test_list_exams_and_filter(self):
        """TC-EXAM-001: List exams and filter by level."""
        res = self.client.get("/api/v1/exams")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data["total"], 6)

        # Filter by N5
        res_n5 = self.client.get("/api/v1/exams?level=N5")
        self.assertEqual(res_n5.status_code, 200)
        data_n5 = res_n5.json()
        for item in data_n5["items"]:
            self.assertEqual(item["level"], "N5")

    def test_create_and_delete_custom_exam(self):
        """TC-EXAM-002: Create custom exam with valid metadata and delete it."""
        payload = {
            "title": "Custom Test JLPT N5 Unit 1",
            "description": "Custom mock quiz for N5 vocabulary",
            "level": "N5",
            "category": "VOCABULARY",
            "year": 2024,
            "duration_minutes": 45,
            "passing_score": 70,
            "max_score": 100,
            "drive_folder_url": "https://drive.google.com/drive/folders/sample_folder_id"
        }
        res = self.client.post("/api/v1/exams", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 201)
        created = res.json()
        exam_id = created["id"]
        self.assertEqual(created["title"], payload["title"])
        self.assertFalse(created["is_system_preset"])

        # Delete the custom exam
        del_res = self.client.delete(f"/api/v1/exams/{exam_id}", headers=self.headers)
        self.assertEqual(del_res.status_code, 200)

    def test_protect_system_preset_exam(self):
        """TC-EXAM-003: Protect system preset exams from deletion (BR-044)."""
        res = self.client.delete("/api/v1/exams/exam_seed_n5_full", headers=self.headers)
        self.assertEqual(res.status_code, 403)
        self.assertIn("Không thể xóa bộ đề thi mặc định", res.json()["detail"])

    def test_exam_detail_and_submission(self):
        """TC-EXAM-004: Take interactive exam, submit answers, and receive score + explanations."""
        # Get exam details (answers masked)
        res = self.client.get("/api/v1/exams/exam_seed_n5_full")
        self.assertEqual(res.status_code, 200)
        detail = res.json()
        self.assertGreaterEqual(len(detail["questions"]), 1)
        self.assertIsNone(detail["questions"][0]["correct_option"])

        # Submit answers
        q_01_id = detail["questions"][0]["id"]
        submission_payload = {
            "answers": {
                q_01_id: 1 # Option 1 (てんき) is correct for q_n5_01
            }
        }
        sub_res = self.client.post(f"/api/v1/exams/{detail['id']}/submit", json=submission_payload)
        self.assertEqual(sub_res.status_code, 200)
        sub_data = sub_res.json()
        self.assertEqual(sub_data["exam_id"], detail["id"])
        self.assertGreaterEqual(sub_data["correct_count"], 1)
        self.assertTrue(len(sub_data["results"]) >= 1)
        self.assertIn("feedback_message", sub_data)

    def test_reference_materials_catalog(self):
        """TC-EXAM-005: Browse reference materials (Google Drive, Tae Kim, Dictionary)."""
        res = self.client.get("/api/v1/exams/materials")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data["total"], 8)

        # Check Tae Kim grammar guide exists
        items = data["items"]
        tae_kim = next((m for m in items if "Tae Kim" in m["title"]), None)
        self.assertIsNotNone(tae_kim)
        self.assertEqual(tae_kim["source_type"], "WEB_GUIDE")
        self.assertTrue(tae_kim["external_url"].startswith("https://"))

        # Check Google Drive links exist
        drive_mats = [m for m in items if m["source_type"] == "GOOGLE_DRIVE"]
        self.assertGreaterEqual(len(drive_mats), 6)

    def test_sanitization_and_validation(self):
        """TC-EXAM-006: Insecure or invalid inputs rejected."""
        # Invalid level
        bad_exam = {
            "title": "Bad Level Exam",
            "level": "N99",
            "duration_minutes": 60
        }
        res = self.client.post("/api/v1/exams", json=bad_exam, headers=self.headers)
        self.assertEqual(res.status_code, 422)

        # Non-HTTPS URL
        bad_mat = {
            "title": "Insecure Material",
            "category": "JLPT_N5",
            "external_url": "http://insecure-site.com/materials"
        }
        res_mat = self.client.post("/api/v1/exams/materials", json=bad_mat, headers=self.headers)
        self.assertEqual(res_mat.status_code, 422)

if __name__ == "__main__":
    unittest.main()
