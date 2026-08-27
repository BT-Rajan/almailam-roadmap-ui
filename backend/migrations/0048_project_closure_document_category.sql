-- Migration 0048: add "Project Closure" link-document category
--
-- The Completed stage's Documents tab now has a dedicated "Project
-- Closure Docs" sub-tab (completion certificate, handover document,
-- client sign-off, etc) -- reuses the exact same link-document CRUD
-- (project_link_documents, LinkDocumentCard/AddLinkDocumentDialog)
-- already used for Property/Government/Others, just a new category
-- value, not a new table or new UI primitive.
--
-- Idempotent -- guarded by an information_schema check, same
-- convention as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0048_project_closure_document_category.sql

SET @needs_widening := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_link_documents' AND COLUMN_NAME = 'category'
      AND COLUMN_TYPE NOT LIKE '%''Project Closure''%'
);
SET @sql := IF(@needs_widening > 0,
    'ALTER TABLE project_link_documents MODIFY COLUMN category ENUM(''Property'',''Government'',''Others'',''Project Closure'') NOT NULL',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0048 complete.' AS status;
