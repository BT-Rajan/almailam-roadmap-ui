-- Migration 0006: backfill missing initial document version rows
--
-- Before this fix, create_document() never inserted a matching
-- DocumentVersion row for the initial upload -- only add_version()
-- retroactively created one, and only when/if a document was ever
-- revised a second time. Any document created under the old code that
-- has never been revised has ZERO rows in document_versions, even
-- though it unambiguously has one real, current version.
--
-- This backfills exactly those documents (and only those -- anything
-- that already has version history, from being revised under the old
-- code, is left alone) with a version row matching their current file.
--
-- Idempotent -- the LEFT JOIN ... WHERE dv.id IS NULL condition means
-- once a document has any version row (from this backfill or a real
-- revision), it's excluded from being backfilled again.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0006_backfill_document_versions.sql

INSERT INTO document_versions (document_id, revision, uploaded_by, upload_date, notes, storage_key, original_filename, file_size_bytes)
SELECT pd.id, pd.revision, pd.uploaded_by, pd.upload_date, 'Initial upload (backfilled).', pd.storage_key, pd.original_filename, pd.file_size_bytes
FROM project_documents pd
LEFT JOIN document_versions dv ON dv.document_id = pd.id
WHERE dv.id IS NULL;

SELECT 'Migration 0006 complete.' AS status;
