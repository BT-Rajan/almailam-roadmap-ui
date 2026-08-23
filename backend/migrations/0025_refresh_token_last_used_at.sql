-- Migration 0025: refresh_tokens.last_used_at -- server-side backstop for
-- the 30-minute idle logout (see auth_service.refresh() and the frontend's
-- useIdleLogout.ts). A refresh token minted long enough ago, with no
-- activity in between to redeem it sooner, is now rejected as an
-- abandoned session even if it hasn't technically expired yet.
--
-- Idempotent -- guarded by an information_schema check, same convention
-- as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0025_refresh_token_last_used_at.sql

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'refresh_tokens' AND COLUMN_NAME = 'last_used_at'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE refresh_tokens ADD COLUMN last_used_at DATETIME NULL AFTER created_at',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Backfill existing rows (any live sessions issued before this migration)
-- so the NOT NULL below doesn't fail -- created_at is the best available
-- stand-in for "last activity" on rows that predate this column.
UPDATE refresh_tokens SET last_used_at = created_at WHERE last_used_at IS NULL;

SET @col_nullable = (
  SELECT IS_NULLABLE FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'refresh_tokens' AND COLUMN_NAME = 'last_used_at'
);
SET @sql = IF(@col_nullable = 'YES',
  'ALTER TABLE refresh_tokens MODIFY COLUMN last_used_at DATETIME NOT NULL',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0025 complete.' AS status;
