-- Migration 0050: fillable form fields, a sample-file attachment, and
-- per-project filed-form tracking for Approvals & Permits
--
-- Government forms gain a `fields` schema (which {{token}}s in the
-- template get a dropdown or radio group instead of a plain text box)
-- and an optional uploaded sample-file attachment admin can check the
-- template/fields against.
--
-- project_form_entries is new: one row per (project, form) actually
-- filled in for that project -- the Approvals & Permits tab's own CRUD
-- record, organized by the form's authority (MEW/KFD/Baladia/...)
-- there. A project can only have one entry per form (unique constraint
-- below).
--
-- Idempotent -- guarded by information_schema checks throughout, same
-- convention as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0050_project_form_entries.sql

SET @db := DATABASE();

-- ---------------------------------------------------------------------------
-- Part 1: government_forms -> fields + sample-file columns
-- ---------------------------------------------------------------------------

SET @exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'government_forms' AND column_name = 'fields'
);
SET @sql := IF(@exists = 0,
    'ALTER TABLE government_forms ADD COLUMN fields JSON NULL AFTER service_tags',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'government_forms' AND column_name = 'sample_file_storage_key'
);
SET @sql := IF(@exists = 0,
    'ALTER TABLE government_forms ADD COLUMN sample_file_storage_key VARCHAR(300) NULL AFTER fields',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'government_forms' AND column_name = 'sample_file_original_filename'
);
SET @sql := IF(@exists = 0,
    'ALTER TABLE government_forms ADD COLUMN sample_file_original_filename VARCHAR(255) NULL AFTER sample_file_storage_key',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'government_forms' AND column_name = 'sample_file_size_bytes'
);
SET @sql := IF(@exists = 0,
    'ALTER TABLE government_forms ADD COLUMN sample_file_size_bytes BIGINT NULL AFTER sample_file_original_filename',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------------------------
-- Part 2: project_form_entries table
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS project_form_entries (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id          BIGINT UNSIGNED NOT NULL,
    form_id             BIGINT UNSIGNED NOT NULL,
    field_values        JSON NOT NULL,
    status              ENUM('Draft','Submitted','Under Review','Comments Received','Approved','Rejected','Withdrawn') NOT NULL DEFAULT 'Draft',
    document_id         BIGINT UNSIGNED NULL,
    created_by           BIGINT UNSIGNED NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_project_form_entries_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_project_form_entries_form FOREIGN KEY (form_id) REFERENCES government_forms(id) ON DELETE RESTRICT,
    CONSTRAINT fk_project_form_entries_document FOREIGN KEY (document_id) REFERENCES project_documents(id) ON DELETE SET NULL,
    CONSTRAINT fk_project_form_entries_user FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT uq_project_form_entries_project_form UNIQUE (project_id, form_id),
    INDEX idx_project_form_entries_project (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SELECT 'Migration 0050 complete.' AS status;
