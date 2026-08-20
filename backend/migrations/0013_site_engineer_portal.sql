-- Migration 0013: Site Engineer Portal
--
-- Adds:
--   1. users.employee_id -- an alternate login identifier for the Site
--      Engineer Portal (login by employee ID + password, same
--      password_hash as the existing username login -- not a separate
--      account or credential).
--   2. status_reports -- one supervision report per engineer per day,
--      filed through the portal, digitizing the paper "تقرير إشراف"
--      form (report date, project, what was received/inspected, type
--      of supervision, engineer's free-text notes).
--   3. company_settings.status_report_recipient_id -- the staff member
--      who reviews incoming reports and attaches them to the relevant
--      project's timeline.
--   4. project_timeline_events.type gets a new 'field_activity' value
--      -- what an attached status report becomes on the project
--      timeline. Deliberately excluded from the customer portal's
--      events feed (see customer_portal_service.py) -- internal
--      supervision content, not a client-facing update.
--
-- Idempotent -- guarded by information_schema checks, same pattern as
-- migrations 0008-0010.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0013_site_engineer_portal.sql

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'employee_id'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE users ADD COLUMN employee_id VARCHAR(30) NULL UNIQUE AFTER username',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'company_settings' AND COLUMN_NAME = 'status_report_recipient_id'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE company_settings ADD COLUMN status_report_recipient_id BIGINT UNSIGNED NULL AFTER stale_onboarding_alert_days, '
  'ADD CONSTRAINT fk_company_settings_status_report_recipient FOREIGN KEY (status_report_recipient_id) REFERENCES users(id) ON DELETE SET NULL',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- MySQL/MariaDB can't add an ENUM value with a plain ALTER COLUMN in one
-- portable statement across versions the same way TEXT columns can be
-- altered -- MODIFY COLUMN with the full new value list is the
-- straightforward, safe way to add one.
ALTER TABLE project_timeline_events
  MODIFY COLUMN type ENUM('stage','document','quotation','contract','submission','milestone','task','note','field_activity') NOT NULL;

CREATE TABLE IF NOT EXISTS status_reports (
    id                          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    report_no                   VARCHAR(20)  NOT NULL UNIQUE,
    project_id                  BIGINT UNSIGNED NOT NULL,
    engineer_id                 BIGINT UNSIGNED NOT NULL,
    report_date                 DATE NOT NULL,
    receipt_type                VARCHAR(200) NULL,
    supervision_type            ENUM('Full-time','Part-time') NOT NULL DEFAULT 'Full-time',
    notes                       TEXT NOT NULL,
    status                      ENUM('Pending','Attached') NOT NULL DEFAULT 'Pending',
    attached_task_id            BIGINT UNSIGNED NULL,
    attached_timeline_event_id  BIGINT UNSIGNED NULL,
    attached_by                 BIGINT UNSIGNED NULL,
    attached_at                 DATETIME NULL,
    created_at                  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at                  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_status_reports_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_status_reports_engineer FOREIGN KEY (engineer_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_status_reports_task FOREIGN KEY (attached_task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    CONSTRAINT fk_status_reports_timeline_event FOREIGN KEY (attached_timeline_event_id) REFERENCES project_timeline_events(id) ON DELETE SET NULL,
    CONSTRAINT fk_status_reports_attached_by FOREIGN KEY (attached_by) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT uq_status_reports_engineer_date UNIQUE (engineer_id, report_date),
    INDEX idx_status_reports_project (project_id),
    INDEX idx_status_reports_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SELECT 'Migration 0013 complete.' AS status;
