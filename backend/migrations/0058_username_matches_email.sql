-- Migration 0058: username mirrors email for every user except 'admin'.
--
-- New users (user_service.create_user) now get username = email
-- directly instead of a derived local-part-of-email slug -- simpler,
-- and it means logging in with your actual email address just works,
-- not just whatever slug got generated. Safe as the sole source of
-- uniqueness since email itself is already UNIQUE.
--
-- This migration:
--   1. Widens users.username from VARCHAR(50) to VARCHAR(120) to match
--      email (a 50-char cap would silently truncate/collide on longer
--      real email addresses).
--   2. Backfills every existing user's username to their email, except
--      the 'admin' bootstrap account (scripts/create_admin.py), which
--      is explicitly exempt and keeps its own username.
--
-- Idempotent -- guarded by information_schema checks / no-op re-runs,
-- same convention as every other migration in this directory.

SET @db := DATABASE();

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'users' AND column_name = 'username'
);
SET @sql := IF(@col_exists > 0,
    'ALTER TABLE users MODIFY COLUMN username VARCHAR(120) NOT NULL',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

UPDATE users
SET username = email
WHERE username <> 'admin'
  AND username <> email;

SELECT 'Migration 0058 complete.' AS status;
