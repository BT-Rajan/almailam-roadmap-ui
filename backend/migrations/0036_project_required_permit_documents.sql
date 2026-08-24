-- Migration 0036: persist the "permits the client already holds" the
-- New Project Wizard's Permits step collects.
--
-- The wizard has sent this as `requiredPermitDocuments` since it was
-- built, but nothing on the backend ever accepted, stored, or returned
-- it -- Pydantic silently drops unrecognized fields by default, so the
-- mandatory-upload checklist staff set up at project creation
-- (ProjectDocumentsTab.vue's permitChecklist) never actually existed
-- for any project. This column is what actually makes it real.
--
-- Added nullable first, backfilled to an empty list, then narrowed to
-- NOT NULL -- same three-step shape as 0026's scope_items/payment_terms
-- JSON columns, rather than an ALTER ... DEFAULT (JSON_ARRAY()) in one
-- step.
--
-- Idempotent -- guarded by an information_schema check, same pattern
-- as 0034. Safe to re-run, including against a database install.sh has
-- already applied this to.
--
-- Run:
--   mysql -u <user> -p <database> < backend/migrations/0036_project_required_permit_documents.sql

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'projects' AND COLUMN_NAME = 'required_permit_documents'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE projects ADD COLUMN required_permit_documents JSON NULL AFTER service_total',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

UPDATE projects SET required_permit_documents = JSON_ARRAY() WHERE required_permit_documents IS NULL;
ALTER TABLE projects MODIFY COLUMN required_permit_documents JSON NOT NULL;

SELECT 'Migration 0036 complete.' AS status;
