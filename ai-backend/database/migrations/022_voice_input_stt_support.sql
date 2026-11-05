-- ==============================================================================
-- MIGRATION: 022_voice_input_stt_support.sql
-- Mô tả: Bổ sung trường hỗ trợ thu âm giọng nói và STT (FEAT-006, FR-079..FR-082)
-- ==============================================================================

PRAGMA foreign_keys = ON;

-- 1. Bổ sung các cột cho bảng attachments nếu chưa có
-- (Lưu ý: SQLite hỗ trợ ALTER TABLE ADD COLUMN từng cột)
-- storage_path, category, checksum_sha256, prompt_id, extracted_text, image_width, image_height

-- 2. Bổ sung các cột cho bảng messages để lưu thông tin âm thanh người dùng
-- audio_attachment_id, audio_duration_ms, stt_language, stt_confidence

