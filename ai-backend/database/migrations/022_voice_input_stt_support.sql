-- ==============================================================================
-- BẢN NÂNG CẤP DỮ LIỆU: 022_voice_input_stt_support.sql
-- Mô tả: Bổ sung trường hỗ trợ thu âm giọng nói, STT, Voice Binding và hoàn thiện User Profile
-- Bounded Context: Speech & Audio Context, Chat Context, User Personalization
-- Ràng buộc nghiệp vụ: FEAT-006, FR-016, FR-020, FR-069..FR-073, FR-079..FR-082
-- ==============================================================================

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------------------------
-- 1. BẢNG QUẢN LÝ GIỌNG NÓI VOICEVOX (VOICES)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS voices (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    character_name VARCHAR(100) NOT NULL,
    speaker_id INTEGER NOT NULL,
    style_name VARCHAR(50) DEFAULT 'Normal',
    gender VARCHAR(20) DEFAULT 'female' CHECK (gender IN ('female', 'male', 'other')),
    description TEXT,
    speed_scale REAL DEFAULT 1.0,
    pitch_scale REAL DEFAULT 0.0,
    intonation_scale REAL DEFAULT 1.0,
    volume_scale REAL DEFAULT 1.0,
    sample_text VARCHAR(255) DEFAULT 'こんにちは！日本語の勉強を一緒に頑張りましょう。',
    avatar_url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    is_system_preset BOOLEAN DEFAULT 0,
    user_id VARCHAR(36) DEFAULT 'system',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_voices_speaker_id ON voices(speaker_id);
CREATE INDEX IF NOT EXISTS idx_voices_status ON voices(status);

-- ------------------------------------------------------------------------------
-- 2. BỔ SUNG CỘT CHO BẢNG MESSAGES (Âm thanh người dùng & Voice Binding)
-- ------------------------------------------------------------------------------
ALTER TABLE messages ADD COLUMN audio_attachment_id VARCHAR(36) REFERENCES attachments(id) ON DELETE SET NULL;
ALTER TABLE messages ADD COLUMN audio_duration_ms INTEGER DEFAULT 0;
ALTER TABLE messages ADD COLUMN stt_language VARCHAR(10) DEFAULT 'auto';
ALTER TABLE messages ADD COLUMN stt_confidence REAL DEFAULT 1.0;
ALTER TABLE messages ADD COLUMN sensei_id VARCHAR(36) REFERENCES system_prompts(id) ON DELETE SET NULL;
ALTER TABLE messages ADD COLUMN voice_id VARCHAR(50) REFERENCES voices(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_messages_audio_att ON messages(audio_attachment_id);
CREATE INDEX IF NOT EXISTS idx_messages_sensei_id ON messages(sensei_id);
CREATE INDEX IF NOT EXISTS idx_messages_voice_id ON messages(voice_id);

-- ------------------------------------------------------------------------------
-- 3. BỔ SUNG CỘT CHO BẢNG ATTACHMENTS (Hỗ trợ lưu trữ đa phương tiện & OCR/STT)
-- ------------------------------------------------------------------------------
ALTER TABLE attachments ADD COLUMN storage_path VARCHAR(500);
ALTER TABLE attachments ADD COLUMN category VARCHAR(50) DEFAULT 'document';
ALTER TABLE attachments ADD COLUMN checksum_sha256 VARCHAR(64);
ALTER TABLE attachments ADD COLUMN prompt_id VARCHAR(36) REFERENCES system_prompts(id) ON DELETE CASCADE;
ALTER TABLE attachments ADD COLUMN extracted_text TEXT;
ALTER TABLE attachments ADD COLUMN image_width INTEGER;
ALTER TABLE attachments ADD COLUMN image_height INTEGER;

CREATE INDEX IF NOT EXISTS idx_attachments_category ON attachments(category);
CREATE INDEX IF NOT EXISTS idx_attachments_prompt_id ON attachments(prompt_id);

-- ------------------------------------------------------------------------------
-- 4. BỔ SUNG CỘT CHO BẢNG USERS (Hồ sơ cá nhân hóa học tập & Tùy biến giao diện)
-- ------------------------------------------------------------------------------
ALTER TABLE users ADD COLUMN age INTEGER CHECK (age IS NULL OR (age >= 1 AND age <= 120));
ALTER TABLE users ADD COLUMN occupation VARCHAR(100);
ALTER TABLE users ADD COLUMN interests VARCHAR(255);
ALTER TABLE users ADD COLUMN japanese_level VARCHAR(20) DEFAULT 'CHUA_HOC';
ALTER TABLE users ADD COLUMN learning_goal VARCHAR(255);
ALTER TABLE users ADD COLUMN custom_bg_url VARCHAR(1000);
ALTER TABLE users ADD COLUMN bg_opacity INTEGER DEFAULT 90 CHECK (bg_opacity >= 20 AND bg_opacity <= 100);
ALTER TABLE users ADD COLUMN bg_blur INTEGER DEFAULT 12 CHECK (bg_blur >= 0 AND bg_blur <= 40);
ALTER TABLE users ADD COLUMN bg_dim INTEGER DEFAULT 0 CHECK (bg_dim >= 0 AND bg_dim <= 100);
ALTER TABLE users ADD COLUMN accent_color VARCHAR(30) DEFAULT 'emerald';
ALTER TABLE users ADD COLUMN ui_font_size VARCHAR(10) DEFAULT 'medium' CHECK (ui_font_size IN ('small', 'medium', 'large'));

-- ------------------------------------------------------------------------------
-- 5. BỔ SUNG CỘT CHO BẢNG SYSTEM_PROMPTS (Liên kết giọng nói mặc định của Sensei)
-- ------------------------------------------------------------------------------
ALTER TABLE system_prompts ADD COLUMN voice_id VARCHAR(50) REFERENCES voices(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_system_prompts_voice_id ON system_prompts(voice_id);

-- ------------------------------------------------------------------------------
-- 6. KHỞI TẠO DANH MỤC 14 GIỌNG ĐỌC MẶC ĐỊNH CỦA VOICEVOX (SYSTEM PRESETS)
-- ------------------------------------------------------------------------------
INSERT OR REPLACE INTO voices (
    id, name, character_name, speaker_id, style_name, gender, description,
    speed_scale, pitch_scale, intonation_scale, volume_scale,
    sample_text, avatar_url, status, is_system_preset, user_id
) VALUES
('voice_kasukabe_tsumugi', 'Kasukabe Tsumugi (Normal)', '春日部つむぎ', 8, 'Normal', 'female', 'Giọng nữ tươi vui, trong sáng, phù hợp giao tiếp đời thường N5-N4.', 1.0, 0.0, 1.0, 1.0, 'こんにちは！一緒に日本語を勉強しましょう！', '/avatars/voices/tsumugi.png', 'ACTIVE', 1, 'system'),
('voice_shikoku_metan_normal', 'Shikoku Metan (Normal)', '四国めたん', 2, 'Normal', 'female', 'Giọng nữ thanh lịch, điềm tĩnh, chuẩn mực hội thoại N4-N3.', 1.0, 0.0, 1.0, 1.0, 'こんにちは、四国めたんです。よろしくお願いします。', '/avatars/voices/metan.png', 'ACTIVE', 1, 'system'),
('voice_shikoku_metan_sweet', 'Shikoku Metan (Sweet)', '四国めたん', 0, 'Sweet', 'female', 'Giọng nữ ngọt ngào, nhẹ nhàng, động viên học viên.', 1.0, 0.0, 1.0, 1.0, '一緒に頑張りましょうね！', '/avatars/voices/metan_sweet.png', 'ACTIVE', 1, 'system'),
('voice_shikoku_metan_tsun', 'Shikoku Metan (Tsuntsun)', '四国めたん', 6, 'Tsuntsun', 'female', 'Giọng nữ kiêu kỳ tsun-tsun, kích thích phản xạ Kaiwa.', 1.05, 0.02, 1.1, 1.0, 'べ、べつにあなたの勉強を手伝いたいわけじゃないんだからね！', '/avatars/voices/metan_tsun.png', 'ACTIVE', 1, 'system'),
('voice_shikoku_metan_sexy', 'Shikoku Metan (Sexy)', '四国めたん', 4, 'Sexy', 'female', 'Giọng nữ quyến rũ, truyền cảm, ngữ điệu chậm rãi.', 0.95, -0.02, 1.0, 1.0, 'ふふっ、次はどんな文法を学びたいのかしら？', '/avatars/voices/metan_sexy.png', 'ACTIVE', 1, 'system'),
('voice_zundamon_normal', 'Zundamon (Normal)', 'ずんだもん', 3, 'Normal', 'female', 'Giọng Zundamon lém lỉnh, hoạt bát, tràn đầy năng lượng.', 1.05, 0.05, 1.15, 1.0, 'ずんだもんなのだ！日本語の勉強を始めるのだ！', '/avatars/voices/zundamon.png', 'ACTIVE', 1, 'system'),
('voice_zundamon_sweet', 'Zundamon (Sweet)', 'ずんだもん', 1, 'Sweet', 'female', 'Giọng Zundamon nũng nịu, dễ thương.', 1.0, 0.04, 1.05, 1.0, 'えへへ、よく頑張ったのだ！褒めてあげるのだ！', '/avatars/voices/zundamon_sweet.png', 'ACTIVE', 1, 'system'),
('voice_zundamon_tsun', 'Zundamon (Tsuntsun)', 'ずんだもん', 7, 'Tsuntsun', 'female', 'Giọng Zundamon cá tính, thách thức.', 1.1, 0.03, 1.2, 1.0, 'まだそんな初歩的な単語を間違えているのだ？しっかりするのだ！', '/avatars/voices/zundamon_tsun.png', 'ACTIVE', 1, 'system'),
('voice_zundamon_sexy', 'Zundamon (Sexy)', 'ずんだもん', 5, 'Sexy', 'female', 'Giọng Zundamon phong cách hài hước người lớn.', 0.98, 0.0, 1.0, 1.0, 'たまには落ち着いて漢字の練習でもするのだ...', '/avatars/voices/zundamon_sexy.png', 'ACTIVE', 1, 'system'),
('voice_kyushu_sora_normal', 'Kyushu Sora (Normal)', '九州そら', 16, 'Normal', 'female', 'Giọng nữ chín chắn, giọng chuẩn phát thanh viên, phù hợp N2-N1.', 1.0, -0.02, 1.0, 1.0, '九州そらです。ビジネス日本語と敬語を一緒に身につけましょう。', '/avatars/voices/sora.png', 'ACTIVE', 1, 'system'),
('voice_aoyama_ryusei_normal', 'Aoyama Ryusei (Normal)', '青山龍星', 13, 'Normal', 'male', 'Giọng nam trầm ấm, lịch thiệp, phù hợp luyện phỏng vấn công sở.', 1.0, -0.05, 1.0, 1.0, 'こんにちは、青山龍星です。日本のビジネスマナーを解説します。', '/avatars/voices/ryusei.png', 'ACTIVE', 1, 'system'),
('voice_meimei_himari_normal', 'Meimei Himari (Normal)', '冥鳴ひまり', 14, 'Normal', 'female', 'Giọng nữ dễ thương, trong trẻo, phù hợp luyện Kaiwa du lịch.', 1.0, 0.02, 1.0, 1.0, '冥鳴ひまりだよ！日常会話を楽しもうね！', '/avatars/voices/himari.png', 'ACTIVE', 1, 'system'),
('voice_namine_ritsu_normal', 'Namine Ritsu (Normal)', '波音リツ', 9, 'Normal', 'female', 'Giọng nữ đĩnh đạc, rõ âm vị, tối ưu cho bài thi nghe Choukai.', 0.98, 0.0, 1.05, 1.0, '波音リツです。聴解問題のポイントを分かりやすく指導します。', '/avatars/voices/ritsu.png', 'ACTIVE', 1, 'system'),
('voice_goki_normal', 'Goki (Normal)', '後鬼', 27, 'Normal', 'female', 'Giọng nữ trung tính, điềm đạm, phù hợp đọc giải thích văn phạm sâu.', 0.95, -0.03, 0.95, 1.0, '後鬼である。日本語の奥深い文法構造を解き明かそう。', '/avatars/voices/goki.png', 'ACTIVE', 1, 'system');

