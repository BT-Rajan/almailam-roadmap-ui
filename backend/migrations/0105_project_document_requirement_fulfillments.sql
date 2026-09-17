-- Migration 0105: project_document_requirement_fulfillments -- per-project
-- checkbox state for a DocumentRequirementLink, making the till-now purely
-- informational Design/Permit/Supervision document checklist
-- (document_requirement_service.py) actually gate something (#4/#5 on the
-- Design-stage tangle pass: (a) closing a Design activity/Permit/
-- Supervision activity to Complete, (b) the project's move into Handover).
--
-- Idempotent -- guarded by information_schema checks, same convention as
-- every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0105_project_document_requirement_fulfillments.sql

SET @db := DATABASE();

SET @table_exists := (
    SELECT COUNT(*) FROM information_schema.tables
    WHERE table_schema = @db AND table_name = 'project_document_requirement_fulfillments'
);
SET @sql := IF(@table_exists = 0,
    "CREATE TABLE project_document_requirement_fulfillments (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
        project_id BIGINT UNSIGNED NOT NULL,
        document_requirement_link_id BIGINT UNSIGNED NOT NULL,
        document_id BIGINT UNSIGNED NULL,
        fulfilled_at DATETIME NULL,
        fulfilled_by BIGINT UNSIGNED NULL,
        CONSTRAINT uq_project_doc_req_fulfillments_target UNIQUE (project_id, document_requirement_link_id),
        CONSTRAINT fk_project_doc_req_fulfillments_project
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
        CONSTRAINT fk_project_doc_req_fulfillments_link
            FOREIGN KEY (document_requirement_link_id) REFERENCES document_requirement_links (id) ON DELETE CASCADE,
        CONSTRAINT fk_project_doc_req_fulfillments_document
            FOREIGN KEY (document_id) REFERENCES project_documents (id) ON DELETE SET NULL,
        CONSTRAINT fk_project_doc_req_fulfillments_user
            FOREIGN KEY (fulfilled_by) REFERENCES users (id) ON DELETE SET NULL,
        INDEX idx_project_doc_req_fulfillments_project (project_id),
        INDEX idx_project_doc_req_fulfillments_link (document_requirement_link_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci",
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0105 complete.' AS status;
