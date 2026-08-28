-- Migration 0053: remove quotation tax and the lettered-template
-- feature from quotations and contracts
--
-- Quotations: drops tax_rate_percent outright -- a quotation's amount
-- is now simply subtotal minus discount, no tax applied. Any stored
-- amount computed with the old formula is left as-is (historical data,
-- not recalculated).
--
-- Quotations + Contracts: drops the lettered-template fields (the
-- Design & Permits / Supervision Arabic and bilingual letter formats
-- and everything specific to them -- template_key, addressee/subject
-- lines, fee frequency, scope/payment bullet lists). Every quotation
-- and contract is the itemised/clause-based kind from here on.
-- Contracts' client_representative is NOT touched -- it's a base field
-- used by both flavours (see the Contract model docstring and
-- search_service.py, which searches on it), not a lettered-only one.
--
-- finalized_at and the Draft->Final lock it backs are NOT touched on
-- either table -- that mechanism already applies to every quotation/
-- contract regardless of format, not just the lettered ones.
--
-- Idempotent -- guarded by information_schema checks throughout, same
-- convention as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0053_remove_quotation_tax_and_lettered_templates.sql

SET @db := DATABASE();

-- ---------------------------------------------------------------------------
-- Part 1: quotations -- drop tax_rate_percent and lettered-template columns
-- ---------------------------------------------------------------------------

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'quotations' AND column_name = 'tax_rate_percent'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE quotations DROP COLUMN tax_rate_percent', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'quotations' AND column_name = 'template_key'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE quotations DROP COLUMN template_key', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'quotations' AND column_name = 'client_representative'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE quotations DROP COLUMN client_representative', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'quotations' AND column_name = 'subject_line'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE quotations DROP COLUMN subject_line', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'quotations' AND column_name = 'project_reference'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE quotations DROP COLUMN project_reference', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'quotations' AND column_name = 'fee_frequency'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE quotations DROP COLUMN fee_frequency', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'quotations' AND column_name = 'scope_items'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE quotations DROP COLUMN scope_items', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'quotations' AND column_name = 'payment_terms'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE quotations DROP COLUMN payment_terms', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------------------------
-- Part 2: contracts -- drop lettered-template columns (client_representative stays)
-- ---------------------------------------------------------------------------

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'contracts' AND column_name = 'template_key'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE contracts DROP COLUMN template_key', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'contracts' AND column_name = 'is_bilingual'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE contracts DROP COLUMN is_bilingual', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'contracts' AND column_name = 'subject_line_ar'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE contracts DROP COLUMN subject_line_ar', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'contracts' AND column_name = 'subject_line_en'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE contracts DROP COLUMN subject_line_en', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'contracts' AND column_name = 'project_reference'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE contracts DROP COLUMN project_reference', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'contracts' AND column_name = 'fee_frequency'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE contracts DROP COLUMN fee_frequency', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'contracts' AND column_name = 'scope_items_ar'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE contracts DROP COLUMN scope_items_ar', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'contracts' AND column_name = 'scope_items_en'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE contracts DROP COLUMN scope_items_en', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'contracts' AND column_name = 'payment_terms_ar'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE contracts DROP COLUMN payment_terms_ar', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'contracts' AND column_name = 'payment_terms_en'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE contracts DROP COLUMN payment_terms_en', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0053 complete.' AS status;
