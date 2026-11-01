import io
import sys
import uuid
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

# Add src and parent to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.main import app
from src.core.security import hash_password, create_access_token
from src.db import execute_commit, query_one


class TestTextFileImport(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.user_a_id = f"usr_a_{uuid.uuid4().hex[:8]}"
        self.email_a = f"import_user_a_{uuid.uuid4().hex[:8]}@example.com"
        self.user_b_id = f"usr_b_{uuid.uuid4().hex[:8]}"
        self.email_b = f"import_user_b_{uuid.uuid4().hex[:8]}@example.com"
        self.hashed_pw = hash_password("ValidSecret123!")

        # Create two test users
        execute_commit(
            "INSERT INTO users (id, email, full_name, hashed_password, status) VALUES (?, ?, 'Importer A', ?, 'ACTIVE')",
            (self.user_a_id, self.email_a, self.hashed_pw)
        )
        execute_commit(
            "INSERT INTO users (id, email, full_name, hashed_password, status) VALUES (?, ?, 'Importer B', ?, 'ACTIVE')",
            (self.user_b_id, self.email_b, self.hashed_pw)
        )

        self.token_a = create_access_token(self.user_a_id, self.email_a)
        self.token_b = create_access_token(self.user_b_id, self.email_b)

        self.headers_a = {"Authorization": f"Bearer {self.token_a}"}
        self.headers_b = {"Authorization": f"Bearer {self.token_b}"}

    def tearDown(self):
        # Dọn dẹp database
        execute_commit("DELETE FROM rules WHERE user_id IN (?, ?)", (self.user_a_id, self.user_b_id))
        execute_commit("DELETE FROM system_prompts WHERE user_id IN (?, ?)", (self.user_a_id, self.user_b_id))
        execute_commit("DELETE FROM users WHERE id IN (?, ?)", (self.user_a_id, self.user_b_id))

    # ==========================================================================
    # 1. RULES TEXT IMPORT TESTS
    # ==========================================================================
    def test_01_rules_import_from_file_and_text(self):
        """Kiểm tra nhập Rule từ file markdown và qua /rules/import-text."""
        rule_md = (
            "---\n"
            "name: Strict Japanese Grammar Rule\n"
            "description: Yêu cầu giải thích cấu trúc ngữ pháp và kanji\n"
            "activation_mode: glob\n"
            "glob_patterns:\n"
            "  - 'src/**/*.ts'\n"
            "  - 'src/**/*.tsx'\n"
            "priority: 80\n"
            "---\n\n"
            "Luôn giải thích Furigana và ví dụ ngữ cảnh cụ thể cho học viên.\n"
        ).encode("utf-8")

        # 1. Nhập từ file multipart
        res = self.client.post(
            "/api/v1/rules/import-file",
            headers=self.headers_a,
            files={"file": ("japanese_rules.md", io.BytesIO(rule_md), "text/markdown")}
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["name"], "Strict Japanese Grammar Rule")
        self.assertEqual(data["activation_mode"], "glob")
        self.assertEqual(data["glob_patterns"], ["src/**/*.ts", "src/**/*.tsx"])
        self.assertEqual(data["priority"], 80)
        self.assertEqual(data["scope"], "user")

        # 2. Nhập từ JSON text payload
        text_payload = {
            "filename": "grammar_standards.rst",
            "content": "Tuân thủ phân tích trợ từ は và が chính xác.",
            "name": "Japanese Particle Guidelines",
            "description": "Tiêu chuẩn phân biệt trợ từ",
            "activation_mode": "always_on",
            "priority": 70
        }
        res2 = self.client.post(
            "/api/v1/rules/import-text",
            headers=self.headers_a,
            json=text_payload
        )
        self.assertEqual(res2.status_code, 201)
        data2 = res2.json()
        self.assertEqual(data2["name"], "Japanese Particle Guidelines")
        self.assertEqual(data2["priority"], 70)

    def test_02_rules_reject_binary(self):
        """Kiểm tra từ chối nhập file nhị phân vào Rules Library."""
        fake_bin = b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00"
        res = self.client.post(
            "/api/v1/rules/import-file",
            headers=self.headers_a,
            files={"file": ("binary_rule.md", io.BytesIO(fake_bin), "text/markdown")}
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("nhị phân", res.text)

    # ==========================================================================
    # 2. SYSTEM PROMPTS TEXT IMPORT TESTS
    # ==========================================================================
    def test_03_system_prompts_import_unicode_and_placeholders(self):
        """Kiểm tra nhập System Prompt bảo toàn Unicode, tiếng Việt, emoji và placeholder."""
        prompt_text = (
            "Bạn là giáo viên Sensei AI-Chan tận tâm 🌟.\n"
            "Cấp độ học viên: {jlpt_level}\n"
            "Chủ đề Kaiwa: {conversation_topic}\n"
            "Hãy sửa lỗi ngữ pháp nhẹ nhàng và khích lệ người học!\n"
        ).encode("utf-8")

        res = self.client.post(
            "/api/v1/system-prompts/import-file",
            headers=self.headers_a,
            files={"file": ("sensei_persona.txt", io.BytesIO(prompt_text), "text/plain")}
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["name"], "sensei persona")
        self.assertIn("Sensei AI-Chan tận tâm 🌟", data["content"])
        self.assertIn("{jlpt_level}", data["content"])

        # Nhập lần 2 trùng tên -> 409
        res_dup = self.client.post(
            "/api/v1/system-prompts/import-file",
            headers=self.headers_a,
            files={"file": ("sensei_persona.txt", io.BytesIO(prompt_text), "text/plain")}
        )
        self.assertEqual(res_dup.status_code, 409)

    def test_04_system_prompts_import_text_api(self):
        """Kiểm tra nhập System Prompt qua /system-prompts/import-text."""
        payload = {
            "filename": "kaiwa_sensei.yaml",
            "content": "---\nname: Kaiwa Sensei\ndescription: Hướng dẫn đàm thoại\n---\nBạn là giáo viên đàm thoại bản xứ.",
            "name": "Custom Kaiwa Sensei",
            "description": "Giáo viên luyện Kaiwa phản xạ"
        }
        res = self.client.post(
            "/api/v1/system-prompts/import-text",
            headers=self.headers_a,
            json=payload
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["name"], "Custom Kaiwa Sensei")
        self.assertEqual(data["description"], "Giáo viên luyện Kaiwa phản xạ")

    # ==========================================================================
    # 3. USER ISOLATION / ANTI-IDOR TESTS
    # ==========================================================================
    def test_05_user_isolation(self):
        """Kiểm tra tính năng cách ly người dùng (Anti-IDOR): User B không thấy và không sửa được item của User A."""
        # User A imports a rule
        rule_content = "Quy tắc ngữ pháp riêng của User A".encode("utf-8")
        res_rule = self.client.post(
            "/api/v1/rules/import-file",
            headers=self.headers_a,
            files={"file": ("user_a_rule.txt", io.BytesIO(rule_content), "text/plain")}
        )
        self.assertEqual(res_rule.status_code, 201)
        rule_id = res_rule.json()["id"]

        # User B cannot get or delete this rule
        res_get_b = self.client.get(f"/api/v1/rules/{rule_id}", headers=self.headers_b)
        self.assertEqual(res_get_b.status_code, 404)

        res_del_b = self.client.delete(f"/api/v1/rules/{rule_id}", headers=self.headers_b)
        self.assertEqual(res_del_b.status_code, 404)
