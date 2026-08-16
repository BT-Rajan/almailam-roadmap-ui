-- Migration 0001: client-module schema updates
--
-- This repo has no migration framework -- schema.sql is normally the only
-- source of truth, updated in place, with the assumption that anyone with
-- an existing database just recreates it via install.sh's fresh-DB mode.
-- That assumption broke for any live/shared instance with real data: the
-- backend code was updated (new columns referenced in queries) but the
-- database itself never was, causing "Unknown column" errors on every
-- request that touches the client module -- e.g. opening a client's
-- workspace page 500s immediately, because loadClientDetail() fetches
-- documents/contacts/addresses/identifications/verifications in parallel
-- and every one of those queries now references a column that doesn't
-- exist yet on an un-migrated database.
--
-- This script is idempotent (safe to run more than once) and safe to run
-- against a database that already has real rows in these tables -- it
-- backfills sane defaults for the two NOT NULL columns that have no
-- built-in default (storage_key, original_filename) rather than failing
-- the ALTER outright.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0001_client_module_schema_updates.sql

-- --- client_documents: real file storage columns (added when client
-- document uploads were fixed to actually save the uploaded file instead
-- of discarding it) plus soft-delete -----------------------------------

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'client_documents' AND COLUMN_NAME = 'storage_key'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE client_documents ADD COLUMN storage_key VARCHAR(255) NOT NULL DEFAULT \'\' AFTER upload_date',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'client_documents' AND COLUMN_NAME = 'original_filename'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE client_documents ADD COLUMN original_filename VARCHAR(255) NOT NULL DEFAULT \'\' AFTER storage_key',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'client_documents' AND COLUMN_NAME = 'file_size_bytes'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE client_documents ADD COLUMN file_size_bytes BIGINT UNSIGNED NOT NULL DEFAULT 0 AFTER original_filename',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'client_documents' AND COLUMN_NAME = 'deleted_at'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE client_documents ADD COLUMN deleted_at DATETIME NULL',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Any existing document rows now have storage_key='' / original_filename=''
-- because they were uploaded before file storage actually worked -- there
-- is no real file on disk to point them at. Flag them clearly instead of
-- leaving a blank filename in the UI.
UPDATE client_documents
SET original_filename = 'legacy-upload (no file on record)'
WHERE storage_key = '' AND original_filename = '';

-- --- client_verifications: link to a specific document ----------------

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'client_verifications' AND COLUMN_NAME = 'document_id'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE client_verifications ADD COLUMN document_id BIGINT UNSIGNED NULL AFTER client_id, ADD CONSTRAINT fk_client_verifications_document FOREIGN KEY (document_id) REFERENCES client_documents(id) ON DELETE SET NULL',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- --- soft-delete columns: client_contacts, client_addresses,
-- client_identifications -------------------------------------------------

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'client_contacts' AND COLUMN_NAME = 'deleted_at'
);
SET @sql = IF(@col_exists = 0, 'ALTER TABLE client_contacts ADD COLUMN deleted_at DATETIME NULL', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'client_addresses' AND COLUMN_NAME = 'deleted_at'
);
SET @sql = IF(@col_exists = 0, 'ALTER TABLE client_addresses ADD COLUMN deleted_at DATETIME NULL', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'client_identifications' AND COLUMN_NAME = 'deleted_at'
);
SET @sql = IF(@col_exists = 0, 'ALTER TABLE client_identifications ADD COLUMN deleted_at DATETIME NULL', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- --- Clients permission module -----------------------------------------
-- No schema change needed here -- ROLE_PERMISSIONS lives in
-- backend/app/core/permissions.py, not the database, so a restart of the
-- backend process picks it up automatically.

SELECT 'Migration 0001 complete.' AS status;
