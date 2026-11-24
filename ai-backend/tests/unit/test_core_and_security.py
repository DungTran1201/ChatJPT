"""Unit tests for Core Infrastructure: DatabaseManager/UoW, Exceptions, Security (SEC-007), SecretVault."""

import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

from src.core.database import DatabaseManager
from src.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    QuotaExceededError,
)
from src.core.secret_vault import SecretVault
from src.core.security import (
    InMemoryRateLimiter,
    create_access_token,
    decode_access_token,
    hash_password,
    is_admin_user,
    is_token_revoked_by_password_change,
    verify_password,
)


class TestDatabaseManagerAndUoW(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "unit_core.db"
        self.db = DatabaseManager(db_path=self.db_path)
        self.db.execute_commit(
            "CREATE TABLE items (id TEXT PRIMARY KEY, name TEXT NOT NULL)"
        )
        self.db.execute_commit(
            "CREATE TABLE child_items (id TEXT PRIMARY KEY, item_id TEXT NOT NULL REFERENCES items(id))"
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_wal_and_foreign_keys_enforced(self):
        self.assertTrue(self.db.check_connection())
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute_commit(
                "INSERT INTO child_items (id, item_id) VALUES ('c1', 'missing_parent')"
            )

    def test_transaction_commit_and_rollback_atomicity(self):
        with self.db.transaction() as uow:
            uow.execute("INSERT INTO items (id, name) VALUES ('i1', 'committed')")
        row = self.db.query_one("SELECT * FROM items WHERE id = 'i1'")
        self.assertIsNotNone(row)
        self.assertEqual(row["name"], "committed")

        with self.assertRaises(RuntimeError):
            with self.db.transaction() as uow:
                uow.execute("INSERT INTO items (id, name) VALUES ('i2', 'should_rollback')")
                raise RuntimeError("boom")

        rolled_back = self.db.query_one("SELECT * FROM items WHERE id = 'i2'")
        self.assertIsNone(rolled_back)


class TestDomainExceptions(unittest.TestCase):
    def test_plain_vs_structured_detail(self):
        plain = NotFoundError("Không tìm thấy")
        self.assertEqual(plain.status_code, 404)
        self.assertEqual(plain.to_http_detail(), "Không tìm thấy")

        structured = ConflictError("Xung đột phiên bản", error_code="VERSION_CONFLICT", structured=True)
        self.assertEqual(structured.status_code, 409)
        self.assertEqual(
            structured.to_http_detail(),
            {"error_code": "VERSION_CONFLICT", "message": "Xung đột phiên bản"},
        )

        quota_err = QuotaExceededError(
            "Hết quota",
            error_code="DAILY_QUOTA_EXCEEDED",
            extra={"retry_after": 120},
            headers={"Retry-After": "120"},
            structured=True,
        )
        self.assertEqual(quota_err.status_code, 429)
        self.assertEqual(quota_err.headers.get("Retry-After"), "120")
        self.assertEqual(quota_err.to_http_detail()["retry_after"], 120)
        self.assertEqual(BadRequestError("x").status_code, 400)
        self.assertEqual(ForbiddenError("x").status_code, 403)


class TestSecurityAndSecretVault(unittest.TestCase):
    def test_password_hash_and_verify(self):
        pw = "Sup3rS3cur3!Pass"
        hashed = hash_password(pw)
        self.assertTrue(verify_password(pw, hashed))
        self.assertFalse(verify_password("wrong", hashed))

    def test_sec007_password_change_revokes_older_tokens(self):
        old_token = create_access_token("u1", "u1@example.com")
        payload = decode_access_token(old_token)
        self.assertIsNotNone(payload)

        future_pw_change = (datetime.now(timezone.utc) + timedelta(seconds=60)).strftime("%Y-%m-%d %H:%M:%S")
        past_pw_change = (datetime.now(timezone.utc) - timedelta(seconds=60)).strftime("%Y-%m-%d %H:%M:%S")

        self.assertTrue(is_token_revoked_by_password_change(payload, future_pw_change))
        self.assertFalse(is_token_revoked_by_password_change(payload, past_pw_change))
        self.assertFalse(is_token_revoked_by_password_change(payload, None))

    def test_is_admin_user_blocks_substring_spoofing(self):
        with patch("src.core.config.settings.ADMIN_EMAILS", "boss@chatjpt.local"):
            self.assertFalse(is_admin_user({"email": "fake_admin@evil.com"}))
            self.assertTrue(is_admin_user({"email": "BOSS@chatjpt.local"}))
            self.assertTrue(is_admin_user({"email": "user@example.com", "role": "admin"}))

    def test_rate_limiter_enforces_limit(self):
        limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60)
        limiter.check("client-a")
        limiter.check("client-a")
        with self.assertRaises(HTTPException) as ctx:
            limiter.check("client-a")
        self.assertEqual(ctx.exception.status_code, 429)
        limiter.check("client-b")  # isolated per key

    def test_secret_vault_roundtrip_and_tamper_rejection(self):
        vault = SecretVault(key_provider=lambda: "unit-test-master-secret-32-bytes!!")
        secret = "sk-test-1234567890abcdef"
        ct = vault.encrypt(secret)
        self.assertNotIn(secret, ct)
        self.assertEqual(vault.decrypt(ct), secret)
        self.assertEqual(vault.mask(secret), "sk-t...cdef")
        self.assertEqual(len(vault.fingerprint(secret)), 16)
        with self.assertRaises(ValueError):
            vault.decrypt(ct[:-4] + "AAAA")


if __name__ == "__main__":
    unittest.main()
