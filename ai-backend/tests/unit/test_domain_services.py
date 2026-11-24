"""Unit tests for Auth, Users, Conversations, Credentials, Models, Storage, Prompts, Rules, and TextImport."""

import asyncio
import tempfile
import unittest
from pathlib import Path

from src.core.database import DatabaseManager
from src.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationDomainError
from src.core.secret_vault import SecretVault
from src.core.storage import FileSecurityValidator, LocalAttachmentStorage, TextExtractor
from src.repositories.api_key_repo import ApiKeyRepository
from src.repositories.attachment_repo import AttachmentRepository
from src.repositories.conversation_repo import ConversationRepository
from src.repositories.model_repo import ModelRepository
from src.repositories.prompt_repo import PromptRepository
from src.repositories.rule_repo import RuleRepository
from src.repositories.user_repo import UserRepository
from src.schemas.v1.auth import ChangePasswordRequest, LoginRequest, RegisterRequest
from src.schemas.v1.models import ModelCreateRequest
from src.schemas.v1.prompts import PromptCreateRequest, PromptUpdateRequest
from src.schemas.v1.rules import RuleCreateRequest, RuleUpdateRequest
from src.schemas.v1.users import UserProfileUpdate
from src.services.attachment_service import AttachmentService, build_content_disposition
from src.services.auth_service import AuthService
from src.services.conversation_service import ConversationService
from src.services.credential_service import CredentialService
from src.services.env_file_store import EnvFileStore
from src.services.model_service import ModelService
from src.services.prompt_service import PromptService
from src.services.provider_registry import ProviderRegistry, ProviderSpec, redact_secrets_from_text, validate_ollama_url
from src.services.rule_service import RuleService
from src.services.text_import_service import TextImportService
from src.services.user_service import UserService

SCHEMA_SQL_PATH = Path(__file__).resolve().parent.parent.parent / "database" / "schema.sql"


def _init_temp_db(tmp_dir: str) -> DatabaseManager:
    db_path = Path(tmp_dir) / "domain_unit.db"
    db = DatabaseManager(db_path=db_path)
    schema_sql = SCHEMA_SQL_PATH.read_text(encoding="utf-8")
    with db.get_connection() as conn:
        conn.executescript(schema_sql)
        conn.commit()
    return db


