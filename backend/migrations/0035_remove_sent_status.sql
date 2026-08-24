-- Migration 0035: remove the "Sent" status from quotations and contracts
--
-- "Sent" was a pure intermediate value with no attached behavior -- no
-- email, no notification, nothing else in the app keyed off it. It was
-- just one value in the generic status picklist (StatusTransitionDialog.vue),
-- auto-selected only because it was the sole option while a quotation
-- or contract sat in Draft. Removing it: Draft now transitions directly
-- to what used to be reachable only via Sent -- quotations to
-- Approved/Rejected/Expired, contracts to Signed. See
-- core/status_transitions.py's own comment on
-- QUOTATION_ALLOWED_TRANSITIONS/CONTRACT_ALLOWED_TRANSITIONS.
--
-- Any row currently sitting at "Sent" is moved to "Draft" first (a real
-- ENUM value can't be dropped while rows still hold it) -- matches the
-- existing semantics of Rejected/Expired already folding back to Draft,
-- and it's the only reachable status that doesn't require picking a
-- business outcome (Approved/Rejected/Signed) on the data's behalf.
--
-- Idempotent -- guarded by an information_schema check on the ENUM
-- definition itself, same convention as 0019 (see 0018's own header
-- comment on why: install.sh has no migration-tracking table and
-- reapplies every file on every run).
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0035_remove_sent_status.sql

UPDATE quotations SET status = 'Draft' WHERE status = 'Sent';
UPDATE contracts SET status = 'Draft' WHERE status = 'Sent';

SET @quotations_need_narrowing = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'quotations' AND COLUMN_NAME = 'status'
    AND COLUMN_TYPE LIKE '%''Sent''%'
);
SET @sql = IF(@quotations_need_narrowing > 0,
  'ALTER TABLE quotations MODIFY COLUMN status ENUM(''Draft'',''Approved'',''Rejected'',''Expired'') NOT NULL DEFAULT ''Draft''',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @contracts_need_narrowing = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'contracts' AND COLUMN_NAME = 'status'
    AND COLUMN_TYPE LIKE '%''Sent''%'
);
SET @sql = IF(@contracts_need_narrowing > 0,
  'ALTER TABLE contracts MODIFY COLUMN status ENUM(''Draft'',''Signed'',''Active'',''Expired'',''Terminated'') NOT NULL DEFAULT ''Draft''',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0035 complete.' AS status;
