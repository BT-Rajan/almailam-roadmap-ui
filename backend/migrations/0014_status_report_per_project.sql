-- Migration 0014: one status report per engineer *per project* per day
--
-- Previously the uniqueness rule was (engineer_id, report_date) -- one
-- report per engineer per day, full stop. An engineer assigned to more
-- than one project needs to file a separate report for each project
-- they supervised that day, so this widens the rule to (engineer_id,
-- project_id, report_date).
--
-- Safe to run even if some engineers already have exactly one report
-- per day under the old rule -- the old constraint is a strict subset
-- of data already satisfying the new one (fewer distinct rows per
-- engineer-day can only make the new, more permissive constraint
-- easier to satisfy, never harder), so no data conflicts are possible
-- from widening it this direction.
--
-- Idempotent -- guarded by information_schema checks, same pattern as
-- earlier migrations.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0014_status_report_per_project.sql

-- Order matters here: MySQL/MariaDB won't let the old unique index be
-- dropped while it's still the only index backing the foreign key on
-- engineer_id -- confirmed directly (ERROR 1553, "needed in a foreign
-- key constraint") when this was written the other way around. The new
-- constraint also starts with engineer_id, so creating it first gives
-- the foreign key an alternative supporting index, and only then can
-- the old one be safely dropped.

SET @new_constraint_exists = (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'status_reports'
    AND CONSTRAINT_NAME = 'uq_status_reports_engineer_project_date'
);
SET @sql = IF(@new_constraint_exists = 0,
  'ALTER TABLE status_reports ADD CONSTRAINT uq_status_reports_engineer_project_date UNIQUE (engineer_id, project_id, report_date)',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @old_constraint_exists = (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'status_reports'
    AND CONSTRAINT_NAME = 'uq_status_reports_engineer_date'
);
SET @sql = IF(@old_constraint_exists > 0,
  'ALTER TABLE status_reports DROP INDEX uq_status_reports_engineer_date',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0014 complete.' AS status;
