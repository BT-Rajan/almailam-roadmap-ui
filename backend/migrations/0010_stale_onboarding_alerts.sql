-- Migration 0010: stale-onboarding notification support
--
-- Sibling to migration 0008 (stale-project alerts), same mechanism
-- applied to client onboarding: adds the admin-configurable threshold
-- (company_settings.stale_onboarding_alert_days, default 5) and the
-- per-client tracking column (clients.onboarding_notified_at) that
-- lets the background check notify a client's account manager once
-- when onboarding hasn't moved in a while, without re-notifying every
-- time the check runs.
--
-- Idempotent -- guarded by information_schema checks, same pattern as
-- migration 0008.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0009_stale_onboarding_alerts.sql

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'company_settings' AND COLUMN_NAME = 'stale_onboarding_alert_days'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE company_settings ADD COLUMN stale_onboarding_alert_days INT UNSIGNED NOT NULL DEFAULT 5 AFTER stale_project_alert_days',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'clients' AND COLUMN_NAME = 'onboarding_notified_at'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE clients ADD COLUMN onboarding_notified_at DATETIME NULL AFTER onboarding_state',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0010 complete.' AS status;
