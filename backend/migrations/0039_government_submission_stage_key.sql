-- Migration 0039: link a government submission to the approval-process
-- gate its own approval satisfies
--
-- The real government-submission workflow (Government Center: create a
-- submission, upload required documents, submit, record the authority's
-- response, mark it Approved) had no connection at all to the project's
-- 5-gate Project Approval Process -- an authority's actual approval never
-- moved a project past the "Government Submission" workflow stage. The
-- only way to close those gates was the Process tab's generic "upload any
-- file" shortcut, disconnected from the real submission being tracked.
--
-- Adds an optional stage_key on government_submissions (one of
-- 'mew_approval', 'submit_baladia_kfd', 'permit_approved' -- see
-- GOVERNMENT_SUBMISSION_STAGE_KEYS in models/government.py). Once a
-- tagged submission reaches "Approved", submission_service.set_status
-- marks the matching ProjectApprovalStep complete and tries the
-- project's own auto-advance, the same way a stage-gate document
-- upload already does.
--
-- Idempotent -- guarded by an information_schema check, same pattern as
-- every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0039_government_submission_stage_key.sql

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'government_submissions' AND COLUMN_NAME = 'stage_key'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE government_submissions ADD COLUMN stage_key VARCHAR(40) NULL AFTER notes',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0039 complete.' AS status;
