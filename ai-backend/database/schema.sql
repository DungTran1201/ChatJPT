-- ==============================================================================
-- DATABASE ARCHITECTURE SCHEMA: CHATJPT JAPANESE LEARNING PLATFORM
-- Target DBMS: SQLite 3 / ANSI SQL Compatible (PostgreSQL Ready)
-- ==============================================================================

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------------------------
-- 1. BẢNG NGƯỜI DÙNG (USERS)
-- Bounded Context: Identity & Authentication Context
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE COLLATE NOCASE,
    full_name VARCHAR(255),
    hashed_password VARCHAR(255),
    username VARCHAR(50) UNIQUE COLLATE NOCASE,
    avatar_url VARCHAR(500),
    bio VARCHAR(500),
    phone_number VARCHAR(20),
    discord_id VARCHAR(50) UNIQUE,
    discord_username VARCHAR(100),
    age INTEGER CHECK (age IS NULL OR (age >= 1 AND age <= 120)),
    occupation VARCHAR(100),
    interests VARCHAR(255),
    japanese_level VARCHAR(20) DEFAULT 'CHUA_HOC',
    learning_goal VARCHAR(255),
    custom_bg_url VARCHAR(1000),
    bg_opacity INTEGER DEFAULT 90 CHECK (bg_opacity >= 20 AND bg_opacity <= 100),
    bg_blur INTEGER DEFAULT 12 CHECK (bg_blur >= 0 AND bg_blur <= 40),
    bg_dim INTEGER DEFAULT 0 CHECK (bg_dim >= 0 AND bg_dim <= 100),
    accent_color VARCHAR(30) DEFAULT 'emerald',
    ui_font_size VARCHAR(10) DEFAULT 'medium' CHECK (ui_font_size IN ('small', 'medium', 'large')),
    theme_preference VARCHAR(10) NOT NULL DEFAULT 'DARK' CHECK (theme_preference IN ('DARK', 'LIGHT', 'SYSTEM')),
    language_preference VARCHAR(10) NOT NULL DEFAULT 'vi' CHECK (language_preference IN ('vi', 'en', 'ja')),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')),
    last_login_at TIMESTAMP,
    password_changed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

CREATE TRIGGER IF NOT EXISTS trg_users_updated_at
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;


-- ------------------------------------------------------------------------------
-- 2. BẢNG CUỘC TRÒ CHUYỆN (CONVERSATIONS)
-- Bounded Context: Conversation Context
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversations (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    title VARCHAR(255) NOT NULL DEFAULT 'Cuộc trò chuyện mới',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_updated ON conversations(user_id, updated_at DESC);

CREATE TRIGGER IF NOT EXISTS trg_conversations_updated_at
AFTER UPDATE ON conversations
FOR EACH ROW
BEGIN
    UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;


-- ------------------------------------------------------------------------------
-- 3. BẢNG TIN NHẮN ĐÀM THOẠI (MESSAGES)
-- Bounded Context: Chat Context
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    model_used VARCHAR(100),
    tokens_prompt INTEGER DEFAULT 0,
    tokens_completion INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_conv_created ON messages(conversation_id, created_at ASC);


-- ------------------------------------------------------------------------------
-- 4. BẢNG DANH MỤC MÔ HÌNH AI (MODELS)
-- Bounded Context: AI Infrastructure & Model Catalog Context
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS models (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    description TEXT,
    context_window INTEGER NOT NULL DEFAULT 8192,
    max_output_tokens INTEGER NOT NULL DEFAULT 4096,
    input_token_price NUMERIC(10, 6) DEFAULT 0.0,
    output_token_price NUMERIC(10, 6) DEFAULT 0.0,
    average_latency_ms NUMERIC(8, 2) DEFAULT 0.0,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'ARCHIVED')),
    is_default BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider);
CREATE INDEX IF NOT EXISTS idx_models_status ON models(status);


-- ------------------------------------------------------------------------------
-- 5. BẢNG NHẬT KÝ TELEMETRY & METRICS (API_METRIC_LOGS)
-- Bounded Context: Telemetry & Monitoring Context
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS api_metric_logs (
    id VARCHAR(36) PRIMARY KEY,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    latency_ms NUMERIC(10, 2) NOT NULL,
    user_id VARCHAR(36),
    model_id VARCHAR(100),
    tokens_prompt INTEGER DEFAULT 0,
    tokens_completion INTEGER DEFAULT 0,
    error_code VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_metric_logs_endpoint ON api_metric_logs(endpoint);
CREATE INDEX IF NOT EXISTS idx_metric_logs_created_at ON api_metric_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_metric_logs_user_id ON api_metric_logs(user_id);


-- ------------------------------------------------------------------------------
-- 6. BẢNG HẠN NGẠCH NGƯỜI DÙNG (USER_QUOTAS)
-- Bounded Context: Quota & Rate Limiting Context
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_quotas (
    user_id VARCHAR(36) PRIMARY KEY,
    daily_token_limit INTEGER NOT NULL DEFAULT 50000,
    daily_tokens_used INTEGER NOT NULL DEFAULT 0,
    reset_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


-- ------------------------------------------------------------------------------
-- 7. BẢNG CHỈ DẪN HỆ THỐNG / SENSEI PROMPTS (SYSTEM_PROMPTS)
-- Bounded Context: Pedagogical Prompt Context
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS system_prompts (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    content TEXT NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_system_prompts_user_id ON system_prompts(user_id);


-- ------------------------------------------------------------------------------
-- 8. BẢNG TỆP ĐÍNH KÈM (ATTACHMENTS)
-- Bounded Context: Attachment Context
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS attachments (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    message_id VARCHAR(36),
    conversation_id VARCHAR(36),
    filename VARCHAR(255) NOT NULL,
    stored_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'READY' CHECK (status IN ('READY', 'ATTACHED', 'DELETED')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_attachments_user_id ON attachments(user_id);
CREATE INDEX IF NOT EXISTS idx_attachments_message_id ON attachments(message_id);


-- ------------------------------------------------------------------------------
-- 9. BẢNG QUY TẮC HỌC TẬP / SENSEI RULES (RULES)
-- Bounded Context: Japanese Learning Rules Context
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rules (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    content TEXT NOT NULL,
    scope VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (scope IN ('system', 'user')),
    activation_mode VARCHAR(30) NOT NULL DEFAULT 'always_on' CHECK (activation_mode IN ('always_on', 'model_decision', 'glob', 'manual')),
    glob_patterns TEXT NOT NULL DEFAULT '[]',
    tags TEXT NOT NULL DEFAULT '[]',
    priority INTEGER NOT NULL DEFAULT 50 CHECK (priority >= 0 AND priority <= 100),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    version INTEGER NOT NULL DEFAULT 1,
    deleted_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rules_user_id ON rules(user_id);
CREATE INDEX IF NOT EXISTS idx_rules_status ON rules(status);


-- ------------------------------------------------------------------------------
-- 10. BẢNG API KEYS NGƯỜI DÙNG (USER_API_KEYS)
-- Bounded Context: Credential Vault & BYOK Context
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_api_keys (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    encrypted_key TEXT NOT NULL,
    key_hint VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, provider)
);

CREATE INDEX IF NOT EXISTS idx_user_api_keys_user_id ON user_api_keys(user_id);
