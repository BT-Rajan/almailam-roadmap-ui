-- Brings an EXISTING database up to backend/schema.sql. install.sh runs it
-- on every install against a non-empty database (a fresh one gets schema.sql
-- itself). Every statement must be idempotent (MariaDB IF [NOT] EXISTS), so
-- re-running it is a no-op. When schema.sql gains a column or index, add the
-- matching statement here in the same commit.

-- clients.mobile_digits: mobile with non-digits removed, used by the
-- duplicate-client check (app/models/client.py keeps it in step on save).
ALTER TABLE clients
    ADD COLUMN IF NOT EXISTS mobile_digits VARCHAR(30) NOT NULL DEFAULT '' AFTER mobile;
UPDATE clients
    SET mobile_digits = REGEXP_REPLACE(mobile, '[^0-9]', '')
    WHERE mobile_digits <> REGEXP_REPLACE(mobile, '[^0-9]', '');
ALTER TABLE clients
    ADD INDEX IF NOT EXISTS idx_clients_mobile_digits (mobile_digits);

-- Indexes that gained a column: rebuilt only while they still have the old
-- column count (one ALTER, so a foreign key relying on it is never left bare).

-- Notification drawer: unread + newest read, per user.
SET @stmt = IF(
    (SELECT COUNT(*) FROM information_schema.statistics
      WHERE table_schema = DATABASE() AND table_name = 'notifications' AND index_name = 'idx_notifications_user_read') = 3,
    'DO 0',
    'ALTER TABLE notifications DROP INDEX IF EXISTS idx_notifications_user_read, ADD INDEX idx_notifications_user_read (user_id, `read`, created_at)');
PREPARE stmt FROM @stmt; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Message log: per-client history newest first, and the global list by date.
SET @stmt = IF(
    (SELECT COUNT(*) FROM information_schema.statistics
      WHERE table_schema = DATABASE() AND table_name = 'message_log' AND index_name = 'idx_message_log_client') = 2,
    'DO 0',
    'ALTER TABLE message_log DROP INDEX IF EXISTS idx_message_log_client, ADD INDEX idx_message_log_client (client_id, sent_at)');
PREPARE stmt FROM @stmt; EXECUTE stmt; DEALLOCATE PREPARE stmt;
ALTER TABLE message_log
    ADD INDEX IF NOT EXISTS idx_message_log_sent_at (sent_at);

-- Project timeline: stage events per project.
ALTER TABLE project_timeline_events
    ADD INDEX IF NOT EXISTS idx_project_timeline_events_stage (project_id, type, created_at);
