-- Migration 0043: Replace the general-purpose AI assistant, document
-- review, and contract summary features with a single strict
-- knowledgebase Q&A tool -- upload a document, ask questions about it in
-- Arabic/English/mixed, answered only from that document's content.
--
-- Drops document_ai_reviews and ai_prompt_templates (both fed the removed
-- general-assistant/document-review features and are no longer read by
-- any code path). Adds knowledge_documents + knowledge_qa_cache, and
-- extends ai_configuration with knowledgebase settings (system prompt,
-- upload/context size limits) -- the answer-cache TTL reuses the existing
-- cache_duration_minutes column rather than adding a new one.
--
-- Idempotent -- guarded by information_schema checks, same convention as
-- every other migration in this directory.

SET @db := DATABASE();

DROP TABLE IF EXISTS document_ai_reviews;
DROP TABLE IF EXISTS ai_prompt_templates;

CREATE TABLE IF NOT EXISTS knowledge_documents (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    document_no         VARCHAR(20) NOT NULL UNIQUE,
    title               VARCHAR(200) NOT NULL,
    storage_key         VARCHAR(300) NOT NULL,
    original_filename   VARCHAR(255) NOT NULL,
    file_size_bytes     BIGINT UNSIGNED NOT NULL,
    content_type        VARCHAR(20) NOT NULL,
    extracted_text       LONGTEXT NOT NULL,
    char_count          INT UNSIGNED NOT NULL DEFAULT 0,
    truncated           TINYINT(1) NOT NULL DEFAULT 0,
    extraction_ok        TINYINT(1) NOT NULL DEFAULT 1,
    extraction_error     VARCHAR(500) NOT NULL DEFAULT '',
    is_active           TINYINT(1) NOT NULL DEFAULT 1,
    uploaded_by         BIGINT UNSIGNED NOT NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_knowledge_documents_user FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_knowledge_documents_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS knowledge_qa_cache (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    scope_key           VARCHAR(64) NOT NULL,
    question_hash       CHAR(64) NOT NULL,
    question_text       TEXT NOT NULL,
    answer_text         MEDIUMTEXT NOT NULL,
    source_document_ids JSON NOT NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_knowledge_qa_cache_scope_question (scope_key, question_hash),
    INDEX idx_knowledge_qa_cache_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET @exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'ai_configuration' AND column_name = 'kb_system_prompt'
);
SET @sql := IF(@exists = 0,
    'ALTER TABLE ai_configuration ADD COLUMN kb_system_prompt TEXT NULL',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'ai_configuration' AND column_name = 'kb_max_upload_size_mb'
);
SET @sql := IF(@exists = 0,
    'ALTER TABLE ai_configuration ADD COLUMN kb_max_upload_size_mb INT UNSIGNED NOT NULL DEFAULT 20',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'ai_configuration' AND column_name = 'kb_max_document_chars'
);
SET @sql := IF(@exists = 0,
    'ALTER TABLE ai_configuration ADD COLUMN kb_max_document_chars INT UNSIGNED NOT NULL DEFAULT 60000',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'ai_configuration' AND column_name = 'kb_max_context_chars'
);
SET @sql := IF(@exists = 0,
    'ALTER TABLE ai_configuration ADD COLUMN kb_max_context_chars INT UNSIGNED NOT NULL DEFAULT 150000',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0043 complete.' AS status;
