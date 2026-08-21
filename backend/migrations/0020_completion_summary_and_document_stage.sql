-- Migration 0020: Completion summary fields + per-stage document tagging
--
-- Two small, unrelated additions bundled here since both are additive,
-- nullable columns with no data to backfill:
--
-- 1. projects.completed_at / projects.completion_notes -- back the
--    Overview tab's Completion summary (planned vs. actual budget,
--    planned vs. actual duration, and a free-text notes box). Budget
--    itself is NOT stored here -- it's derived live from the existing
--    financial_agreements/payments tables (see
--    project_service.get_completion_summary) so it can never drift
--    from what Payments actually shows.
--
-- 2. project_documents.stage_key -- lets a document (e.g. an
--    architectural drawing) be tagged to one of the 5 Project Approval
--    Process stages, so the Process tab can show each stage's own
--    document list with its revision history, instead of every
--    stage showing the same undifferentiated full document list.
--
-- Idempotent -- guarded by information_schema checks, same pattern as
-- migrations 0004/0008-0010/0013/0015/0018.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0020_completion_summary_and_document_stage.sql

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'projects' AND COLUMN_NAME = 'completed_at'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE projects ADD COLUMN completed_at DATETIME NULL AFTER service_total',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'projects' AND COLUMN_NAME = 'completion_notes'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE projects ADD COLUMN completion_notes TEXT NULL AFTER completed_at',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Backfill: a project already sitting at status 'Completed' from before
-- this migration has no completed_at yet -- approximate it from the
-- most recent "Status changed" -> Completed audit log entry rather
-- than leaving it permanently null (which would show as "still in
-- progress" duration on the Completion summary for a project that's
-- actually done). Falls back to updated_at if no such audit entry
-- exists (e.g. audit history was pruned).
UPDATE projects p
LEFT JOIN (
    SELECT entity_id, MAX(changed_at) AS last_changed_at
    FROM audit_log
    WHERE entity_type = 'PROJECT' AND event_label = 'Status changed' AND new_value = 'Completed'
    GROUP BY entity_id
) al ON al.entity_id = p.id
SET p.completed_at = COALESCE(al.last_changed_at, p.updated_at)
WHERE p.status = 'Completed' AND p.completed_at IS NULL;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_documents' AND COLUMN_NAME = 'stage_key'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE project_documents ADD COLUMN stage_key VARCHAR(40) NULL AFTER revision',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0020 complete.' AS status;
