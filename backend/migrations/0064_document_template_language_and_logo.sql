-- Migration 0064: lets a Quotation/Contract document type have TWO
-- defaults at once -- one English, one Arabic -- instead of a single
-- shared default regardless of the template's actual language (which is
-- also what let an English template get force-rendered right-to-left
-- with an Arabic font by render_quotation_pdf/render_contract_pdf; the
-- PDF now reads this same language column to pick direction/font
-- instead of assuming Arabic always). Also adds a company-wide logo,
-- insertable into any template via the new {{ logo }} merge field (see
-- document_template_service.MERGE_FIELD_CATALOG / _render_docx).
--
-- Idempotent -- guarded by information_schema checks, same convention
-- as every other migration here (install.sh reapplies every migration
-- file on every run with no tracking of what already ran).
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0064_document_template_language_and_logo.sql

SET @db := DATABASE();

SET @template_language_col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'document_templates' AND column_name = 'language'
);
SET @sql := IF(@template_language_col_exists = 0,
    "ALTER TABLE document_templates
        ADD COLUMN language ENUM('English','Arabic') NOT NULL DEFAULT 'English' AFTER document_type",
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @logo_col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'company_settings' AND column_name = 'logo_storage_key'
);
SET @sql := IF(@logo_col_exists = 0,
    "ALTER TABLE company_settings
        ADD COLUMN logo_storage_key VARCHAR(300) NULL,
        ADD COLUMN logo_original_filename VARCHAR(255) NULL",
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0064 complete.' AS status;
