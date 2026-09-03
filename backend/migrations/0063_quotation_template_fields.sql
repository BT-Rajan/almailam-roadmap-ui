-- Migration 0063: adds the data a Quotation document template actually
-- needs to fully merge -- a project site/plot address, and two more
-- free-text repeating fields on the quotation itself (scope broken into
-- phases, and a payment-terms breakdown), mirroring the existing
-- terms_and_conditions column. Without these, an uploaded Quotation
-- template with placeholders for a project address, phased scope, or a
-- payment schedule had no data to bind them to (see
-- document_template_service.MERGE_FIELD_CATALOG).
--
-- Idempotent -- guarded by information_schema checks, same convention
-- as every other migration here (install.sh reapplies every migration
-- file on every run with no tracking of what already ran).
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0063_quotation_template_fields.sql

SET @db := DATABASE();

SET @site_address_col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'projects' AND column_name = 'site_address'
);
SET @sql := IF(@site_address_col_exists = 0,
    "ALTER TABLE projects ADD COLUMN site_address VARCHAR(300) NULL AFTER description",
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @scope_phases_col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'quotations' AND column_name = 'scope_phases'
);
SET @sql := IF(@scope_phases_col_exists = 0,
    "ALTER TABLE quotations ADD COLUMN scope_phases JSON NOT NULL DEFAULT (JSON_ARRAY()) AFTER terms_and_conditions",
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @payment_terms_col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'quotations' AND column_name = 'payment_terms'
);
SET @sql := IF(@payment_terms_col_exists = 0,
    "ALTER TABLE quotations ADD COLUMN payment_terms JSON NOT NULL DEFAULT (JSON_ARRAY()) AFTER scope_phases",
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0063 complete.' AS status;
