-- ==============================================================================
-- BẢN NÂNG CẤP DỮ LIỆU: 021_message_status_and_timestamps.sql
-- Mô tả: Bổ sung các cột `status` và `updated_at` cho bảng `messages`, tạo index và trigger tự động cập nhật
-- Bounded Context: Chat Context & Message Lifecycle
-- Ràng buộc nghiệp vụ: FR-012, FR-013, STATE-002, BR-002
-- ==============================================================================

-- 1. MỞ RỘNG CỘT CHO BẢNG MESSAGES
-- Lưu ý SQLite: Chỉ chấp nhận hằng số làm DEFAULT trong ALTER TABLE ADD COLUMN
ALTER TABLE messages ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'COMPLETED';
ALTER TABLE messages ADD COLUMN updated_at TIMESTAMP;

-- 2. ĐỒNG BỘ DỮ LIỆU LỊCH SỬ (BACKFILL)
-- Gán updated_at cho các bản ghi bằng created_at để giữ tính toàn vẹn dữ liệu
UPDATE messages SET updated_at = created_at WHERE updated_at IS NULL;

-- 3. CHỈ MỤC TỐI ƯU TRUY VẤN
CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status);
CREATE INDEX IF NOT EXISTS idx_messages_updated_at ON messages(updated_at);

-- 4. TRIGGER TỰ ĐỘNG CẬP NHẬT THỜI GIAN KHI BẢN GHI ĐƯỢC CHÈN MỚI
CREATE TRIGGER IF NOT EXISTS trg_messages_insert_updated_at
AFTER INSERT ON messages
WHEN new.updated_at IS NULL
BEGIN
    UPDATE messages SET updated_at = new.created_at WHERE id = new.id;
END;

-- 5. TRIGGER TỰ ĐỘNG CẬP NHẬT THỜI GIAN KHI BẢN GHI ĐƯỢC CHỈNH SỬA
CREATE TRIGGER IF NOT EXISTS trg_messages_updated_at
AFTER UPDATE ON messages
FOR EACH ROW
BEGIN
    UPDATE messages SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;
