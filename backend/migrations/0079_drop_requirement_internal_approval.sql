-- Migration 0079: drop the Requirement stage's internal scope-of-work
-- approval step.
--
-- The Requirement stage used to require TWO sign-offs before a project
-- could move to Quotation: a staff-only internal approval
-- (project.scope_status / scope_approved_at / scope_approved_by, added
-- in migration 0038) followed by the client's own email-OTP
-- confirmation (project.scope_client_confirmed_at, added in migration
-- 0067). Per product decision, the internal approval step is removed
-- entirely -- staff prepares the scope of work and the client's OTP
-- confirmation alone is now the outcome that gates the move to
-- Quotation (see project_service._assert_stage_exit_criteria/
-- send_requirement_otp/verify_requirement_otp).
--
-- This drops the now-unused scope_status/scope_approved_at/
-- scope_approved_by columns (and their FK) from `projects`.
-- scope_client_confirmed_at is untouched -- it's still the live gate.
--
-- Idempotent -- guarded by information_schema checks, same convention
-- as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0079_drop_requirement_internal_approval.sql

SET @fk_exists = (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'projects'
    AND CONSTRAINT_NAME = 'fk_projects_scope_approved_by'
);
SET @sql = IF(@fk_exists > 0,
  'ALTER TABLE projects DROP FOREIGN KEY fk_projects_scope_approved_by',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'projects' AND COLUMN_NAME = 'scope_approved_by'
);
SET @sql = IF(@col_exists > 0,
  'ALTER TABLE projects DROP COLUMN scope_approved_by',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'projects' AND COLUMN_NAME = 'scope_approved_at'
);
SET @sql = IF(@col_exists > 0,
  'ALTER TABLE projects DROP COLUMN scope_approved_at',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'projects' AND COLUMN_NAME = 'scope_status'
);
SET @sql = IF(@col_exists > 0,
  'ALTER TABLE projects DROP COLUMN scope_status',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0079 complete.' AS status;
