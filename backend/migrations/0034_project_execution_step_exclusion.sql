-- Migration 0034: per-project exclusion for execution activities.
--
-- is_optional (template + project) is documentation-only ("doesn't
-- gate anything" per migration 0022) and is shared across every
-- project since it's copied from the template. Staff need to drop an
-- activity out of the Completed-stage gate and out of the %complete
-- calculation for ONE specific project (e.g. no false ceiling on this
-- job) without touching the template that every other project's
-- snapshot was copied from -- hence a new column on
-- project_execution_steps only, not on execution_step_templates.
--
-- Idempotent -- every ADD COLUMN is guarded by an information_schema
-- check, same pattern as earlier migrations (see 0026). Safe to
-- re-run, including against a database install.sh has already applied
-- this to.
--
-- Run:
--   mysql -u <user> -p <database> < backend/migrations/0034_project_execution_step_exclusion.sql

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_execution_steps' AND COLUMN_NAME = 'is_excluded'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_execution_steps ADD COLUMN is_excluded TINYINT(1) NOT NULL DEFAULT 0 AFTER is_optional',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_execution_steps' AND COLUMN_NAME = 'excluded_reason'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_execution_steps ADD COLUMN excluded_reason VARCHAR(200) NULL AFTER is_excluded',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0034 complete.' AS status;
