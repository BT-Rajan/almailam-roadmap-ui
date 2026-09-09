-- Migration 0086: repair any document_templates rows where more than
-- one template ended up flagged is_default=1 for the same
-- (document_type, language) pair.
--
-- "Exactly one default per (document_type, language)" has only ever
-- been enforced in application code (document_template_service.
-- set_default/upload_template), never as a DB constraint -- MySQL has
-- no partial/filtered unique index to express that (see
-- DocumentTemplate's own docstring). get_default() reads it back with
-- a plain `.first()` and no explicit ordering, so if a duplicate ever
-- existed (a stray row from before upload_template started demoting
-- the previous default on every new upload), which one actually gets
-- used was effectively undefined -- a real, live way for the "active"
-- template to look like the wrong/stale one even after uploading and
-- setting default correctly.
--
-- For each (document_type, language) pair with more than one
-- is_default=1 row, keeps only the most recently created one (highest
-- id) as default and clears the rest. Idempotent -- a clean table (at
-- most one default per pair already) has nothing for this to touch,
-- safe to run repeatedly.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0086_document_template_single_default_repair.sql

UPDATE document_templates dt
JOIN (
    SELECT document_type, language, MAX(id) AS keep_id
    FROM document_templates
    WHERE is_default = 1 AND deleted_at IS NULL
    GROUP BY document_type, language
) keepers
    ON dt.document_type = keepers.document_type AND dt.language = keepers.language
SET dt.is_default = 0
WHERE dt.is_default = 1 AND dt.deleted_at IS NULL AND dt.id <> keepers.keep_id;

SELECT 'Migration 0086 complete.' AS status;
