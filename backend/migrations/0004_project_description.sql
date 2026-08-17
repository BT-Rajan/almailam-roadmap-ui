-- Migration 0004: project description
--
-- Adds a single nullable column to `projects` -- safe to add via
-- ALTER TABLE regardless of existing row count, no backfill needed.
--
-- Idempotent -- guarded by an information_schema check, same pattern as
-- earlier migrations.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0004_project_description.sql

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'projects' AND COLUMN_NAME = 'description'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE projects ADD COLUMN description VARCHAR(2000) NULL AFTER project_name',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0004 complete.' AS status;
