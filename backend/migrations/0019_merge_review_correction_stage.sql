-- Migration 0019: merge the "Correction" stage into "Review"
--
-- "Correction" used to be its own stage in the 9-stage project
-- pipeline, looping back and forth with "Review" (Review -> Correction
-- -> Review -> Approval), with a required reason on the way into
-- Correction. That back-and-forth stage hop wasn't preserving anything
-- a reason-carrying project timeline note doesn't already cover --
-- staff now log a correction cycle as a note on the project instead of
-- moving its stage back and forth. See core/status_transitions.py's
-- own comment on PROJECT_STAGE_ALLOWED_TRANSITIONS for the full
-- reasoning.
--
-- Any project currently sitting at "Correction" is moved to "Review"
-- first (a real ENUM value can't be dropped while rows still hold it),
-- then the ENUM itself is narrowed to drop "Correction".
--
-- Idempotent -- guarded by an information_schema check on the ENUM
-- definition itself, same convention as every other migration here
-- (see 0018's own header comment on why: install.sh has no migration-
-- tracking table and reapplies every file on every run).
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0019_merge_review_correction_stage.sql

UPDATE projects SET current_stage = 'Review' WHERE current_stage = 'Correction';

SET @needs_narrowing = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'projects' AND COLUMN_NAME = 'current_stage'
    AND COLUMN_TYPE LIKE '%''Correction''%'
);
SET @sql = IF(@needs_narrowing > 0,
  'ALTER TABLE projects MODIFY COLUMN current_stage ENUM(''Enquiry'',''Quotation'',''Contract'',''Design'',''Government Submission'',''Review'',''Approval'',''Completed'') NOT NULL DEFAULT ''Enquiry''',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0019 complete.' AS status;
