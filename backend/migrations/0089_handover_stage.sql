-- Migration 0089: a real "Handover" workflow stage, replacing the old
-- shape where Design -> Government Submission -> Supervision was a
-- fixed sequential chain and "project completion" lived entirely
-- outside the stage machine as a project.status flip gated by a
-- separate _all_tracks_closed check.
--
-- Design, Government Submission (Permits), and Supervision now run as
-- independent, parallel tracks off Contract -- a project takes
-- whichever of the three it actually includes, in no particular order,
-- and all of them converge on Handover once done. See
-- core/status_transitions.PROJECT_STAGE_ALLOWED_TRANSITIONS and
-- project_service._assert_stage_exit_criteria's Handover branch for the
-- actual graph/gate.
--
-- Idempotent -- guarded by information_schema checks / a safe-to-rerun
-- MODIFY COLUMN, same convention as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0089_handover_stage.sql

SET @db := DATABASE();

-- ----------------------------------------------------------------------------
-- 1. projects.current_stage gains 'Handover'
-- ----------------------------------------------------------------------------

ALTER TABLE projects
  MODIFY COLUMN current_stage
    ENUM('Requirement','Quotation','Payment Plan','Contract','Design','Government Submission','Supervision','Handover')
    NOT NULL DEFAULT 'Requirement';

-- ----------------------------------------------------------------------------
-- 2. projects: manual payment confirmation + closing notes for the
--    Handover stage's Payment Confirmation / Notes and Report tabs
-- ----------------------------------------------------------------------------

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'projects' AND column_name = 'handover_payment_confirmed_at'
);
SET @sql := IF(@col_exists = 0,
    'ALTER TABLE projects
       ADD COLUMN handover_payment_confirmed_at DATETIME NULL,
       ADD COLUMN handover_payment_confirmed_by BIGINT UNSIGNED NULL,
       ADD COLUMN handover_notes TEXT NULL,
       ADD CONSTRAINT fk_projects_handover_payment_confirmed_by FOREIGN KEY (handover_payment_confirmed_by)
           REFERENCES users(id) ON DELETE SET NULL',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0089 complete.' AS status;
