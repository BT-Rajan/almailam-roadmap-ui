-- Migration 0008: stale-project notification support
--
-- Adds the admin-configurable threshold (company_settings.
-- stale_project_alert_days, default 45) and the per-project tracking
-- column (projects.stale_notified_at) that lets the background check
-- notify a project's assigned engineer once when it hasn't moved in a
-- while, without re-notifying every time the check runs.
--
-- Idempotent -- guarded by information_schema checks, same pattern as
-- earlier migrations.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0008_stale_project_alerts.sql

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'company_settings' AND COLUMN_NAME = 'stale_project_alert_days'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE company_settings ADD COLUMN stale_project_alert_days INT UNSIGNED NOT NULL DEFAULT 45 AFTER default_quotation_validity_days',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'projects' AND COLUMN_NAME = 'stale_notified_at'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE projects ADD COLUMN stale_notified_at DATETIME NULL AFTER status',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0008 complete.' AS status;
