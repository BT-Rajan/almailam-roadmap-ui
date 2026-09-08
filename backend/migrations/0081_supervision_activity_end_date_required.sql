-- Migration 0081: make project_selected_supervision_activities.end_date
-- required.
--
-- It used to be nullable -- a Supervision activity could be selected
-- (and the project driven all the way through Design, Government
-- Submission, and into Supervision itself) with no end date at all,
-- only to hit a wall once staff tried to create its Financial Agreement
-- (payment_service._compute_contract_terms hard-requires one to build
-- the day-prorated monthly billing schedule). A real, confirmed bug: a
-- user could reach Payment Plan with no way forward and no early
-- warning. Now caught at the point of selection instead -- see
-- SelectedSupervisionActivityIn in app/schemas/project.py.
--
-- Backfills any existing NULL end_date row to its own start_date (the
-- same safe fallback _persist_supervision_selection's own validation
-- used to fall back to) before narrowing the column, same
-- "backfill-then-narrow" shape as every other NOT-NULL tightening here.
--
-- Idempotent -- the UPDATE is a no-op once no NULL rows remain, and the
-- ALTER is a no-op once the column is already NOT NULL.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0081_supervision_activity_end_date_required.sql

UPDATE project_selected_supervision_activities
SET end_date = start_date
WHERE end_date IS NULL;

SET @col_is_nullable = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_selected_supervision_activities'
    AND COLUMN_NAME = 'end_date' AND IS_NULLABLE = 'YES'
);
SET @sql = IF(@col_is_nullable > 0,
  'ALTER TABLE project_selected_supervision_activities MODIFY COLUMN end_date DATE NOT NULL',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0081 complete.' AS status;
