-- Migration 0057: Quotation/Contract document templates.
--
-- Administrators can now upload a .docx template per document type
-- (Quotation, Contract) under Administration > Documents, and mark one
-- as the default -- the one used when a project's Quotation/Contract
-- tab generates the actual merged document. Storage follows the same
-- convention as every other upload in this app (storage_key/
-- original_filename/file_size_bytes, see file_storage.save_upload);
-- is_default is enforced exclusive-per-document_type in
-- document_template_service.set_default, not by a DB constraint (MySQL
-- has no partial/filtered unique index to express "at most one default
-- per document_type").
--
-- Idempotent -- guarded by information_schema checks, same convention as
-- every other migration in this directory.

CREATE TABLE IF NOT EXISTS document_templates (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    document_type       ENUM('Quotation','Contract') NOT NULL,
    storage_key         VARCHAR(300) NOT NULL,
    original_filename   VARCHAR(255) NOT NULL,
    file_size_bytes     BIGINT UNSIGNED NOT NULL,
    is_default          TINYINT(1) NOT NULL DEFAULT 0,
    uploaded_by         BIGINT UNSIGNED NOT NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at          DATETIME NULL,
    CONSTRAINT fk_document_templates_user FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_document_templates_type (document_type, is_default)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SELECT 'Migration 0057 complete.' AS status;
