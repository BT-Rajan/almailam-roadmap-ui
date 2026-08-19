-- Migration 0011: project link documents (Property / Government / Others)
--
-- The project Documents tab previously only had one flat, upload-based
-- document list. This adds a second, lightweight table for documents that
-- live outside the app -- a shared drive, a government portal, a scanned
-- copy on the office server -- where only a name, category, and path/link
-- back to the file is recorded, not an uploaded file itself. "Customer ID"
-- documents (the fourth category shown in the same tab) are NOT part of
-- this table -- those are read-only, sourced from the client's own
-- onboarding documents (client_documents).
--
-- Idempotent -- the CREATE TABLE IF NOT EXISTS is naturally safe to
-- re-run, same pattern as migration 0007.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0011_project_link_documents.sql

CREATE TABLE IF NOT EXISTS project_link_documents (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    link_document_no    VARCHAR(20) NOT NULL UNIQUE,
    project_id          BIGINT UNSIGNED NOT NULL,
    category            ENUM('Property','Government','Others') NOT NULL,
    name                VARCHAR(200) NOT NULL,
    path                VARCHAR(1000) NOT NULL,
    added_by            BIGINT UNSIGNED NOT NULL,
    added_date          DATE NOT NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at          DATETIME NULL,
    CONSTRAINT fk_project_link_documents_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_project_link_documents_user FOREIGN KEY (added_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_project_link_documents_project (project_id),
    INDEX idx_project_link_documents_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SELECT 'Migration 0011 complete.' AS status;
