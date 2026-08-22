-- Migration 0021: Delivery deviation notes
--
-- projects.deviation_notes -- a PM-editable annotation on the Overview
-- tab's Completion summary, distinct from the existing completion_notes
-- (general handover/lessons-learned free text). This one specifically
-- backs the "what we delivered vs. what was asked for" section: the
-- scope-change list itself is derived live from contracts/contract_
-- revisions (never stored here, same reasoning as budget in migration
-- 0020), but a PM can confirm/explain that auto-derived read in their
-- own words -- e.g. "revision R1 was cosmetic, no real scope change"
-- or, when nothing at all changed, an explicit confirmation rather
-- than just an empty section.
--
-- Idempotent -- guarded by information_schema checks, same pattern as
-- migrations 0004/0008-0010/0013/0015/0018/0020.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0021_deviation_notes.sql

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'projects' AND COLUMN_NAME = 'deviation_notes'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE projects ADD COLUMN deviation_notes TEXT NULL AFTER completion_notes',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0021 complete.' AS status;
