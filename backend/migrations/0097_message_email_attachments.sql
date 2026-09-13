-- Migration 0097: real Email sending from the Message Centre --
-- subject + failure reason on message_log, plus a message_attachments
-- table.
--
-- Message Centre's compose modal previously only ever wrote a
-- MessageLogEntry with status hardcoded to 'Sent' -- no email, SMS, or
-- WhatsApp message was ever actually delivered (see
-- message_service.send_message). Email now sends for real over SMTP
-- (see email_service.py, reused from Quotation/Contract's own emailed-
-- document flow) via a dedicated multipart endpoint
-- (POST /api/messages/send-email) that can also attach files. SMS/
-- WhatsApp are unchanged (still simulated, still no subject/
-- attachments) -- see app/models/message.py for the full field
-- documentation.
--
-- Idempotent -- guarded by information_schema checks, same convention
-- as every other migration here (e.g. migration 0096).
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0097_message_email_attachments.sql

SET @db := DATABASE();

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'message_log' AND column_name = 'subject'
);
SET @sql := IF(@col_exists = 0,
    'ALTER TABLE message_log ADD COLUMN subject VARCHAR(300) NULL AFTER template_id',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'message_log' AND column_name = 'error_message'
);
SET @sql := IF(@col_exists = 0,
    'ALTER TABLE message_log ADD COLUMN error_message VARCHAR(500) NULL AFTER status',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @table_exists := (
    SELECT COUNT(*) FROM information_schema.tables
    WHERE table_schema = @db AND table_name = 'message_attachments'
);
SET @sql := IF(@table_exists = 0,
    'CREATE TABLE message_attachments (
        id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        message_log_id      BIGINT UNSIGNED NOT NULL,
        storage_key         VARCHAR(255) NOT NULL,
        original_filename   VARCHAR(255) NOT NULL,
        file_size_bytes     BIGINT UNSIGNED NULL,
        CONSTRAINT fk_message_attachments_log FOREIGN KEY (message_log_id) REFERENCES message_log(id) ON DELETE CASCADE,
        INDEX idx_message_attachments_log (message_log_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0097 complete.' AS status;
