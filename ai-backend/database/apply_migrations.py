import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MIGRATIONS_DIR = BASE_DIR / "migrations"

def run_migration():
    for db_path in [BASE_DIR / "app.db", BASE_DIR.parent / "app.db", BASE_DIR / "test_app.db"]:
        if not db_path.exists():
            continue
        print(f"Applying migration to {db_path}...")
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA foreign_keys = ON;")
        cur = conn.cursor()
        
        # 1. Check & apply users table extensions (002)
        cols = [c[1] for c in cur.execute("PRAGMA table_info(users)").fetchall()]
        print(f"Current columns in users ({db_path.name}): {cols}")
        
        columns_to_add = [
            ("username", "VARCHAR(50)"),
            ("avatar_url", "VARCHAR(500)"),
            ("bio", "VARCHAR(500)"),
            ("phone_number", "VARCHAR(20)"),
            ("theme_preference", "VARCHAR(10) DEFAULT 'DARK'"),
            ("language_preference", "VARCHAR(10) DEFAULT 'vi'"),
            ("last_login_at", "TIMESTAMP"),
            ("password_changed_at", "TIMESTAMP"),
        ]
        
        for col_name, col_def in columns_to_add:
            if col_name not in cols:
                print(f"Adding column {col_name} to users...")
                cur.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        conn.commit()

        # 2. Apply 003_agent_model_management.sql
        migration_003_file = MIGRATIONS_DIR / "003_agent_model_management.sql"
        if migration_003_file.exists():
            print(f"Executing {migration_003_file.name} on {db_path.name}...")
            with open(migration_003_file, "r", encoding="utf-8") as f:
                cur.executescript(f.read())
            conn.commit()

        # 3. Apply 004_discord_oauth_support.sql if columns missing
        user_cols = [c[1] for c in cur.execute("PRAGMA table_info(users)").fetchall()]
        if "discord_id" not in user_cols:
            print(f"Adding discord_id and discord_username to users in {db_path.name}...")
            cur.execute("ALTER TABLE users ADD COLUMN discord_id VARCHAR(50)")
            cur.execute("ALTER TABLE users ADD COLUMN discord_username VARCHAR(100)")
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_discord_id ON users(discord_id)")
            conn.commit()

        # 4. Apply 005_resource_telemetry_and_quotas.sql
        migration_005_file = MIGRATIONS_DIR / "005_resource_telemetry_and_quotas.sql"
        if migration_005_file.exists():
            print(f"Executing {migration_005_file.name} on {db_path.name}...")
            with open(migration_005_file, "r", encoding="utf-8") as f:
                cur.executescript(f.read())
            conn.commit()

        # 5. Seed default quotas for existing users without quota records
        cur.execute("""
            INSERT OR IGNORE INTO user_quotas (user_id, daily_token_limit, daily_tokens_used, reset_at)
            SELECT id, 100000, 0, datetime('now', '+1 day', 'start of day')
            FROM users
            WHERE id NOT IN (SELECT user_id FROM user_quotas)
        """)
        conn.commit()

        # 6. Apply 006_model_archival_and_catalog_extensions.sql (if status constraint does not yet include ARCHIVED)
        models_sql_row = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='models'").fetchone()
        if models_sql_row and "ARCHIVED" not in models_sql_row[0]:
            migration_006_file = MIGRATIONS_DIR / "006_model_archival_and_catalog_extensions.sql"
            if migration_006_file.exists():
                print(f"Executing {migration_006_file.name} on {db_path.name}...")
                with open(migration_006_file, "r", encoding="utf-8") as f:
                    cur.executescript(f.read())
                conn.commit()
                print(f"Applied 006 migration successfully to {db_path.name}.")

        # 7. Apply 007_discord_bot_management.sql
        migration_007_file = MIGRATIONS_DIR / "007_discord_bot_management.sql"
        if migration_007_file.exists():
            print(f"Executing {migration_007_file.name} on {db_path.name}...")
            with open(migration_007_file, "r", encoding="utf-8") as f:
                cur.executescript(f.read())
            conn.commit()
            print(f"Applied 007 migration successfully to {db_path.name}.")

        # 8. Check and add source column to messages table (FR-047)
        msg_cols = [c[1] for c in cur.execute("PRAGMA table_info(messages)").fetchall()]
        if "source" not in msg_cols:
            print(f"Adding source column to messages in {db_path.name}...")
            cur.execute("ALTER TABLE messages ADD COLUMN source VARCHAR(20) DEFAULT 'WEB'")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_source ON messages(source)")
            conn.commit()

        # 9. Apply 008_project_management.sql (Projects table & conversations.project_id)
        migration_008_file = MIGRATIONS_DIR / "008_project_management.sql"
        if migration_008_file.exists():
            print(f"Executing {migration_008_file.name} on {db_path.name}...")
            with open(migration_008_file, "r", encoding="utf-8") as f:
                cur.executescript(f.read())
            conn.commit()
            print(f"Applied 008 migration successfully to {db_path.name}.")

        conv_cols = [c[1] for c in cur.execute("PRAGMA table_info(conversations)").fetchall()]
        if "project_id" not in conv_cols:
            print(f"Adding project_id column to conversations in {db_path.name}...")
            cur.execute("ALTER TABLE conversations ADD COLUMN project_id VARCHAR(36) REFERENCES projects(id) ON DELETE SET NULL")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_conversations_project_id ON conversations(project_id)")
            conn.commit()

        # 10. Apply 009_system_prompt_management.sql (system_prompts table)
        migration_009_file = MIGRATIONS_DIR / "009_system_prompt_management.sql"
        if migration_009_file.exists():
            print(f"Executing {migration_009_file.name} on {db_path.name}...")
            with open(migration_009_file, "r", encoding="utf-8") as f:
                cur.executescript(f.read())
            conn.commit()
            print(f"Applied 009 migration successfully to {db_path.name}.")

        # Seed default sample system prompts for guest_user if table is empty for guest
        prompt_count = cur.execute("SELECT COUNT(*) FROM system_prompts WHERE user_id = 'guest_user'").fetchone()[0]
        if prompt_count == 0:
            print(f"Seeding default system prompts for guest_user in {db_path.name}...")
            cur.execute("""
                INSERT OR IGNORE INTO system_prompts (id, user_id, name, description, content)
                VALUES
                (
                    'sp_seed_python_expert',
                    'guest_user',
                    'Chuyên Gia Python & Kiến Trúc Phần Mềm',
                    'Hỗ trợ viết mã nguồn Python tối ưu, tuân thủ PEP 8, Type Hinting và Clean Architecture',
                    'Bạn là chuyên gia Senior Python Architect với hơn 10 năm kinh nghiệm. Khi viết code, hãy luôn tuân thủ các nguyên tắc sau:\n1. Luôn sử dụng Type Hinting đầy đủ cho tham số và kiểu trả về.\n2. Viết docstring theo chuẩn Google hoặc Sphinx.\n3. Ưu tiên giải pháp tối ưu thời gian O(n) và không gian O(n).\n4. Đưa ra giải thích súc tích, tập trung vào bản chất kỹ thuật.'
                ),
                (
                    'sp_seed_business_analyst',
                    'guest_user',
                    'Senior Business Analyst (IT)',
                    'Hỗ trợ khảo sát, bóc tách yêu cầu, viết User Stories và phân tích nghiệp vụ',
                    'Bạn là Senior Business Analyst chuyên nghiệp. Khi tiếp nhận yêu cầu từ người dùng:\n1. Phân loại rõ: FACT, ASSUMPTION, DECISION, OPEN QUESTION.\n2. Xác định Actor, Preconditions, Postconditions và Acceptance Criteria kiểm thử được.\n3. Không tự tiện suy diễn yêu cầu nếu chưa có bằng chứng xác thực.'
                )
            """)
            conn.commit()

        # 11. Apply 010_agent_skills_management.sql (skills & skill_files tables)
        migration_010_file = MIGRATIONS_DIR / "010_agent_skills_management.sql"
        if migration_010_file.exists():
            print(f"Executing {migration_010_file.name} on {db_path.name}...")
            with open(migration_010_file, "r", encoding="utf-8") as f:
                cur.executescript(f.read())
            conn.commit()
            print(f"Applied 010 migration successfully to {db_path.name}.")

        # 12. Apply 014_sunset_development_orchestrator.sql (Sunset and Decommission Orchestrator/Workspaces)
        migration_014_file = MIGRATIONS_DIR / "014_sunset_development_orchestrator.sql"
        if migration_014_file.exists():
            print(f"Executing {migration_014_file.name} on {db_path.name}...")
            with open(migration_014_file, "r", encoding="utf-8") as f:
                cur.executescript(f.read())
            conn.commit()
            print(f"Applied 014 sunset migration successfully to {db_path.name}.")

        # Clean up unreferenced workspace_id column from projects if still present
        if "projects" in [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
            prj_cols = [c[1] for c in cur.execute("PRAGMA table_info(projects)").fetchall()]
            if "workspace_id" in prj_cols:
                print(f"Dropping unreferenced workspace_id column from projects in {db_path.name}...")
                cur.execute("ALTER TABLE projects DROP COLUMN workspace_id")
                conn.commit()

        # 13. Apply 015_unified_file_upload_system.sql (Attachments and Assets)
        # If attachments table already exists, ensure skill_id and prompt_id columns are added first
        if "attachments" in [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
            att_cols = [c[1] for c in cur.execute("PRAGMA table_info(attachments)").fetchall()]
            if "skill_id" not in att_cols:
                print(f"Adding skill_id column to attachments in {db_path.name}...")
                cur.execute("ALTER TABLE attachments ADD COLUMN skill_id VARCHAR(36) REFERENCES skills(id) ON DELETE CASCADE")
                conn.commit()
            if "prompt_id" not in att_cols:
                print(f"Adding prompt_id column to attachments in {db_path.name}...")
                cur.execute("ALTER TABLE attachments ADD COLUMN prompt_id VARCHAR(36) REFERENCES system_prompts(id) ON DELETE CASCADE")
                conn.commit()

        migration_015_file = MIGRATIONS_DIR / "015_unified_file_upload_system.sql"
        if migration_015_file.exists():
            print(f"Executing {migration_015_file.name} on {db_path.name}...")
            with open(migration_015_file, "r", encoding="utf-8") as f:
                cur.executescript(f.read())
            conn.commit()
            print(f"Applied 015 migration successfully to {db_path.name}.")

        # 14. Apply 016_tool_management_system.sql (Tools, Tool Configurations, Bindings, Executions)
        migration_016_file = MIGRATIONS_DIR / "016_tool_management_system.sql"
        if migration_016_file.exists():
            print(f"Executing {migration_016_file.name} on {db_path.name}...")
            with open(migration_016_file, "r", encoding="utf-8") as f:
                cur.executescript(f.read())
            conn.commit()
            print(f"Applied 016 migration successfully to {db_path.name}.")

        # 15. Apply 017_rules_management_system.sql (Rules, Activation Metadata, Project Bindings)
        migration_017_file = MIGRATIONS_DIR / "017_rules_management_system.sql"
        if migration_017_file.exists():
            print(f"Executing {migration_017_file.name} on {db_path.name}...")
            with open(migration_017_file, "r", encoding="utf-8") as f:
                cur.executescript(f.read())
            conn.commit()
            print(f"Applied 017 migration successfully to {db_path.name}.")

        # 16. Apply 018_multi_discord_bot_management.sql (Multi-Bot Registry, Encrypted Tokens, Project Binding)
        migration_018_file = MIGRATIONS_DIR / "018_multi_discord_bot_management.sql"
        if migration_018_file.exists():
            print(f"Executing {migration_018_file.name} on {db_path.name}...")
            with open(migration_018_file, "r", encoding="utf-8") as f:
                cur.executescript(f.read())
            conn.commit()
            print(f"Applied 018 migration successfully to {db_path.name}.")

        # 17. Apply 019_user_api_keys_management.sql (User Personal API Keys Vault)
        migration_019_file = MIGRATIONS_DIR / "019_user_api_keys_management.sql"
        if migration_019_file.exists():
            print(f"Executing {migration_019_file.name} on {db_path.name}...")
            with open(migration_019_file, "r", encoding="utf-8") as f:
                cur.executescript(f.read())
            conn.commit()
            print(f"Applied 019 migration successfully to {db_path.name}.")

        # 18. Apply 020_external_skills_catalog_provenance.sql (External Skills Catalog Provenance)
        skill_cols = [c[1] for c in cur.execute("PRAGMA table_info(skills)").fetchall()]
        skill_columns_to_add = [
            ("source_provider", "VARCHAR(50)"),
            ("source_repository_url", "VARCHAR(500)"),
            ("source_skill_id", "VARCHAR(100)"),
            ("source_path", "VARCHAR(500)"),
            ("source_version", "VARCHAR(100)"),
            ("source_content_hash", "VARCHAR(64)"),
            ("source_license", "VARCHAR(100)"),
            ("attribution", "VARCHAR(500)"),
            ("imported_at", "TIMESTAMP"),
            ("source_updated_at", "TIMESTAMP"),
            ("source_status", "VARCHAR(50) DEFAULT 'current'"),
        ]
        for col_name, col_def in skill_columns_to_add:
            if col_name not in skill_cols:
                print(f"Adding column {col_name} to skills in {db_path.name}...")
                cur.execute(f"ALTER TABLE skills ADD COLUMN {col_name} {col_def}")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_skills_source_skill_id ON skills(user_id, source_provider, source_skill_id)")
        conn.commit()
        print(f"Applied 020 migration successfully to {db_path.name}.")

        # 19. Apply 021_message_status_and_timestamps.sql (Message status & updated_at)
        msg_cols = [c[1] for c in cur.execute("PRAGMA table_info(messages)").fetchall()]
        if "status" not in msg_cols:
            print(f"Adding status column to messages in {db_path.name}...")
            cur.execute("ALTER TABLE messages ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'COMPLETED'")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status)")
        if "updated_at" not in msg_cols:
            print(f"Adding updated_at column to messages in {db_path.name}...")
            cur.execute("ALTER TABLE messages ADD COLUMN updated_at TIMESTAMP")
            cur.execute("UPDATE messages SET updated_at = created_at WHERE updated_at IS NULL")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_updated_at ON messages(updated_at)")
        cur.execute("""
            CREATE TRIGGER IF NOT EXISTS trg_messages_insert_updated_at
            AFTER INSERT ON messages
            WHEN new.updated_at IS NULL
            BEGIN
                UPDATE messages SET updated_at = new.created_at WHERE id = new.id;
            END;
        """)
        cur.execute("""
            CREATE TRIGGER IF NOT EXISTS trg_messages_updated_at
            AFTER UPDATE ON messages
            FOR EACH ROW
            BEGIN
                UPDATE messages SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;
        """)
        conn.commit()
        print(f"Applied 021 migration successfully to {db_path.name}.")

        # 20. Apply 022_voice_input_stt_support.sql (Voices, audio messages, attachments, user profile extensions)
        print(f"Applying 022 extensions to {db_path.name}...")
        
        # 20.1 Ensure voices table exists
        cur.execute("""
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
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_voices_speaker_id ON voices(speaker_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_voices_status ON voices(status)")

        # Seed 14 official VoiceVox preset voices if table has no system presets
        voice_preset_count = cur.execute("SELECT COUNT(*) FROM voices WHERE is_system_preset = 1").fetchone()[0]
        if voice_preset_count < 14:
            print(f"Seeding official VoiceVox preset voices in {db_path.name}...")
            voice_presets = [
                ("voice_kasukabe_tsumugi", "Kasukabe Tsumugi (Normal)", "春日部つむぎ", 8, "Normal", "female", "Giọng nữ tươi vui, trong sáng, phù hợp giao tiếp đời thường N5-N4.", 1.0, 0.0, 1.0, 1.0, "こんにちは！一緒に日本語を勉強しましょう！", "/avatars/voices/tsumugi.png", "ACTIVE", 1, "system"),
                ("voice_shikoku_metan_normal", "Shikoku Metan (Normal)", "四国めたん", 2, "Normal", "female", "Giọng nữ thanh lịch, điềm tĩnh, chuẩn mực hội thoại N4-N3.", 1.0, 0.0, 1.0, 1.0, "こんにちは、四国めたんです。よろしくお願いします。", "/avatars/voices/metan.png", "ACTIVE", 1, "system"),
                ("voice_shikoku_metan_sweet", "Shikoku Metan (Sweet)", "四国めたん", 0, "Sweet", "female", "Giọng nữ ngọt ngào, nhẹ nhàng, động viên học viên.", 1.0, 0.0, 1.0, 1.0, "一緒に頑張りましょうね！", "/avatars/voices/metan_sweet.png", "ACTIVE", 1, "system"),
                ("voice_shikoku_metan_tsun", "Shikoku Metan (Tsuntsun)", "四国めたん", 6, "Tsuntsun", "female", "Giọng nữ kiêu kỳ tsun-tsun, kích thích phản xạ Kaiwa.", 1.05, 0.02, 1.1, 1.0, "べ、べつにあなたの勉強を手伝いたいわけじゃないんだからね！", "/avatars/voices/metan_tsun.png", "ACTIVE", 1, "system"),
                ("voice_shikoku_metan_sexy", "Shikoku Metan (Sexy)", "四国めたん", 4, "Sexy", "female", "Giọng nữ quyến rũ, truyền cảm, ngữ điệu chậm rãi.", 0.95, -0.02, 1.0, 1.0, "ふふっ、次はどんな文法を学びたいのかしら？", "/avatars/voices/metan_sexy.png", "ACTIVE", 1, "system"),
                ("voice_zundamon_normal", "Zundamon (Normal)", "ずんだもん", 3, "Normal", "female", "Giọng Zundamon lém lỉnh, hoạt bát, tràn đầy năng lượng.", 1.05, 0.05, 1.15, 1.0, "ずんだもんなのだ！日本語の勉強を始めるのだ！", "/avatars/voices/zundamon.png", "ACTIVE", 1, "system"),
                ("voice_zundamon_sweet", "Zundamon (Sweet)", "ずんだもん", 1, "Sweet", "female", "Giọng Zundamon nũng nịu, dễ thương.", 1.0, 0.04, 1.05, 1.0, "えへへ、よく頑張ったのだ！褒めてあげるのだ！", "/avatars/voices/zundamon_sweet.png", "ACTIVE", 1, "system"),
                ("voice_zundamon_tsun", "Zundamon (Tsuntsun)", "ずんだもん", 7, "Tsuntsun", "female", "Giọng Zundamon cá tính, thách thức.", 1.1, 0.03, 1.2, 1.0, "まだそんな初歩的な単語を間違えているのだ？しっかりするのだ！", "/avatars/voices/zundamon_tsun.png", "ACTIVE", 1, "system"),
                ("voice_zundamon_sexy", "Zundamon (Sexy)", "ずんだもん", 5, "Sexy", "female", "Giọng Zundamon phong cách hài hước người lớn.", 0.98, 0.0, 1.0, 1.0, "たまには落ち着いて漢字の練習でもするのだ...", "/avatars/voices/zundamon_sexy.png", "ACTIVE", 1, "system"),
                ("voice_kyushu_sora_normal", "Kyushu Sora (Normal)", "九州そら", 16, "Normal", "female", "Giọng nữ chín chắn, giọng chuẩn phát thanh viên, phù hợp N2-N1.", 1.0, -0.02, 1.0, 1.0, "九州そらです。ビジネス日本語と敬語を一緒に身につけましょう。", "/avatars/voices/sora.png", "ACTIVE", 1, "system"),
                ("voice_aoyama_ryusei_normal", "Aoyama Ryusei (Normal)", "青山龍星", 13, "Normal", "male", "Giọng nam trầm ấm, lịch thiệp, phù hợp luyện phỏng vấn công sở.", 1.0, -0.05, 1.0, 1.0, "こんにちは、青山龍星です。日本のビジネスマナーを解説します。", "/avatars/voices/ryusei.png", "ACTIVE", 1, "system"),
                ("voice_meimei_himari_normal", "Meimei Himari (Normal)", "冥鳴ひまり", 14, "Normal", "female", "Giọng nữ dễ thương, trong trẻo, phù hợp luyện Kaiwa du lịch.", 1.0, 0.02, 1.0, 1.0, "冥鳴ひまりだよ！日常会話を楽しもうね！", "/avatars/voices/himari.png", "ACTIVE", 1, "system"),
                ("voice_namine_ritsu_normal", "Namine Ritsu (Normal)", "波音リツ", 9, "Normal", "female", "Giọng nữ đĩnh đạc, rõ âm vị, tối ưu cho bài thi nghe Choukai.", 0.98, 0.0, 1.05, 1.0, "波音リツです。聴解問題のポイントを分かりやすく指導します。", "/avatars/voices/ritsu.png", "ACTIVE", 1, "system"),
                ("voice_goki_normal", "Goki (Normal)", "後鬼", 27, "Normal", "female", "Giọng nữ trung tính, điềm đạm, phù hợp đọc giải thích văn phạm sâu.", 0.95, -0.03, 0.95, 1.0, "後鬼である。日本語の奥深い文法構造を解き明かそう。", "/avatars/voices/goki.png", "ACTIVE", 1, "system")
            ]
            for vp in voice_presets:
                cur.execute("""
                    INSERT OR REPLACE INTO voices (
                        id, name, character_name, speaker_id, style_name, gender, description,
                        speed_scale, pitch_scale, intonation_scale, volume_scale,
                        sample_text, avatar_url, status, is_system_preset, user_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, vp)
            conn.commit()
            print(f"Seeded {len(voice_presets)} official VoiceVox presets successfully to {db_path.name}.")

        # 20.2 Messages table voice & STT extensions
        msg_cols = [c[1] for c in cur.execute("PRAGMA table_info(messages)").fetchall()]
        msg_extensions = [
            ("audio_attachment_id", "VARCHAR(36) REFERENCES attachments(id) ON DELETE SET NULL"),
            ("audio_duration_ms", "INTEGER DEFAULT 0"),
            ("stt_language", "VARCHAR(10) DEFAULT 'auto'"),
            ("stt_confidence", "REAL DEFAULT 1.0"),
            ("sensei_id", "VARCHAR(36) REFERENCES system_prompts(id) ON DELETE SET NULL"),
            ("voice_id", "VARCHAR(50) REFERENCES voices(id) ON DELETE SET NULL"),
        ]
        for col_name, col_def in msg_extensions:
            if col_name not in msg_cols:
                print(f"Adding column {col_name} to messages in {db_path.name}...")
                cur.execute(f"ALTER TABLE messages ADD COLUMN {col_name} {col_def}")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_audio_att ON messages(audio_attachment_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_sensei_id ON messages(sensei_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_voice_id ON messages(voice_id)")

        # 20.3 Attachments table storage & metadata extensions
        att_cols = [c[1] for c in cur.execute("PRAGMA table_info(attachments)").fetchall()]
        att_extensions = [
            ("storage_path", "VARCHAR(500)"),
            ("category", "VARCHAR(50) DEFAULT 'document'"),
            ("checksum_sha256", "VARCHAR(64)"),
            ("prompt_id", "VARCHAR(36) REFERENCES system_prompts(id) ON DELETE CASCADE"),
            ("extracted_text", "TEXT"),
            ("image_width", "INTEGER"),
            ("image_height", "INTEGER"),
        ]
        for col_name, col_def in att_extensions:
            if col_name not in att_cols:
                print(f"Adding column {col_name} to attachments in {db_path.name}...")
                cur.execute(f"ALTER TABLE attachments ADD COLUMN {col_name} {col_def}")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_attachments_category ON attachments(category)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_attachments_prompt_id ON attachments(prompt_id)")

        # 20.4 Users table profile personalization extensions
        user_cols = [c[1] for c in cur.execute("PRAGMA table_info(users)").fetchall()]
        user_profile_extensions = [
            ("age", "INTEGER CHECK (age IS NULL OR (age >= 1 AND age <= 120))"),
            ("occupation", "VARCHAR(100)"),
            ("interests", "VARCHAR(255)"),
            ("japanese_level", "VARCHAR(20) DEFAULT 'CHUA_HOC'"),
            ("learning_goal", "VARCHAR(255)"),
            ("custom_bg_url", "VARCHAR(1000)"),
            ("bg_opacity", "INTEGER DEFAULT 90 CHECK (bg_opacity >= 20 AND bg_opacity <= 100)"),
            ("bg_blur", "INTEGER DEFAULT 12 CHECK (bg_blur >= 0 AND bg_blur <= 40)"),
            ("bg_dim", "INTEGER DEFAULT 0 CHECK (bg_dim >= 0 AND bg_dim <= 100)"),
            ("accent_color", "VARCHAR(30) DEFAULT 'emerald'"),
            ("ui_font_size", "VARCHAR(10) DEFAULT 'medium' CHECK (ui_font_size IN ('small', 'medium', 'large'))"),
        ]
        for col_name, col_def in user_profile_extensions:
            if col_name not in user_cols:
                print(f"Adding column {col_name} to users in {db_path.name}...")
                cur.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")

        # 20.5 System prompts voice binding extension
        sp_cols = [c[1] for c in cur.execute("PRAGMA table_info(system_prompts)").fetchall()]
        if "voice_id" not in sp_cols:
            print(f"Adding column voice_id to system_prompts in {db_path.name}...")
            cur.execute("ALTER TABLE system_prompts ADD COLUMN voice_id VARCHAR(50) REFERENCES voices(id) ON DELETE SET NULL")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_system_prompts_voice_id ON system_prompts(voice_id)")

        conn.commit()
        print(f"Applied 022 migration successfully to {db_path.name}.")

        # Verify active tables
        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print(f"Tables in {db_path.name}: {tables}")
        if "user_api_keys" in tables:
            keys_count = cur.execute("SELECT COUNT(*) FROM user_api_keys").fetchone()[0]
            print(f"Total user API keys in {db_path.name}: {keys_count}")
        if "api_metric_logs" in tables and "user_quotas" in tables:
            quota_count = cur.execute("SELECT COUNT(*) FROM user_quotas").fetchone()[0]
            print(f"Total user quotas in {db_path.name}: {quota_count}")
        if "discord_bot_configs" in tables:
            bot_cfg_count = cur.execute("SELECT COUNT(*) FROM discord_bot_configs").fetchone()[0]
            print(f"Total discord bot configs in {db_path.name}: {bot_cfg_count}")
        if "projects" in tables:
            project_count = cur.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
            print(f"Total projects in {db_path.name}: {project_count}")
        if "system_prompts" in tables:
            sp_count = cur.execute("SELECT COUNT(*) FROM system_prompts").fetchone()[0]
            print(f"Total system prompts in {db_path.name}: {sp_count}")
        if "skills" in tables:
            skill_count = cur.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
            print(f"Total skills in {db_path.name}: {skill_count}")
        if "rules" in tables:
            rule_count = cur.execute("SELECT COUNT(*) FROM rules").fetchone()[0]
            print(f"Total rules in {db_path.name}: {rule_count}")
        if "project_rules" in tables:
            pr_count = cur.execute("SELECT COUNT(*) FROM project_rules").fetchone()[0]
            print(f"Total project rules bindings in {db_path.name}: {pr_count}")
            
        conn.close()

if __name__ == "__main__":
    run_migration()



