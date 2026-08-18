-- Migration 0007: client document version history
--
-- Client documents previously had no version history at all -- replacing
-- a file via the "Replace File" action just bumped the version number
-- and overwrote storage_key in place. The old file was never actually
-- deleted from disk, but there was no way to ever recover or even see
-- it again through the app once replaced. This adds the same real
-- version-history table project documents already have
-- (document_versions), and backfills an initial version row for every
-- existing client document, matching migration 0006's approach for
-- project documents.
--
-- Idempotent -- the CREATE TABLE IF NOT EXISTS is naturally safe to
-- re-run, and the backfill INSERT is guarded the same way 0006's is:
-- once a document has any version row, it's excluded from being
-- backfilled again.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0007_client_document_versions.sql

CREATE TABLE IF NOT EXISTS client_document_versions (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    document_id         BIGINT UNSIGNED NOT NULL,
    version             INT UNSIGNED NOT NULL,
    uploaded_by         BIGINT UNSIGNED NOT NULL,
    upload_date         DATETIME NOT NULL,
    notes               VARCHAR(500) NOT NULL DEFAULT '',
    storage_key         VARCHAR(255) NOT NULL,
    original_filename   VARCHAR(255) NOT NULL,
    file_size_bytes     BIGINT UNSIGNED NOT NULL DEFAULT 0,
    CONSTRAINT fk_client_document_versions_document FOREIGN KEY (document_id) REFERENCES client_documents(id) ON DELETE CASCADE,
    CONSTRAINT fk_client_document_versions_user FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_client_document_versions_document (document_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO client_document_versions (document_id, version, uploaded_by, upload_date, notes, storage_key, original_filename, file_size_bytes)
SELECT cd.id, cd.version, cd.uploaded_by, cd.upload_date, 'Initial upload (backfilled).', cd.storage_key, cd.original_filename, cd.file_size_bytes
FROM client_documents cd
LEFT JOIN client_document_versions cdv ON cdv.document_id = cd.id
WHERE cdv.id IS NULL AND cd.storage_key != '';

SELECT 'Migration 0007 complete.' AS status;
