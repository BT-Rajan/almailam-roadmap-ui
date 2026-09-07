-- Migration 0078: a new idempotency guard column,
-- payment_obligations.client_reminder_sent_at, for the client-facing
-- "payment due in 2 days" email (see
-- payment_service.check_and_notify_payment_reminders). Deliberately
-- separate from reminder_before_sent_at, which already guards the
-- internal Engineer notification at the same -2-day point -- keeping
-- them apart means neither audience's delivery state depends on the
-- other's (e.g. a project with no Engineer assigned still gets its
-- client reminder emailed on schedule).
--
-- Idempotent -- guarded by an information_schema check, same convention
-- as every other additive migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0078_payment_client_reminder.sql

SET @db := DATABASE();

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'payment_obligations' AND column_name = 'client_reminder_sent_at'
);
SET @sql := IF(@col_exists = 0,
    'ALTER TABLE payment_obligations ADD COLUMN client_reminder_sent_at DATETIME NULL AFTER reminder_after_sent_at',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0078 complete.' AS status;
