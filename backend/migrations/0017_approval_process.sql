-- Migration 0017: Project Approval Process (new, standalone trial)
--
-- Adds a separate, self-contained 5-step tracker (Documents Signed ->
-- MEW Approval -> Architectural Design Approved by Client -> Submit to
-- Baladia or KFD -> Permit Approved), built deliberately independent
-- of the existing 9-stage current_stage/PROJECT_STAGE_ALLOWED_
-- TRANSITIONS system -- see backend/app/models/approval_process.py's
-- own docstring for the full reasoning. Whether this eventually merges
-- into that system, replaces part of it, or stays independent is an
-- open decision pending client consultation; this migration doesn't
-- touch projects.current_stage or projects.progress in any way.
--
-- Also backfills project_approval_steps for every project that already
-- existed before this migration ran -- without it, every pre-existing
-- project would be stuck with an empty approval-process checklist,
-- since the snapshot only happens inside project_service.create_
-- project's own code path. Same pattern as migration 0016's execution-
-- step backfill.
--
-- Idempotent -- CREATE TABLE IF NOT EXISTS is naturally safe to re-run;
-- both the template seed and the per-project backfill are guarded to
-- only fire where there's genuinely nothing there yet.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0017_approval_process.sql

CREATE TABLE IF NOT EXISTS approval_process_templates (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name                VARCHAR(200) NOT NULL,
    sequence_number     INT NOT NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at          DATETIME NULL,
    INDEX idx_approval_process_templates_sequence (sequence_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS project_approval_steps (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id          BIGINT UNSIGNED NOT NULL,
    name                VARCHAR(200) NOT NULL,
    sequence_number     INT NOT NULL,
    status              ENUM('Pending','Completed') NOT NULL DEFAULT 'Pending',
    completed_at        DATETIME NULL,
    completed_by        BIGINT UNSIGNED NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_project_approval_steps_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_project_approval_steps_completed_by FOREIGN KEY (completed_by) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT uq_project_approval_steps_project_sequence UNIQUE (project_id, sequence_number),
    INDEX idx_project_approval_steps_project (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO approval_process_templates (name, sequence_number)
SELECT * FROM (
    SELECT 'Documents Signed' AS name, 1 AS sequence_number
    UNION ALL SELECT 'MEW Approval', 2
    UNION ALL SELECT 'Architectural Design Approved by Client', 3
    UNION ALL SELECT 'Submit to Baladia or KFD', 4
    UNION ALL SELECT 'Permit Approved', 5
) AS seed
WHERE NOT EXISTS (SELECT 1 FROM approval_process_templates);

-- The status column this originally inserted was dropped by migration
-- 0022 (project_approval_steps became a stage-gate document tracker --
-- a stage counts as complete once storage_key is set, not via a
-- status column). install.sh reapplies every migration file on every
-- run with no tracking of what already ran, so this file executes
-- again on a database that's already past 0022, at which point a
-- hardcoded reference to status would fail with "Unknown column".
-- Branches on whether the column is still there, same as migration
-- 0016's identical fix for project_execution_steps.
SET @has_status = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_approval_steps' AND COLUMN_NAME = 'status'
);
SET @sql = IF(@has_status > 0,
  'INSERT INTO project_approval_steps (project_id, name, sequence_number, status)
   SELECT p.id, t.name, t.sequence_number, ''Pending''
   FROM projects p
   CROSS JOIN approval_process_templates t
   WHERE t.deleted_at IS NULL
     AND NOT EXISTS (SELECT 1 FROM project_approval_steps pas WHERE pas.project_id = p.id)',
  'INSERT INTO project_approval_steps (project_id, name, sequence_number)
   SELECT p.id, t.name, t.sequence_number
   FROM projects p
   CROSS JOIN approval_process_templates t
   WHERE t.deleted_at IS NULL
     AND NOT EXISTS (SELECT 1 FROM project_approval_steps pas WHERE pas.project_id = p.id)'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0017 complete.' AS status;
