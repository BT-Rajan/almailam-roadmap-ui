-- Migration 0099: restructure government_submissions from the old
-- Draft/Submitted/Under Review/Comments Received/Approved/Rejected/
-- Withdrawn status machine into the 5-stage Permit Application
-- workspace: Prepare -> Apply -> Track <-> Update -> Close. See
-- backend/app/models/government.py's GovernmentSubmission docstring
-- and backend/app/core/status_transitions.py's
-- SUBMISSION_ALLOWED_TRANSITIONS for the design.
--
-- Existing rows are mapped onto the nearest new stage rather than
-- reset to Prepare, so applications already in flight don't lose their
-- place:
--   Draft                -> Prepare  (never actually filed yet)
--   Submitted             -> Track    (already filed; the old
--                                      proof-of-submission upload is
--                                      what Apply's acknowledgement
--                                      upload now is)
--   Under Review          -> Track
--   Comments Received     -> Update   (the authority asked for
--                                      something else -- exactly what
--                                      Update is for)
--   Approved/Rejected     -> Close, response_outcome carried over as-is
--   Withdrawn             -> Close, response_outcome set to 'Withdrawn'
--                                      (a new response_outcome value --
--                                      see the ALTER below)
--
-- Idempotent -- guarded by information_schema checks, same convention
-- as every other migration here (e.g. migration 0097).
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0099_permit_application_stages.sql

SET @db := DATABASE();

-- 1. Widen response_outcome to add 'Withdrawn' BEFORE any row needs it,
--    so the data migration below can actually set it.
SET @outcome_needs_withdrawn := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'government_submissions'
      AND column_name = 'response_outcome' AND column_type NOT LIKE '%Withdrawn%'
);
SET @sql := IF(@outcome_needs_withdrawn > 0,
    "ALTER TABLE government_submissions MODIFY COLUMN response_outcome ENUM('Approved', 'Rejected', 'No Response', 'Withdrawn') NULL",
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2. Add the new columns this migration introduces, each guarded
--    independently since a partially-applied prior run shouldn't
--    re-fail or re-add anything.
SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'government_submissions' AND column_name = 'readiness_confirmed_at'
);
SET @sql := IF(@col_exists = 0,
    "ALTER TABLE government_submissions ADD COLUMN readiness_confirmed_at DATETIME NULL AFTER notes",
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'government_submissions' AND column_name = 'readiness_confirmed_by'
);
SET @sql := IF(@col_exists = 0,
    "ALTER TABLE government_submissions ADD COLUMN readiness_confirmed_by BIGINT UNSIGNED NULL AFTER readiness_confirmed_at, ADD CONSTRAINT fk_gov_sub_readiness_by FOREIGN KEY (readiness_confirmed_by) REFERENCES users(id) ON DELETE SET NULL",
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'government_submissions' AND column_name = 'acknowledgement_number'
);
SET @sql := IF(@col_exists = 0,
    "ALTER TABLE government_submissions ADD COLUMN acknowledgement_number VARCHAR(60) NULL AFTER readiness_confirmed_by",
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'government_submissions' AND column_name = 'payment_reference'
);
SET @sql := IF(@col_exists = 0,
    "ALTER TABLE government_submissions ADD COLUMN payment_reference VARCHAR(100) NULL AFTER acknowledgement_number",
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'government_submissions' AND column_name = 'closing_notes'
);
SET @sql := IF(@col_exists = 0,
    "ALTER TABLE government_submissions ADD COLUMN closing_notes TEXT NULL",
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 3. Migrate the `status` column's data onto the new stage vocabulary,
--    then rename+retype it to `stage`. Only runs if `status` still
--    exists (an already-migrated database, or a fresh one created
--    straight from the current models.py, has `stage` from the start).
SET @has_old_status := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'government_submissions' AND column_name = 'status'
);

SET @sql := IF(@has_old_status > 0,
    "UPDATE government_submissions SET response_outcome = 'Withdrawn' WHERE status = 'Withdrawn'",
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := IF(@has_old_status > 0,
    "ALTER TABLE government_submissions ADD COLUMN stage ENUM('Prepare','Apply','Track','Update','Close') NOT NULL DEFAULT 'Prepare' AFTER project_selected_permit_id",
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := IF(@has_old_status > 0,
    "UPDATE government_submissions SET stage = CASE status
        WHEN 'Draft' THEN 'Prepare'
        WHEN 'Submitted' THEN 'Track'
        WHEN 'Under Review' THEN 'Track'
        WHEN 'Comments Received' THEN 'Update'
        WHEN 'Approved' THEN 'Close'
        WHEN 'Rejected' THEN 'Close'
        WHEN 'Withdrawn' THEN 'Close'
        ELSE 'Prepare' END",
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := IF(@has_old_status > 0,
    "ALTER TABLE government_submissions DROP COLUMN status",
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 4. submission_followups: distinguish Track vs Update entries, and let
--    an Update entry carry its own document (an additional document
--    the authority asked for, or an updated version of one already
--    sent) -- a plain Track entry leaves these null.
SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'submission_followups' AND column_name = 'stage'
);
SET @sql := IF(@col_exists = 0,
    "ALTER TABLE submission_followups ADD COLUMN stage ENUM('Track','Update') NOT NULL DEFAULT 'Track' AFTER submission_id",
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'submission_followups' AND column_name = 'storage_key'
);
SET @sql := IF(@col_exists = 0,
    "ALTER TABLE submission_followups ADD COLUMN storage_key VARCHAR(300) NULL, ADD COLUMN original_filename VARCHAR(255) NULL, ADD COLUMN file_size_bytes BIGINT NULL",
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Existing follow-ups predate the Track/Update split entirely -- a
-- Comments-Received-era application's follow-ups genuinely were what
-- Update now means, so backfill by the submission's own migrated stage
-- rather than leaving every historical row mislabeled 'Track'.
SET @sql := IF(@has_old_status > 0,
    "UPDATE submission_followups sf
     JOIN government_submissions gs ON gs.id = sf.submission_id
     SET sf.stage = 'Update'
     WHERE gs.stage = 'Update'",
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0099 complete.' AS status;
