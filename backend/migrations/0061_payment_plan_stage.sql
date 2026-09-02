-- Migration 0061: insert a "Payment Plan" workflow stage between
-- Quotation and Contract, and give financial_agreements a status
-- (Draft/Approved) so a project can no longer reach Contract on the
-- strength of a merely-*created* agreement -- it now has to be
-- explicitly approved first (see project_service._assert_stage_exit_
-- criteria and payment_service.approve_agreement).
--
-- Idempotent -- guarded by information_schema checks, same convention
-- as every other migration here (install.sh reapplies every migration
-- file on every run with no tracking of what already ran).
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0061_payment_plan_stage.sql

SET @db := DATABASE();

-- 1. projects.current_stage -- add 'Payment Plan' to the enum, between
--    Quotation and Contract. MODIFY COLUMN with an identical definition
--    is a safe no-op, so this is naturally idempotent on its own --
--    still existence-guarded since a MODIFY against a dropped column
--    would fail outright.
SET @stage_col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'projects' AND column_name = 'current_stage'
);
SET @sql := IF(@stage_col_exists > 0,
    "ALTER TABLE projects MODIFY COLUMN current_stage ENUM('Requirement','Quotation','Payment Plan','Contract','Design','Supervision','Government Submission') NOT NULL DEFAULT 'Requirement'",
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2. financial_agreements.status -- new agreements default to 'Draft'
--    and must be explicitly approved (see AGREEMENT_STATUSES). Every
--    agreement that already existed before this migration predates the
--    approval concept entirely and was already treated as final under
--    the old rules (the project may well have already advanced past
--    Contract on the strength of it) -- backfilled to 'Approved' below
--    so this migration can't retroactively strand an already-progressed
--    project behind a gate that didn't exist when it passed through.
SET @status_col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'financial_agreements' AND column_name = 'status'
);
SET @sql := IF(@status_col_exists = 0,
    "ALTER TABLE financial_agreements ADD COLUMN status ENUM('Draft','Approved') NOT NULL DEFAULT 'Draft' AFTER stream",
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := IF(@status_col_exists = 0,
    "UPDATE financial_agreements SET status = 'Approved'",
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0061 complete.' AS status;
