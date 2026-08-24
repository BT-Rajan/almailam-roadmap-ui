-- Migration 0037: close the service_catalog_items lazy-seeding race
--
-- Companion to the earlier role_definitions/ai_configuration race fix.
-- service_catalog_items.name had no database-level uniqueness at all
-- (confirmed directly against schema.sql) -- a concurrent race in
-- service_catalog_service._ensure_seeded wouldn't crash, it would
-- silently insert duplicate default services instead. This adds the
-- missing constraint so the accompanying try/except IntegrityError fix
-- actually has something to catch.
--
-- Uses a generated column rather than a plain UNIQUE(name), because
-- the table is soft-deletable and the uniqueness rule only makes sense
-- among active rows -- a deleted service's name should be reusable.
-- MySQL/MariaDB treat multiple NULLs in a UNIQUE index as
-- non-conflicting, so a column that's NULL for soft-deleted rows and
-- the lowercased name otherwise gives exactly that behaviour, matching
-- what _assert_name_available already checks at the application layer.
--
-- Note: workflow_templates had the identical seeding race, but that
-- table (and the admin-editable "Workflow Configuration" system it
-- backed) was dropped entirely by migration 0018_process_cleanup.sql
-- as dead, never-wired-up code -- nothing left there to fix.
--
-- Safety: adding this fails outright if duplicate active names already
-- exist. Checked first, reported clearly, and the constraint is
-- skipped (existing behaviour left exactly as-is) rather than the
-- migration guessing which duplicate should "win" -- same approach as
-- migration 0015's financial-agreement uniqueness fix.
--
-- Idempotent -- guarded by information_schema checks, same pattern as
-- every other migration in this directory. install.sh reapplies every
-- migration file on every run with no tracking of what already ran, so
-- this has to tolerate running again against a database it's already
-- been applied to.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0037_service_catalog_seed_race.sql

SELECT LOWER(name) AS duplicate_active_service_name, COUNT(*) AS row_count
FROM service_catalog_items
WHERE deleted_at IS NULL
GROUP BY LOWER(name)
HAVING COUNT(*) > 1;
-- ^ If this returns any rows, resolve them manually (decide which
--   should survive, rename or soft-delete the rest) before re-running.

SET @dup_services = (
  SELECT COUNT(*) FROM (
    SELECT LOWER(name) FROM service_catalog_items WHERE deleted_at IS NULL GROUP BY LOWER(name) HAVING COUNT(*) > 1
  ) AS dupes
);

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'service_catalog_items' AND COLUMN_NAME = 'active_name_lower'
);
SET @sql = IF(@col_exists = 0 AND @dup_services = 0,
  'ALTER TABLE service_catalog_items '
  'ADD COLUMN active_name_lower VARCHAR(150) GENERATED ALWAYS AS (IF(deleted_at IS NULL, LOWER(name), NULL)) STORED, '
  'ADD CONSTRAINT uq_service_catalog_items_active_name UNIQUE (active_name_lower)',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT
  IF(@dup_services > 0,
    'Migration 0037 SKIPPED the constraint -- duplicate active service names exist, see the report above. Resolve them and re-run.',
    'Migration 0037 complete.'
  ) AS status;
