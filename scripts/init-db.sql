-- Hination Database Initialization Script
-- Runs on first PostgreSQL container start

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =======================
-- Users Table (Admin only)
-- =======================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'admin',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =======================
-- Sessions Table (Refresh Tokens)
-- =======================
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(255) NOT NULL,
    user_agent TEXT,
    ip_address INET,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =======================
-- Scoring Jobs Table
-- =======================
CREATE TABLE IF NOT EXISTS scoring_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(100) NOT NULL,
    job_type VARCHAR(50) NOT NULL DEFAULT 'grading',
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    input_data JSONB NOT NULL DEFAULT '{}',
    result_data JSONB,
    ai_response JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for scoring jobs
CREATE INDEX IF NOT EXISTS idx_scoring_jobs_status ON scoring_jobs(status);
CREATE INDEX IF NOT EXISTS idx_scoring_jobs_student_id ON scoring_jobs(student_id);
CREATE INDEX IF NOT EXISTS idx_scoring_jobs_created_at ON scoring_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scoring_jobs_status_created ON scoring_jobs(status, created_at DESC);

-- =======================
-- API Keys Table (Future - for additional API tokens)
-- =======================
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    scopes JSONB DEFAULT '["scoring:write"]',
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active);

-- =======================
-- Audit Log Table
-- =======================
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- =======================
-- Auto-update timestamps
-- =======================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =======================
-- Seed Admin User
-- =======================
-- Note: Password hash will be set via environment variables
-- This creates the admin if not exists
INSERT INTO users (username, password_hash, role)
VALUES (
    COALESCE(NULLIF(current_setting('app.admin_username', true), ''), 'admin'),
    COALESCE(NULLIF(current_setting('app.admin_password_hash', true), ''), '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.V4tLCshEu5Zi7K'),
    'admin'
) ON CONFLICT (username) DO NOTHING;
