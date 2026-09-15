-- Migration 0102: remove notes/terms_and_conditions/scope_phases/
-- payment_terms from quotations.
--
-- These were free-text fields on the quotation creation/edit forms
-- (QuotationCreatePage.vue / QuotationPreview.vue) that fed the
-- Quotation document template's own "Notes"/"Terms & Conditions"/
-- "Scope Phases"/"Payment Terms" merge fields (see
-- document_template_service.MERGE_FIELD_CATALOG). Determined redundant
-- and removed from the UI -- the corresponding merge-field definitions
-- are removed too so they're no longer offered for new template
-- mappings, but the render context still supplies static empty
-- defaults for these exact keys (rather than removing them outright)
-- so a document template some admin already mapped one of these
-- tokens into still renders instead of raising an undefined-variable
-- error at merge time.
--
-- Idempotent -- each DROP COLUMN is guarded by an information_schema
-- check, same convention as every other migration here (e.g. migration
-- 0094).
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0102_remove_quotation_notes_terms_scope_payment.sql

SET @db := DATABASE();

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'quotations' AND column_name = 'notes'
);
SET @sql := IF(@col_exists > 0,
    'ALTER TABLE quotations DROP COLUMN notes, DROP COLUMN terms_and_conditions, DROP COLUMN scope_phases, DROP COLUMN payment_terms',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0102 complete.' AS status;
