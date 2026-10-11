-- ================================================================
-- USERS SERVICE DATABASE SCHEMA
-- Database: gdb_users_db
-- Purpose: Manage users, roles, and authentication
-- ================================================================

-- ================================================================
-- ENUM TYPES
-- ================================================================
CREATE TYPE user_role_enum AS ENUM ('MANAGER', 'TELLER', 'ADMIN');
CREATE TYPE audit_action_enum AS ENUM ('CREATE', 'UPDATE', 'ACTIVATE', 'INACTIVATE', 'REACTIVATE');

-- ================================================================
-- MAIN USERS TABLE
-- Core user table with role-based access control
-- ================================================================
CREATE TABLE users (
    user_id BIGSERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    login_id VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role user_role_enum NOT NULL DEFAULT 'MANAGER',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_users_login_id ON users(login_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Create unique index on login_id (case-sensitive)
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_login_id_unique ON users(login_id);

-- ================================================================
-- USER AUDIT LOG TABLE
-- Track all user management operations for compliance
-- ================================================================
CREATE TABLE user_audit_log (
    audit_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    action audit_action_enum NOT NULL,
    old_data JSONB,
    new_data JSONB,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Create indexes for audit queries
CREATE INDEX IF NOT EXISTS idx_audit_user_id ON user_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON user_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON user_audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_user_timestamp ON user_audit_log(user_id, timestamp);

-- ================================================================
-- FUNCTION TO UPDATE updated_at TIMESTAMP
-- Automatically updates the updated_at column on record modification
-- ================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for users table
CREATE TRIGGER users_update_timestamp BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ================================================================
-- CONSTRAINTS AND VALIDATION
-- ================================================================

-- Ensure login_id is not empty and properly formatted
ALTER TABLE users ADD CONSTRAINT check_login_id_length 
    CHECK (LENGTH(login_id) >= 3 AND LENGTH(login_id) <= 50);

-- Ensure username is not empty
ALTER TABLE users ADD CONSTRAINT check_username_length 
    CHECK (LENGTH(username) >= 1 AND LENGTH(username) <= 255);

-- Ensure password is not empty
ALTER TABLE users ADD CONSTRAINT check_password_hash_length 
    CHECK (LENGTH(password) > 0);

-- ================================================================
-- SAMPLE DATA (Optional - for testing)
-- ================================================================
-- Insert default admin user if needed
-- Password: admin@12345 (bcrypt hashed - replace with actual hash)
-- INSERT INTO users (username, login_id, password_hash, role, is_active)
-- VALUES ('Admin User', 'admin', '$2b$10$...', 'ADMIN', TRUE);

-- ================================================================
-- PERMISSIONS AND SECURITY
-- ================================================================
-- These should be applied based on your PostgreSQL setup

-- Example: Create application user with appropriate permissions
-- CREATE USER gdb_users_app WITH PASSWORD 'secure_password';
-- GRANT USAGE ON SCHEMA public TO gdb_users_app;
-- GRANT SELECT, INSERT, UPDATE ON users TO gdb_users_app;
-- GRANT SELECT, INSERT ON user_audit_log TO gdb_users_app;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO gdb_users_app;

-- ================================================================
-- VIEWS (Optional - for common queries)
-- ================================================================

-- View for active users only
CREATE VIEW active_users AS
SELECT user_id, username, login_id, role, created_at, updated_at
FROM users
WHERE is_active = TRUE;

-- View for user statistics by role
CREATE VIEW user_role_statistics AS
SELECT 
    role,
    COUNT(*) as total_users,
    COUNT(CASE WHEN is_active THEN 1 END) as active_users,
    COUNT(CASE WHEN NOT is_active THEN 1 END) as inactive_users
FROM users
GROUP BY role;

-- ================================================================
-- COMMENT DOCUMENTATION
-- ================================================================

COMMENT ON TABLE users IS 'Core user table storing user credentials, roles, and status';
COMMENT ON TABLE user_audit_log IS 'Audit log for tracking all user management operations';

COMMENT ON COLUMN users.user_id IS 'Unique user identifier (auto-generated)';
COMMENT ON COLUMN users.username IS 'User display name (1-255 characters)';
COMMENT ON COLUMN users.login_id IS 'Unique login identifier (3-50 chars, alphanumeric + . - _)';
COMMENT ON COLUMN users.password IS 'bcrypt hashed password (never plaintext)';
COMMENT ON COLUMN users.role IS 'User role: MANAGER, TELLER, or ADMIN (default: MANAGER)';
COMMENT ON COLUMN users.is_active IS 'User account status (TRUE=active, FALSE=inactive)';
COMMENT ON COLUMN users.created_at IS 'User account creation timestamp';
COMMENT ON COLUMN users.updated_at IS 'Last update timestamp (auto-updated)';

COMMENT ON COLUMN user_audit_log.audit_id IS 'Unique audit log entry identifier';
COMMENT ON COLUMN user_audit_log.user_id IS 'Reference to user (nullable if user deleted)';
COMMENT ON COLUMN user_audit_log.action IS 'Operation type: CREATE, UPDATE, ACTIVATE, INACTIVATE';
COMMENT ON COLUMN user_audit_log.old_data IS 'Previous data before change (JSONB format)';
COMMENT ON COLUMN user_audit_log.new_data IS 'New data after change (JSONB format)';
COMMENT ON COLUMN user_audit_log.timestamp IS 'When the operation was performed';

-- ================================================================
-- END OF USERS SERVICE DATABASE SCHEMA
-- ================================================================
