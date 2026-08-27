-- Migration 0052: add "No Response" as a third government_submissions
-- response outcome
--
-- Previously only Approved/Rejected -- doesn't cover a follow-up made
-- after the authority's own response window closed with nothing back,
-- which is still a real, recordable outcome (just one that can never
-- satisfy "Mark Complete", same as Rejected).
--
-- Widening an ENUM (adding a value) needs no data reassignment first,
-- unlike narrowing one -- every existing row's value is still valid
-- under the new, larger set.
--
-- Idempotent -- guarded by an information_schema check, same convention
-- as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0052_submission_no_response_outcome.sql

SET @db := DATABASE();

SET @needs_widening := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'government_submissions' AND COLUMN_NAME = 'response_outcome'
        AND COLUMN_TYPE NOT LIKE '%''No Response''%'
);
SET @sql := IF(@needs_widening > 0,
    'ALTER TABLE government_submissions MODIFY COLUMN response_outcome ENUM(''Approved'',''Rejected'',''No Response'') NULL',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0052 complete.' AS status;
