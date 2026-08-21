-- Migration 0023: optional external link + optional file on project_documents
--
-- Backs the Design tab's document list (Document / File Name / Date /
-- Link, full CRUD): a row can now be a plain external URL (e.g. a
-- shared drive or cloud folder) with no uploaded file at all, an
-- uploaded file with no link, or both -- storage_key/original_filename/
-- file_size_bytes widen from NOT NULL to NULL for this reason.
-- document_service.create_document requires at least one of file/
-- external_link at the application layer; the DB just needs to allow it.
--
-- Idempotent -- guarded by information_schema checks, same convention
-- as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0023_document_external_link.sql

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_documents' AND COLUMN_NAME = 'external_link'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_documents ADD COLUMN external_link VARCHAR(1000) NULL AFTER file_size_bytes',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- MODIFY COLUMN is naturally idempotent -- re-running the same
-- nullability against a column that already has it is a safe no-op.
ALTER TABLE project_documents MODIFY COLUMN storage_key VARCHAR(300) NULL;
ALTER TABLE project_documents MODIFY COLUMN original_filename VARCHAR(255) NULL;
ALTER TABLE project_documents MODIFY COLUMN file_size_bytes BIGINT UNSIGNED NULL;

SELECT 'Migration 0023 complete.' AS status;
