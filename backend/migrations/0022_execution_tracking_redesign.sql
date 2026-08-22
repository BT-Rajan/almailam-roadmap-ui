-- Migration 0022: Execution & Tracking redesign
--
-- Three parts, all part of the same "Review" stage overhaul:
--
-- 1. Renames the 9-stage pipeline's "Review" stage to "Execution &
--    Tracking" and removes "Approval" entirely -- its old function
--    (a per-stage gate) is now the stage-gate document upload in
--    part 3 below, not a separate pipeline stage. Any project
--    currently at "Review" or "Approval" moves to "Execution &
--    Tracking" first (a real ENUM value can't be dropped while rows
--    still hold it), same approach as migration 0019's Correction
--    merge.
--
-- 2. project_execution_steps moves from a linear Pending/Completed/
--    Waived status to a free-standing 0-100 completion_percentage
--    per step (plus optional remarks) -- project.progress is now the
--    weighted sum of these percentages rather than the sum of
--    fully-resolved steps' weights. A step already Completed or
--    Waived backfills to 100%; Pending backfills to 0%. The old
--    status/completed_*/waived_* columns are dropped outright (not
--    just stopped-using) since nothing reads them once this ships --
--    same "no dead columns left behind" approach as migration 0018
--    dropping the dead workflow_templates/workflow_stages tables.
--
-- 3. project_approval_steps moves from the same linear status model
--    to a stage-gate document: uploading a file for a stage IS what
--    marks that stage complete (see approval_process_service.
--    upload_stage_gate_document), so the old status/completed_*/
--    waived_*/is_optional columns are dropped and replaced with the
--    file reference columns project_documents already uses
--    (storage_key/original_filename/file_size_bytes) plus who/when
--    uploaded it.
--
-- Idempotent -- guarded by information_schema checks throughout, same
-- convention as every other migration here (see 0018's own header
-- comment on why: install.sh has no migration-tracking table and
-- reapplies every file on every run).
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0022_execution_tracking_redesign.sql

-- ---------------------------------------------------------------------------
-- Part 1: rename "Review" -> "Execution & Tracking", drop "Approval"
-- ---------------------------------------------------------------------------

UPDATE projects SET current_stage = 'Execution & Tracking' WHERE current_stage IN ('Review', 'Approval');

