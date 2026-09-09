-- Migration 0085: add "Payment Plan" as a third document_templates.
-- document_type, alongside Quotation and Contract
--
-- The Payment Plan page now generates a single merged PDF (template +
-- company logo) the same way Quotation/Contract already do -- an
-- Administrator uploads and field-maps a .docx template for it under
-- Administration > Documents, per language, same as the other two
-- types.
--
-- Widening an ENUM (adding a value) needs no data reassignment first,
-- unlike narrowing one -- every existing row's value is still valid
-- under the new, larger set.
--
-- Idempotent -- guarded by an information_schema check, same convention
-- as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0085_payment_plan_document_template.sql

SET @db := DATABASE();

SET @needs_widening := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'document_templates' AND COLUMN_NAME = 'document_type'
        AND COLUMN_TYPE NOT LIKE '%''Payment Plan''%'
);
SET @sql := IF(@needs_widening > 0,
    'ALTER TABLE document_templates MODIFY COLUMN document_type ENUM(''Quotation'',''Contract'',''Payment Plan'') NOT NULL',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0085 complete.' AS status;
