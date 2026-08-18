-- Migration 0005: add "contract" to timeline_event_type
--
-- TIMELINE_EVENT_TYPES was missing "contract" entirely -- stage,
-- document, quotation, and submission all had a dedicated type, but
-- contract creation had nowhere valid to log a timeline event. This
-- widens the enum to add it (adding an enum value is always safe for
-- existing rows, unlike the narrowing case in migration 0002 -- no data
-- migration needed here, just the wider allowed set).
--
-- Idempotent -- MODIFY COLUMN to the same target enum is safe to run
-- more than once.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0005_timeline_event_contract_type.sql

ALTER TABLE project_timeline_events
  MODIFY COLUMN type ENUM('stage','document','quotation','contract','submission','milestone','task','note') NOT NULL;

SELECT 'Migration 0005 complete.' AS status;
