-- Database optimization indexes for Calgentic
-- These indexes will significantly improve query performance for millions of users

-- Index on user_email and created_at for user prompt history queries
CREATE INDEX IF NOT EXISTS idx_prompts_user_email_created_at 
ON prompts(user_email, created_at DESC);

-- Index on user_email and status for filtering by success/error
CREATE INDEX IF NOT EXISTS idx_prompts_user_email_status 
ON prompts(user_email, status);

-- Index on action_type for analytics and filtering
CREATE INDEX IF NOT EXISTS idx_prompts_action_type 
ON prompts(action_type);

-- Index on user_email and action_type for specific action queries
CREATE INDEX IF NOT EXISTS idx_prompts_user_email_action_type 
ON prompts(user_email, action_type);

-- Index on created_at for time-based queries and cleanup
CREATE INDEX IF NOT EXISTS idx_prompts_created_at 
ON prompts(created_at DESC);

-- Index on user_id for faster user lookups
CREATE INDEX IF NOT EXISTS idx_prompts_user_id 
ON prompts(user_id);

-- Composite index for event creation tracking
CREATE INDEX IF NOT EXISTS idx_prompts_event_created_user 
ON prompts(event_created, user_email, created_at DESC);

-- Index on users table for faster email lookups
CREATE INDEX IF NOT EXISTS idx_users_email 
ON users(email);

-- Index on users table for Google ID lookups
CREATE INDEX IF NOT EXISTS idx_users_google_id 
ON users(google_id);

-- Add comments for documentation
COMMENT ON INDEX idx_prompts_user_email_created_at IS 'Optimizes user prompt history queries';
COMMENT ON INDEX idx_prompts_user_email_status IS 'Optimizes filtering by prompt status';
COMMENT ON INDEX idx_prompts_action_type IS 'Optimizes action type analytics';
COMMENT ON INDEX idx_prompts_user_email_action_type IS 'Optimizes user-specific action queries';
COMMENT ON INDEX idx_prompts_created_at IS 'Optimizes time-based queries and cleanup';
COMMENT ON INDEX idx_prompts_user_id IS 'Optimizes user ID lookups';
COMMENT ON INDEX idx_prompts_event_created_user IS 'Optimizes event creation tracking';
COMMENT ON INDEX idx_users_email IS 'Optimizes user email lookups';
COMMENT ON INDEX idx_users_google_id IS 'Optimizes Google ID lookups';