SET @needs_narrowing = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'projects' AND COLUMN_NAME = 'current_stage'
    AND (COLUMN_TYPE LIKE '%''Review''%' OR COLUMN_TYPE LIKE '%''Approval''%')
);
SET @sql = IF(@needs_narrowing > 0,
  'ALTER TABLE projects MODIFY COLUMN current_stage ENUM(''Enquiry'',''Quotation'',''Contract'',''Design'',''Government Submission'',''Execution & Tracking'',''Completed'') NOT NULL DEFAULT ''Enquiry''',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------------------------
-- Part 2: project_execution_steps -> percentage + remarks
-- ---------------------------------------------------------------------------

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_execution_steps' AND COLUMN_NAME = 'completion_percentage'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_execution_steps ADD COLUMN completion_percentage SMALLINT UNSIGNED NOT NULL DEFAULT 0 AFTER is_optional',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_execution_steps' AND COLUMN_NAME = 'remarks'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_execution_steps ADD COLUMN remarks TEXT NULL AFTER completion_percentage',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_status = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_execution_steps' AND COLUMN_NAME = 'status'
);
SET @sql = IF(@has_status > 0,
  'UPDATE project_execution_steps SET completion_percentage = CASE WHEN status IN (''Completed'',''Waived'') THEN 100 ELSE 0 END',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @constraint_exists = (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_execution_steps'
    AND CONSTRAINT_NAME = 'fk_project_execution_steps_completed_by'
);
SET @sql = IF(@constraint_exists > 0,
  'ALTER TABLE project_execution_steps DROP FOREIGN KEY fk_project_execution_steps_completed_by',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @constraint_exists = (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_execution_steps'
    AND CONSTRAINT_NAME = 'fk_project_execution_steps_waived_by'
);
SET @sql = IF(@constraint_exists > 0,
  'ALTER TABLE project_execution_steps DROP FOREIGN KEY fk_project_execution_steps_waived_by',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_execution_steps' AND COLUMN_NAME = 'status'
);
SET @sql = IF(@col_exists > 0, 'ALTER TABLE project_execution_steps DROP COLUMN status', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_execution_steps' AND COLUMN_NAME = 'completed_at'
);
SET @sql = IF(@col_exists > 0, 'ALTER TABLE project_execution_steps DROP COLUMN completed_at', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_execution_steps' AND COLUMN_NAME = 'completed_by'
);
SET @sql = IF(@col_exists > 0, 'ALTER TABLE project_execution_steps DROP COLUMN completed_by', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_execution_steps' AND COLUMN_NAME = 'waived_at'
);
SET @sql = IF(@col_exists > 0, 'ALTER TABLE project_execution_steps DROP COLUMN waived_at', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_execution_steps' AND COLUMN_NAME = 'waived_by'
);
SET @sql = IF(@col_exists > 0, 'ALTER TABLE project_execution_steps DROP COLUMN waived_by', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_execution_steps' AND COLUMN_NAME = 'waived_reason'
);
SET @sql = IF(@col_exists > 0, 'ALTER TABLE project_execution_steps DROP COLUMN waived_reason', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------------------------
-- Part 3: project_approval_steps -> stage-gate document
-- ---------------------------------------------------------------------------

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps' AND COLUMN_NAME = 'storage_key'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_approval_steps ADD COLUMN storage_key VARCHAR(255) NULL AFTER sequence_number',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps' AND COLUMN_NAME = 'original_filename'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_approval_steps ADD COLUMN original_filename VARCHAR(255) NULL AFTER storage_key',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps' AND COLUMN_NAME = 'file_size_bytes'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_approval_steps ADD COLUMN file_size_bytes BIGINT UNSIGNED NULL AFTER original_filename',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps' AND COLUMN_NAME = 'uploaded_at'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_approval_steps ADD COLUMN uploaded_at DATETIME NULL AFTER file_size_bytes',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps' AND COLUMN_NAME = 'uploaded_by'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_approval_steps ADD COLUMN uploaded_by BIGINT UNSIGNED NULL AFTER uploaded_at',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @constraint_exists = (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps'
    AND CONSTRAINT_NAME = 'fk_project_approval_steps_uploaded_by'
);
SET @sql = IF(@constraint_exists = 0,
  'ALTER TABLE project_approval_steps ADD CONSTRAINT fk_project_approval_steps_uploaded_by FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @constraint_exists = (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps'
    AND CONSTRAINT_NAME = 'fk_project_approval_steps_completed_by'
);
SET @sql = IF(@constraint_exists > 0,
  'ALTER TABLE project_approval_steps DROP FOREIGN KEY fk_project_approval_steps_completed_by',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @constraint_exists = (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps'
    AND CONSTRAINT_NAME = 'fk_project_approval_steps_waived_by'
);
SET @sql = IF(@constraint_exists > 0,
  'ALTER TABLE project_approval_steps DROP FOREIGN KEY fk_project_approval_steps_waived_by',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps' AND COLUMN_NAME = 'status'
);
SET @sql = IF(@col_exists > 0, 'ALTER TABLE project_approval_steps DROP COLUMN status', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps' AND COLUMN_NAME = 'completed_at'
);
SET @sql = IF(@col_exists > 0, 'ALTER TABLE project_approval_steps DROP COLUMN completed_at', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps' AND COLUMN_NAME = 'completed_by'
);
SET @sql = IF(@col_exists > 0, 'ALTER TABLE project_approval_steps DROP COLUMN completed_by', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps' AND COLUMN_NAME = 'waived_at'
);
SET @sql = IF(@col_exists > 0, 'ALTER TABLE project_approval_steps DROP COLUMN waived_at', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps' AND COLUMN_NAME = 'waived_by'
);
SET @sql = IF(@col_exists > 0, 'ALTER TABLE project_approval_steps DROP COLUMN waived_by', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps' AND COLUMN_NAME = 'waived_reason'
);
SET @sql = IF(@col_exists > 0, 'ALTER TABLE project_approval_steps DROP COLUMN waived_reason', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps' AND COLUMN_NAME = 'is_optional'
);
SET @sql = IF(@col_exists > 0, 'ALTER TABLE project_approval_steps DROP COLUMN is_optional', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0022 complete.' AS status;
