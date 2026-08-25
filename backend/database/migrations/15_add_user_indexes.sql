-- Migration: 15_add_user_indexes.sql
-- Purpose: Add indexes on user_id / conversation_id columns used in WHERE clauses
--          to prevent full table scans as data grows on Supabase free-tier.
-- Source: ANALYSIS-B Perf-Hunter report (high-impact perf finding)
-- Risk: LOW (CREATE INDEX IF NOT EXISTS is idempotent; can be run multiple times)
-- Rollback: DROP INDEX IF EXISTS <name>;

-- Conversations table
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations (user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations (updated_at DESC);

-- Messages table
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages (conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages (created_at);

-- Shared conversations
CREATE INDEX IF NOT EXISTS idx_shared_conversations_user_id ON shared_conversations (user_id);
CREATE INDEX IF NOT EXISTS idx_shared_conversations_conversation_id ON shared_conversations (conversation_id);

-- User API keys
CREATE INDEX IF NOT EXISTS idx_user_keys_user_id ON user_keys (user_id);

-- Voice interactions
CREATE INDEX IF NOT EXISTS idx_voice_interactions_user_id ON voice_interactions (user_id);

-- Artifacts
CREATE INDEX IF NOT EXISTS idx_artifacts_conversation_id ON artifacts (conversation_id);

-- Scheduled tasks
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_user_id ON scheduled_tasks (user_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_next_run ON scheduled_tasks (next_run_at);

-- Comment for migration log
COMMENT ON MIGRATION '15_add_user_indexes' IS 'Adds 10 indexes on user_id/conversation_id columns to prevent full table scans on Supabase free-tier. Idempotent via IF NOT EXISTS.';
