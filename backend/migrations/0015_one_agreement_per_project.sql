-- Migration 0015: one financial agreement per project, enforced
--
-- The staff UI has only ever offered "Create Agreement" when a project
-- doesn't already have one, but that was purely a UI convention -- the
-- database itself allowed any number of agreements per project (only a
-- plain, non-unique index on project_id). Found while auditing the
-- customer portal: its budget query picked whichever agreement came
-- back first with no explicit ordering, which would have been silently
-- non-deterministic if this were ever violated. This migration makes
-- "one per project" a real, enforced rule.
--
-- Safety: adding a UNIQUE constraint fails outright if duplicate
-- project_id values already exist. Rather than let that happen with a
-- cryptic constraint-violation error, this checks for duplicates first
-- and reports them clearly, leaving the existing (non-unique) index in
-- place and skipping the constraint until they're resolved manually --
-- picking which agreement should be the one that survives is a business
-- decision, not something a migration should decide unilaterally.
--
-- Idempotent -- guarded by information_schema checks, same pattern as
-- earlier migrations. Safe to re-run after resolving any reported
-- duplicates; it will pick up and add the constraint on a later run.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0015_one_agreement_per_project.sql

SELECT project_id, COUNT(*) AS agreement_count
FROM financial_agreements
GROUP BY project_id
HAVING COUNT(*) > 1;
-- ^ If this returns any rows, STOP: those projects have more than one
--   financial agreement. Decide which agreement should be kept for
--   each (and what to do with the rest -- e.g. move any of their
--   payments/obligations, or delete them if they were created in
--   error), resolve it manually, then re-run this migration.

SET @duplicate_count = (
  SELECT COUNT(*) FROM (
    SELECT project_id FROM financial_agreements GROUP BY project_id HAVING COUNT(*) > 1
  ) AS dupes
);

SET @constraint_exists = (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'financial_agreements'
    AND CONSTRAINT_NAME = 'uq_financial_agreements_project'
);

SET @old_index_exists = (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'financial_agreements'
    AND INDEX_NAME = 'idx_financial_agreements_project'
);

SET @sql = IF(@duplicate_count = 0 AND @constraint_exists = 0,
  'ALTER TABLE financial_agreements ADD CONSTRAINT uq_financial_agreements_project UNIQUE (project_id)',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- The old non-unique index becomes redundant once the unique
-- constraint exists (a UNIQUE key already serves as an index) -- drop
-- it only after confirming the new constraint actually landed.
SET @constraint_exists_after = (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'financial_agreements'
    AND CONSTRAINT_NAME = 'uq_financial_agreements_project'
);
SET @sql = IF(@old_index_exists > 0 AND @constraint_exists_after > 0,
  'ALTER TABLE financial_agreements DROP INDEX idx_financial_agreements_project',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT
  IF(@duplicate_count > 0,
    'Migration 0015 SKIPPED the constraint -- duplicate project_id values exist, see the report above. Resolve them and re-run this migration.',
    'Migration 0015 complete.'
  ) AS status;
