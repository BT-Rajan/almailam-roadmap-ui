-- Migration 0074: Supervision activities gain the same eligibility
-- gating Permits already have (migration 0073) -- "only when few
-- design activities get completed we can start... same case apply for
-- supervision." project_selected_supervision_activities.status widens
-- from ('Not Started','In Progress','Complete','Cancelled') to
-- ('Planned','Eligible','In Progress','Complete','Cancelled'), default
-- changes from 'Not Started' to 'Planned' (existing 'Not Started' rows
-- are migrated to 'Planned'), and the table gains eligibility_met_at/
-- eligibility_notified_at, mirroring project_selected_permits exactly.
-- See project_service._recompute_supervision_eligibility and
-- SupervisionPrerequisite (table already added in migration 0073,
-- unused until this migration's application code exists).
--
-- Idempotent -- widen-migrate-narrow is the same safe, repeatable
-- pattern migration 0002 uses for a narrowing enum change; MODIFY
-- COLUMN to the same target enum is safe to run more than once (see
-- migration 0005), and the data UPDATE becomes a no-op after the first
-- run since no row is left with status = 'Not Started'.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0074_supervision_eligibility.sql

SET @db := DATABASE();

ALTER TABLE project_selected_supervision_activities
  MODIFY COLUMN status ENUM('Not Started','Planned','Eligible','In Progress','Complete','Cancelled')
  NOT NULL DEFAULT 'Not Started';

UPDATE project_selected_supervision_activities SET status = 'Planned' WHERE status = 'Not Started';

ALTER TABLE project_selected_supervision_activities
  MODIFY COLUMN status ENUM('Planned','Eligible','In Progress','Complete','Cancelled')
  NOT NULL DEFAULT 'Planned';

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'project_selected_supervision_activities'
      AND column_name = 'eligibility_met_at'
);
SET @sql := IF(@col_exists = 0,
    'ALTER TABLE project_selected_supervision_activities
       ADD COLUMN eligibility_met_at DATETIME NULL AFTER status,
       ADD COLUMN eligibility_notified_at DATETIME NULL AFTER eligibility_met_at',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0074 complete.' AS status;
