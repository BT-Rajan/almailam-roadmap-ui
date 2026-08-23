-- Migration 0028: payment_obligations reminder tracking -- three nullable
-- timestamps, one per reminder point (2 days before due, on the due date,
-- 2 days after), each set the first time that reminder is sent so the
-- daily scheduler job never sends the same reminder twice. Mirrors
-- projects.stale_notified_at's idempotency convention (see
-- project_service.check_and_notify_stale_projects). A reminder is never
-- sent at all once payment_obligations.date_paid is set -- "payment
-- confirmation has arrived" -- so no fourth "stop" column is needed.
--
-- Idempotent -- guarded by an information_schema check, same convention
-- as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0028_payment_reminder_tracking.sql

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'payment_obligations' AND COLUMN_NAME = 'reminder_before_sent_at'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE payment_obligations ADD COLUMN reminder_before_sent_at DATETIME NULL AFTER notes',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'payment_obligations' AND COLUMN_NAME = 'reminder_due_sent_at'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE payment_obligations ADD COLUMN reminder_due_sent_at DATETIME NULL AFTER reminder_before_sent_at',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'payment_obligations' AND COLUMN_NAME = 'reminder_after_sent_at'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE payment_obligations ADD COLUMN reminder_after_sent_at DATETIME NULL AFTER reminder_due_sent_at',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0028 complete.' AS status;

-- Widen notifications.category to add 'Payment' for the reminder job
-- above. MySQL/MariaDB ALTER ... MODIFY on an ENUM is safe to re-run --
-- setting a column to the same definition it already has is a no-op,
-- so no information_schema guard is needed here the way the ADD COLUMN
-- statements above need one.
ALTER TABLE notifications MODIFY COLUMN category ENUM('Project','Task','Government','Payment','AI','System') NOT NULL;

SELECT 'Migration 0028 (notification category) complete.' AS status;
