-- Migration 0103: status_report_images table -- up to 5 photos per
-- site engineer Status Report, each stamped server-side with the
-- engineer's name, project number, and date/time before being saved
-- (see status_report_service.stamp_report_image).
--
-- Idempotent -- guarded by an information_schema check, same convention
-- as every other migration here (e.g. migration 0098's own
-- message_attachments table).
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0103_status_report_images.sql

SET @db := DATABASE();

SET @table_exists := (
    SELECT COUNT(*) FROM information_schema.tables
    WHERE table_schema = @db AND table_name = 'status_report_images'
);
SET @sql := IF(@table_exists = 0,
    'CREATE TABLE status_report_images (
        id                   BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        status_report_id     BIGINT UNSIGNED NOT NULL,
        storage_key          VARCHAR(255) NOT NULL,
        original_filename    VARCHAR(255) NOT NULL,
        file_size_bytes      BIGINT UNSIGNED NOT NULL,
        sequence             INT NOT NULL,
        created_at           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_status_report_images_report FOREIGN KEY (status_report_id) REFERENCES status_reports(id) ON DELETE CASCADE,
        INDEX idx_status_report_images_report (status_report_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0103 complete.' AS status;
