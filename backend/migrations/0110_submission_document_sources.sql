-- Migration 0110: Reuse documents already on file for a permit application
--
-- A required-documents checklist entry can now be satisfied by pointing at
-- a document the firm already holds instead of uploading it again:
-- a project document, a client document (owner Civil ID ...), a project
-- link document (Property / Government ... links), or a file already
-- attached to another application on the same project. The file is not
-- copied -- the entry reuses the same stored file (or link).
--
--   source_type   -- which kind of document it came from (NULL = uploaded
--                    directly against this entry)
--   source_id     -- that document's id (not a FK: it points at one of
--                    four tables; the file/link is snapshotted on the row,
--                    so the entry stays valid if the source is removed)
--   external_link -- set instead of storage_key when the source is a link
--
-- Idempotent (information_schema guards), same convention as 0108/0109.
--
-- Run: mysql -u <user> -p <database> < backend/migrations/0110_submission_document_sources.sql

SET NAMES utf8mb4;
SET @db := DATABASE();

SET @has_col := (SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'submission_documents' AND column_name = 'source_type');
SET @sql := IF(@has_col = 0,
    "ALTER TABLE submission_documents ADD COLUMN source_type ENUM('project','client','link','application') NULL", 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_col := (SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'submission_documents' AND column_name = 'source_id');
SET @sql := IF(@has_col = 0,
    'ALTER TABLE submission_documents ADD COLUMN source_id BIGINT UNSIGNED NULL', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_col := (SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'submission_documents' AND column_name = 'external_link');
SET @sql := IF(@has_col = 0,
    'ALTER TABLE submission_documents ADD COLUMN external_link VARCHAR(1000) NULL', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0110 complete.' AS status;
