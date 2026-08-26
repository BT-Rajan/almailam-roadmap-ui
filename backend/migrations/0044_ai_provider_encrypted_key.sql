-- Migration 0044: Let an admin's API key entry actually work
--
-- Previously the Knowledgebase AI admin page's "Update Key" field never
-- sent a real key to the server at all (masked client-side before the
-- request), so ai_provider_configs.has_api_key/api_key_hint were always
-- display-only, and every real call still depended entirely on the
-- ANTHROPIC_API_KEY/DEEPSEEK_API_KEY server environment variables --
-- invisible to, and unreachable from, the admin UI. This adds a real,
-- encrypted-at-rest key column that the admin form now writes to and
-- app.services.ai_service reads from (preferring it over the environment
-- variables), so a key entered from the UI is live immediately, no SSH
-- or restart required.
--
-- Idempotent -- guarded by an information_schema check, same convention
-- as every other migration in this directory.

SET @db := DATABASE();

SET @exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'ai_provider_configs' AND column_name = 'api_key_encrypted'
);
SET @sql := IF(@exists = 0,
    'ALTER TABLE ai_provider_configs ADD COLUMN api_key_encrypted TEXT NULL AFTER model',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0044 complete.' AS status;
