-- Migration 0096: scheduled_reports (Administration > Scheduled Reports --
-- "auto email report sender").
--
-- One row per configured schedule: which report (business_summary/
-- financial_summary/project_status), who receives it, and when it fires
-- (once at a specific date+time, or daily/weekly/monthly between an
-- optional start and end date -- NULL end_date means it runs
-- indefinitely). See app/models/scheduled_report.py for the full field
-- documentation and app/services/scheduled_report_service.py for how
-- next_run_at is computed and consumed by the scheduler tick in main.py.
--
-- Idempotent -- guarded by an information_schema check, same convention
-- as every other migration here (e.g. migration 0095).
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0096_scheduled_reports.sql

SET @db := DATABASE();

SET @table_exists := (
    SELECT COUNT(*) FROM information_schema.tables
    WHERE table_schema = @db AND table_name = 'scheduled_reports'
);
SET @sql := IF(@table_exists = 0,
    'CREATE TABLE scheduled_reports (
        id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        name                VARCHAR(150) NOT NULL,
        report_type         ENUM(''business_summary'',''financial_summary'',''project_status'') NOT NULL,
        project_id          BIGINT UNSIGNED NULL,
        period              ENUM(''last_7_days'',''last_30_days'',''this_month'',''last_month'',''this_quarter'',''this_year'') NULL,
        recipients          JSON NOT NULL,
        subject             VARCHAR(300) NULL,
        message_body        TEXT NULL,
        frequency           ENUM(''once'',''daily'',''weekly'',''monthly'') NOT NULL,
        send_time           TIME NULL,
        send_datetime       DATETIME NULL,
        day_of_week         TINYINT NULL,
        day_of_month        TINYINT NULL,
        start_date          DATE NULL,
        end_date            DATE NULL,
        is_active           TINYINT(1) NOT NULL DEFAULT 1,
        next_run_at         DATETIME NULL,
        last_run_at         DATETIME NULL,
        last_run_status     ENUM(''sent'',''failed'') NULL,
        last_run_error      VARCHAR(500) NULL,
        created_by          BIGINT UNSIGNED NOT NULL,
        created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        CONSTRAINT fk_scheduled_reports_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        CONSTRAINT fk_scheduled_reports_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT,
        INDEX idx_scheduled_reports_next_run (is_active, next_run_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0096 complete.' AS status;
