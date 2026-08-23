-- Migration 0033: approval-step completion via tagged document approvals
--
-- Adds a second way to close a Project Approval Process stage gate.
-- Since migration 0022, the only way was uploading the stage's own
-- review document (storage_key set). This adds completed_at/
-- completed_by so a stage can also be marked complete once the
-- project_documents rows tagged to it (via project_documents.
-- stage_key) are reviewed and approved -- see
-- approval_process_service.complete_stage_from_documents. The two
-- paths are independent and both idempotent: uploading a gate
-- document afterward doesn't clear completed_at, and completing via
-- documents doesn't set storage_key. ProjectApprovalStepOut.hasDocument
-- keeps its exact old meaning (storage_key is not None); isComplete
-- is the new field UI should use for the "is this stage done" check,
-- true if either path fired.
--
-- Idempotent -- guarded by information_schema checks, same convention
-- as every other migration here (install.sh reapplies every file on
-- every run with no migration-tracking table).
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0033_approval_step_document_completion.sql

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps' AND COLUMN_NAME = 'completed_at'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_approval_steps ADD COLUMN completed_at DATETIME NULL AFTER uploaded_by',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps' AND COLUMN_NAME = 'completed_by'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_approval_steps ADD COLUMN completed_by BIGINT UNSIGNED NULL AFTER completed_at',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @fk_exists = (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps'
    AND CONSTRAINT_NAME = 'fk_project_approval_steps_completed_by'
);
SET @sql = IF(@fk_exists = 0,
  'ALTER TABLE project_approval_steps ADD CONSTRAINT fk_project_approval_steps_completed_by
     FOREIGN KEY (completed_by) REFERENCES users(id) ON DELETE SET NULL',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0033 complete.' AS status;
