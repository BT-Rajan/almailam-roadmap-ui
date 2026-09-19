-- Migration 0108: Merge the permit application's Track and Update stages
--
-- A permit application used to walk 5 stages: Prepare -> Apply -> Track
-- <-> Update -> Close, where Update was "Track, plus a document" for
-- when the authority asked for something else. In practice that was one
-- stage with two kinds of log entry, and staff bounced between the two
-- for no reason a person could feel. It is now 4 stages -- Prepare ->
-- Apply -> Track -> Close -- and a follow-up in Track can carry a
-- document whenever the authority asked for one (see
-- submission_service.add_followup).
--
-- What this changes:
--   1. government_submissions.stage: any application sitting in Update
--      moves to Track (where it would have gone back to anyway), then the
--      enum loses 'Update'.
--   2. submission_followups.stage is dropped -- it only existed to
--      record whether an entry was logged under Track or Update. Every
--      entry, and any document attached to it, is kept.
--
-- audit_log rows that mention 'Update' as a previous/new stage are
-- history and are left as they are.
--
-- Idempotent -- each step is guarded by an information_schema check, same
-- convention as migration 0099 (which introduced these stages), so it is
-- safe to run again or against a database that never had Update.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0108_merge_permit_application_track_and_update.sql

SET @db := DATABASE();

-- 1. Applications in Update -> Track, then drop 'Update' from the enum.
SET @stage_has_update := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'government_submissions'
      AND column_name = 'stage' AND column_type LIKE '%Update%'
);

SET @sql := IF(@stage_has_update > 0,
    "UPDATE government_submissions SET stage = 'Track' WHERE stage = 'Update'",
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := IF(@stage_has_update > 0,
    "ALTER TABLE government_submissions MODIFY COLUMN stage ENUM('Prepare','Apply','Track','Close') NOT NULL DEFAULT 'Prepare'",
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2. Follow-ups no longer record which stage they were logged under.
SET @followup_has_stage := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'submission_followups' AND column_name = 'stage'
);
SET @sql := IF(@followup_has_stage > 0,
    "ALTER TABLE submission_followups DROP COLUMN stage",
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0108 complete.' AS status;
