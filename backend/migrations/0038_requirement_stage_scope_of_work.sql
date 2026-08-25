-- Migration 0038: Requirement stage + scope-of-work approval
--
-- Redesigns the first workflow stage (before Quotation):
--
-- 1. Renames the "Enquiry" stage to "Requirement" -- same three-step
--    widen/update/narrow shape as migration 0022's "Review" ->
--    "Execution & Tracking" rename, done in the right order here (widen
--    the ENUM to accept both labels *before* the UPDATE that assigns the
--    new one, then narrow once every row has moved off the old label) so
--    it works under strict SQL mode too.
--
-- 2. Adds project.scope_status ('Draft'/'Approved') plus
--    scope_approved_at/scope_approved_by -- the new Requirement tab's
--    internal approval of the scope-of-work text (project.description,
--    the same field "What the Customer Asked For" / changeScope already
--    read/wrote), which is what now gates the automatic move to
--    "Quotation" (see project_service._assert_stage_exit_criteria).
--
-- 3. Adds project_scope_revisions -- one row per saved scope-of-work
--    change while at the Requirement stage, mirroring quotation_
--    revisions/contract_revisions (revision/revised_at/changed_by/
--    summary), plus an optional attached document (storage_key/
--    original_filename/file_size_bytes, same shape as project_approval_
--    steps' stage-gate document).
--
-- 4. Repoints the execution-checklist stage_key label the same way
--    (project_execution_steps/execution_step_templates), matching
--    migration 0029's plain-VARCHAR relabeling -- no ENUM involved there.
--
-- Idempotent -- guarded by information_schema checks throughout, same
-- convention as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0038_requirement_stage_scope_of_work.sql

-- ---------------------------------------------------------------------------
-- Part 1: rename "Enquiry" -> "Requirement" on projects.current_stage
-- ---------------------------------------------------------------------------

SET @needs_widening = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'projects' AND COLUMN_NAME = 'current_stage'
    AND COLUMN_TYPE NOT LIKE '%''Requirement''%'
);
SET @sql = IF(@needs_widening > 0,
  'ALTER TABLE projects MODIFY COLUMN current_stage
     ENUM(''Enquiry'',''Requirement'',''Quotation'',''Contract'',''Design'',''Government Submission'',''Execution & Tracking'',''Completed'')
     NOT NULL DEFAULT ''Requirement''',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

UPDATE projects SET current_stage = 'Requirement' WHERE current_stage = 'Enquiry';

SET @needs_narrowing = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'projects' AND COLUMN_NAME = 'current_stage'
    AND COLUMN_TYPE LIKE '%''Enquiry''%'
);
SET @sql = IF(@needs_narrowing > 0,
  'ALTER TABLE projects MODIFY COLUMN current_stage
     ENUM(''Requirement'',''Quotation'',''Contract'',''Design'',''Government Submission'',''Execution & Tracking'',''Completed'')
     NOT NULL DEFAULT ''Requirement''',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------------------------
-- Part 2: scope-of-work approval fields on projects
-- ---------------------------------------------------------------------------

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'projects' AND COLUMN_NAME = 'scope_status'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE projects ADD COLUMN scope_status ENUM(''Draft'',''Approved'') NOT NULL DEFAULT ''Draft'' AFTER description',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'projects' AND COLUMN_NAME = 'scope_approved_at'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE projects ADD COLUMN scope_approved_at DATETIME NULL AFTER scope_status',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'projects' AND COLUMN_NAME = 'scope_approved_by'
);
SET @sql = IF(@col_exists = 0,
  'ALTER TABLE projects ADD COLUMN scope_approved_by BIGINT UNSIGNED NULL AFTER scope_approved_at',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @fk_exists = (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'projects'
    AND CONSTRAINT_NAME = 'fk_projects_scope_approved_by'
);
SET @sql = IF(@fk_exists = 0,
  'ALTER TABLE projects ADD CONSTRAINT fk_projects_scope_approved_by
     FOREIGN KEY (scope_approved_by) REFERENCES users(id) ON DELETE SET NULL',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------------------------
-- Part 3: project_scope_revisions -- revision history for the Requirement
-- stage's scope-of-work text (mirrors quotation_revisions/contract_revisions)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS project_scope_revisions (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id          BIGINT UNSIGNED NOT NULL,
    revision            VARCHAR(10) NOT NULL,
    scope_text          TEXT NOT NULL,
    storage_key         VARCHAR(300) NULL,
    original_filename   VARCHAR(255) NULL,
    file_size_bytes     BIGINT UNSIGNED NULL,
    revised_at          DATE NOT NULL,
    changed_by          BIGINT UNSIGNED NOT NULL,
    summary             TEXT NOT NULL,
    CONSTRAINT fk_project_scope_revisions_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_project_scope_revisions_user FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_project_scope_revisions_project (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------------
-- Part 4: repoint the plain-VARCHAR execution-checklist stage_key label
-- (same relabeling as migration 0029, no ENUM involved)
-- ---------------------------------------------------------------------------

UPDATE execution_step_templates SET stage_key = 'Requirement' WHERE stage_key = 'Enquiry';
UPDATE project_execution_steps SET stage_key = 'Requirement' WHERE stage_key = 'Enquiry';

SELECT 'Migration 0038 complete.' AS status;
