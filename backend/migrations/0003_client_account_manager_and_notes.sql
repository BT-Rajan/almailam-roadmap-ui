-- Migration 0003: client account manager + internal notes
--
-- Adds two new, fully nullable columns to `clients` -- safe to add via
-- ALTER TABLE regardless of existing row count, no backfill needed:
--   account_manager_id: which staff member owns this client relationship
--   notes: free-text internal notes (preferences, risk flags, etc.)
--
-- Idempotent -- each ALTER/constraint add is guarded by an
-- information_schema check, same pattern as migration 0001.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0003_client_account_manager_and_notes.sql

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'clients' AND COLUMN_NAME = 'account_manager_id'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE clients ADD COLUMN account_manager_id BIGINT UNSIGNED NULL AFTER sms_consent',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'clients' AND COLUMN_NAME = 'notes'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE clients ADD COLUMN notes VARCHAR(2000) NULL AFTER account_manager_id',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @fk_exists = (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'clients' AND CONSTRAINT_NAME = 'fk_clients_account_manager'
);
SET @sql = IF(@fk_exists = 0,
  'ALTER TABLE clients ADD CONSTRAINT fk_clients_account_manager FOREIGN KEY (account_manager_id) REFERENCES users(id) ON DELETE SET NULL',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_exists = (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'clients' AND INDEX_NAME = 'idx_clients_account_manager'
);
SET @sql = IF(@idx_exists = 0,
  'CREATE INDEX idx_clients_account_manager ON clients (account_manager_id)',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0003 complete.' AS status;
