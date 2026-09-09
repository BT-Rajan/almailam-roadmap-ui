-- Migration 0087: document-template letterhead/layout settings, plus
-- permanent version pinning for generated documents.
--
-- Two independent additions:
--
-- 1) document_templates gets a background image (the scanned/exported
--    company letterhead, composited full-bleed behind every page --
--    see document_template_service._docx_to_pdf) and page layout
--    settings (orientation + per-side margins; page_size is kept as a
--    column for future paper sizes even though only 'A4' is offered
--    today). All six columns are optional/defaulted so every existing
--    template row keeps rendering exactly as before until an admin
--    opts in.
--
-- 2) quotations/contracts/projects each get a nullable FK back to the
--    exact document_templates row used to render them, so a template
--    edit/re-upload can never silently change how an already-issued
--    document would come out if reprinted. Populated lazily by
--    document_template_service (pinned once a quotation/contract is
--    finalized, or once a project's Payment Plan is first generated),
--    not backfilled here -- every pre-existing row simply keeps
--    resolving to the type's current default, same as before this
--    migration.
--
-- Idempotent -- guarded by information_schema checks, same convention
-- as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0087_document_template_layout_versioning.sql

SET @db := DATABASE();

-- --- document_templates: background image + page layout -------------

SET @needs_layout_cols := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'document_templates' AND COLUMN_NAME = 'background_storage_key'
);
SET @sql := IF(@needs_layout_cols = 0,
    'ALTER TABLE document_templates
        ADD COLUMN background_storage_key VARCHAR(300) NULL AFTER file_size_bytes,
        ADD COLUMN background_original_filename VARCHAR(255) NULL AFTER background_storage_key,
        ADD COLUMN page_size ENUM(''A4'') NOT NULL DEFAULT ''A4'' AFTER background_original_filename,
        ADD COLUMN orientation ENUM(''Portrait'',''Landscape'') NOT NULL DEFAULT ''Portrait'' AFTER page_size,
        ADD COLUMN margin_top_mm SMALLINT UNSIGNED NOT NULL DEFAULT 25 AFTER orientation,
        ADD COLUMN margin_right_mm SMALLINT UNSIGNED NOT NULL DEFAULT 20 AFTER margin_top_mm,
        ADD COLUMN margin_bottom_mm SMALLINT UNSIGNED NOT NULL DEFAULT 25 AFTER margin_right_mm,
        ADD COLUMN margin_left_mm SMALLINT UNSIGNED NOT NULL DEFAULT 20 AFTER margin_bottom_mm',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- --- quotations: pinned template ------------------------------------

SET @needs_quotation_col := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'quotations' AND COLUMN_NAME = 'document_template_id'
);
SET @sql := IF(@needs_quotation_col = 0,
    'ALTER TABLE quotations
        ADD COLUMN document_template_id BIGINT UNSIGNED NULL AFTER finalized_at,
        ADD CONSTRAINT fk_quotations_document_template FOREIGN KEY (document_template_id)
            REFERENCES document_templates(id) ON DELETE RESTRICT',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- --- contracts: pinned template --------------------------------------

SET @needs_contract_col := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'contracts' AND COLUMN_NAME = 'document_template_id'
);
SET @sql := IF(@needs_contract_col = 0,
    'ALTER TABLE contracts
        ADD COLUMN document_template_id BIGINT UNSIGNED NULL AFTER finalized_at,
        ADD CONSTRAINT fk_contracts_document_template FOREIGN KEY (document_template_id)
            REFERENCES document_templates(id) ON DELETE RESTRICT',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- --- projects: pinned Payment Plan template ---------------------------

SET @needs_project_col := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'projects' AND COLUMN_NAME = 'payment_plan_template_id'
);
SET @sql := IF(@needs_project_col = 0,
    'ALTER TABLE projects
        ADD COLUMN payment_plan_template_id BIGINT UNSIGNED NULL,
        ADD CONSTRAINT fk_projects_payment_plan_template FOREIGN KEY (payment_plan_template_id)
            REFERENCES document_templates(id) ON DELETE RESTRICT',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0087 complete.' AS status;