class TestAuthUserConversationServices(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = _init_temp_db(self.tmp.name)
        self.user_repo = UserRepository(self.db)
        self.conv_repo = ConversationRepository(self.db)
        self.auth_svc = AuthService(self.user_repo)
        self.user_svc = UserService(self.user_repo)
        self.conv_svc = ConversationService(self.conv_repo)

    def tearDown(self):
        self.tmp.cleanup()

    def test_auth_lifecycle_and_password_change_sets_timestamp(self):
        reg = self.auth_svc.register(
            RegisterRequest(email="alice@example.com", password="Password123!", full_name="Alice")
        )
        self.assertEqual(reg.user.email, "alice@example.com")
        logged = self.auth_svc.login(LoginRequest(email="alice@example.com", password="Password123!"))
        self.assertTrue(logged.access_token)

        self.auth_svc.change_password(
            reg.user.id,
            ChangePasswordRequest(current_password="Password123!", new_password="NewPassword456!"),
        )
        user_row = self.user_repo.get_by_id(reg.user.id)
        self.assertIsNotNone(user_row.get("password_changed_at"))

    def test_user_service_blocks_xss_urls_and_rotates_token_on_email_change(self):
        reg = self.auth_svc.register(
            RegisterRequest(email="bob@example.com", password="Password123!", full_name="Bob")
        )
        user_row = self.user_repo.get_by_id(reg.user.id)

        with self.assertRaises(ValidationDomainError):
            self.user_svc.update_profile(user_row, UserProfileUpdate(avatar_url="javascript:alert(1)"))

        updated, new_token = self.user_svc.update_profile(
            user_row,
            UserProfileUpdate(email="bob.new@example.com", full_name="Bob Updated"),
        )
        self.assertEqual(updated.email, "bob.new@example.com")
        self.assertIsNotNone(new_token)

    def test_conversation_pagination_total_and_anti_idor(self):
        u1 = self.auth_svc.register(RegisterRequest(email="u1@example.com", password="Password123!", full_name="U1"))
        u2 = self.auth_svc.register(RegisterRequest(email="u2@example.com", password="Password123!", full_name="U2"))

        created = self.conv_svc.create(u1.user.id, "Test Conv")
        conv_id = created["conversation"]["id"]
        for i in range(5):
            self.conv_repo.insert_user_message(message_id=f"m{i}", conversation_id=conv_id, content=f"msg {i}")

        page = self.conv_svc.list_messages(conv_id, u1.user.id, limit=2, offset=0)
        self.assertEqual(page["total"], 5)
        self.assertEqual(len(page["messages"]), 2)

        with self.assertRaises(NotFoundError):
            self.conv_svc.list_messages(conv_id, u2.user.id, limit=10, offset=0)


class TestProviderCredentialsAndModels(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = _init_temp_db(self.tmp.name)
        self.user_repo = UserRepository(self.db)
        self.auth_svc = AuthService(self.user_repo)
        self.u1 = self.auth_svc.register(
            RegisterRequest(email="keys@example.com", password="Password123!", full_name="KeyUser")
        ).user
        self.vault = SecretVault(key_provider=lambda: "test-vault-secret-key-for-unit-tests")
        self.env_path = Path(self.tmp.name) / ".env"
        self.env_store = EnvFileStore(env_path=self.env_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_ssrf_guard_and_env_injection_block(self):
        self.assertEqual(validate_ollama_url("http://localhost:11434/"), "http://localhost:11434")
        with self.assertRaises(ValueError):
            validate_ollama_url("http://169.254.169.254/latest/meta-data")
        with self.assertRaises(ValueError):
            self.env_store.update_variable("GEMINI_API_KEY", "abc\nINJECTED=1")
        with self.assertRaises(ValueError):
            self.env_store.update_variable("JWT_SECRET_KEY", "hacked")

        res = self.env_store.update_variable("GEMINI_API_KEY", "AIzaSyFakeKeyForUnitTest1234567890")
        self.assertEqual(res["env_var"], "GEMINI_API_KEY")
        self.assertIn("GEMINI_API_KEY=AIzaSyFakeKeyForUnitTest1234567890", self.env_path.read_text(encoding="utf-8"))

    def test_candidate_key_probe_does_not_overwrite_saved_key_status(self):
        async def fake_probe(api_key: str, _model_id=None):
            if api_key == "sk-bad-candidate":
                raise ValueError("401 unauthorized sk-bad-candidate")

        registry = ProviderRegistry(
            [
                ProviderSpec(
                    id="openai",
                    name="OpenAI",
                    category="LLM",
                    env_var="OPENAI_API_KEY",
                    description="test",
                    doc_url="https://example.com",
                    placeholder="sk-...",
                    probe=fake_probe,
                )
            ]
        )
        repo = ApiKeyRepository(self.db)
        svc = CredentialService(repo=repo, vault=self.vault, env_store=self.env_store, registry=registry)
        svc.save_user_key(self.u1.id, "openai", "sk-good-saved-key-9999")

        # Validate saved key -> VALID
        ok = asyncio.run(svc.probe_connection("openai", user_id=self.u1.id))
        self.assertTrue(ok["healthy"])

        # Test unsaved bad candidate -> must NOT overwrite saved key status!
        bad = asyncio.run(svc.probe_connection("openai", user_id=self.u1.id, candidate_key="sk-bad-candidate"))
        self.assertFalse(bad["healthy"])
        self.assertNotIn("sk-bad-candidate", bad["message"])

        rows = repo.list_status_by_user(self.u1.id)
        self.assertEqual(rows[0]["validation_status"], "VALID")

    def test_model_service_byok_activate_and_atomic_default_swap(self):
        model_repo = ModelRepository(self.db)
        key_repo = ApiKeyRepository(self.db)
        cred_svc = CredentialService(repo=key_repo, vault=self.vault, env_store=self.env_store)
        model_svc = ModelService(repo=model_repo, credential_service=cred_svc)

        m1 = model_svc.create_model(ModelCreateRequest(id="m-one", name="Model One", provider="openai"))
        m2 = model_svc.create_model(ModelCreateRequest(id="m-two", name="Model Two", provider="openai"))

        cred_svc.save_user_key(self.u1.id, "openai", "sk-user-byok-openai-key")
        model_svc.activate_model(m1["id"], user_id=self.u1.id)
        model_svc.activate_model(m2["id"], user_id=self.u1.id)

        model_svc.set_default(m1["id"])
        self.assertEqual(model_repo.get_default_active_id(), m1["id"])
        model_svc.set_default(m2["id"])
        self.assertEqual(model_repo.get_default_active_id(), m2["id"])
        self.assertEqual(model_repo.get_by_id(m1["id"])["is_default"], 0)

        self.assertIn("[REDACTED_API_KEY]", redact_secrets_from_text("err sk-1234567890123456789012345"))


class TestStorageAttachmentsPromptsRulesImport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = _init_temp_db(self.tmp.name)
        self.storage = LocalAttachmentStorage(base_dir=Path(self.tmp.name) / "uploads")
        self.user_repo = UserRepository(self.db)
        self.auth_svc = AuthService(self.user_repo)
        self.u1 = self.auth_svc.register(
            RegisterRequest(email="owner@example.com", password="Password123!", full_name="Owner")
        ).user
        self.u2 = self.auth_svc.register(
            RegisterRequest(email="other@example.com", password="Password123!", full_name="Other")
        ).user
        self.conv_repo = ConversationRepository(self.db)
        self.att_repo = AttachmentRepository(self.db)
        self.prompt_repo = PromptRepository(self.db)
        self.rule_repo = RuleRepository(self.db)
        self.att_svc = AttachmentService(self.att_repo, self.conv_repo, self.prompt_repo, storage=self.storage)
        self.prompt_svc = PromptService(self.prompt_repo, self.att_repo, storage=self.storage)
        self.rule_svc = RuleService(self.rule_repo)
        self.import_svc = TextImportService(self.rule_svc, self.prompt_svc)

    def tearDown(self):
        self.tmp.cleanup()

    def test_storage_blocks_executables_traversal_and_binary_docx_decode(self):
        with self.assertRaises(ValueError):
            FileSecurityValidator.classify(b"echo hi", "run.bat")
        with self.assertRaises(ValueError):
            FileSecurityValidator.classify(b"MZ\x90\x00fakepe", "safe.txt")
        with self.assertRaises(ValueError):
            self.storage.resolve_safe_path("../../etc/passwd")
        self.assertIsNone(TextExtractor.extract(b"PK\x03\x04binary", "document", "application/zip", "doc.docx"))

        hdr = build_content_disposition("attachment", "tài_liệu_日本語.txt")
        self.assertIn("filename*=UTF-8''", hdr)

    def test_rule_anti_idor_clone_and_atomic_occ(self):
        created = self.rule_svc.create(
            self.u1.id,
            RuleCreateRequest(name="Private Rule", content="Always explain particles clearly."),
        )
        with self.assertRaises(ForbiddenError):
            self.rule_svc.clone(created.id, self.u2.id)

        updated = self.rule_svc.update(
            created.id,
            self.u1.id,
            RuleUpdateRequest(name="Private Rule v2", content="Updated content", version=1),
        )
        self.assertEqual(updated.version, 2)

        with self.assertRaises(ConflictError):
            self.rule_svc.update(
                created.id,
                self.u1.id,
                RuleUpdateRequest(name="Stale Write", content="Old version", version=1),
            )

    def test_prompt_default_reset_and_text_import(self):
        p1 = self.prompt_svc.create_prompt(
            self.u1.id,
            PromptCreateRequest(name="Sensei One", content="Instruction one", is_default=True),
        )
        p2 = self.prompt_svc.create_prompt(
            self.u1.id,
            PromptCreateRequest(name="Sensei Two", content="Instruction two", is_default=False),
        )
        self.prompt_svc.update_prompt(
            p2.id,
            self.u1.id,
            PromptUpdateRequest(name="Sensei Two", content="Instruction two updated", is_default=True),
        )
        self.assertEqual(self.prompt_repo.get_owned(p1.id, self.u1.id)["is_default"], 0)
        self.assertEqual(self.prompt_repo.get_owned(p2.id, self.u1.id)["is_default"], 1)

        md = "---\nname: Imported Rule\nactivation_mode: always_on\npriority: 80\n---\nUse polite Japanese."
        res = self.import_svc.import_rule_from_text(self.u1.id, md)
        self.assertEqual(res["name"], "Imported Rule")
        always_on = self.rule_repo.list_active_always_on(self.u1.id)
        self.assertEqual(len(always_on), 1)


if __name__ == "__main__":
    unittest.main()
