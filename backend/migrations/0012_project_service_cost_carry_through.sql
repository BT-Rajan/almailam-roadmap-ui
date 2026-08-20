-- Migration 0012: carry service costs from project creation to quotation
--
-- The New Project Wizard's service picker (ServicePickerDialog) already
-- computed and sent a granular activity breakdown plus its total on
-- project creation, but the backend had no columns to store either one --
-- they were silently dropped, so NewQuotationDialog's "prefill line items
-- from the project's picked services" never had anything to prefill from
-- after the initial page load. This adds:
--   - projects.service_total: the total captured at creation
--   - project_selected_activities: one row per picked activity, a
--     snapshot of what was picked and at what price
--
-- Idempotent -- guarded by information_schema checks, same pattern as
-- migration 0008.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0012_project_service_cost_carry_through.sql

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'projects' AND COLUMN_NAME = 'service_total'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE projects ADD COLUMN service_total DECIMAL(12,2) NULL AFTER stale_notified_at',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

CREATE TABLE IF NOT EXISTS project_selected_activities (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id      BIGINT UNSIGNED NOT NULL,
    service_id      VARCHAR(20) NOT NULL,
    service_name    VARCHAR(150) NOT NULL,
    activity_id     VARCHAR(20) NOT NULL,
    activity_name   VARCHAR(150) NOT NULL,
    fixed_cost      DECIMAL(12,2) NOT NULL,
    CONSTRAINT fk_project_selected_activities_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_project_selected_activities_project (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SELECT 'Migration 0012 complete.' AS status;
