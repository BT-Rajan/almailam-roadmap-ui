-- Migration 0083: remove Project.required_permit_documents
--
-- This was the "permits the client already confirmed they hold, as a
-- checklist of documents to upload" concept from the original New
-- Project Wizard -- there has been no wizard step to populate it for a
-- long time (the wizard's Permits step is now ServicePickerDialog's
-- "Permits to Apply For" section, which is a different thing: permits
-- this project still needs to apply for, tracked via
-- ProjectSelectedPermit -- see permit_selection.py). Nothing writes
-- this column anymore, so ProjectDocumentsTab.vue's "Required Permit
-- Documents" checklist (permitChecklist) was permanently empty for
-- every project; both the column and that checklist UI are removed
-- together.
--
-- Idempotent -- guarded by an information_schema check, same
-- convention as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0083_remove_required_permit_documents.sql

SET @db := DATABASE();

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'projects' AND column_name = 'required_permit_documents'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE projects DROP COLUMN required_permit_documents', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0083 complete.' AS status;
