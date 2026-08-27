-- Migration 0051: remove the "Execution & Tracking" / "Completed" stages
-- and the 5-gate Approval Process entirely
--
-- Full removal, per the decision behind this migration: the project
-- workflow now ends at "Government Submission" (5 stages instead of 7),
-- there is no more "Completed" project status at all (a project stays
-- Active/On Hold/Cancelled for its whole life), and the 5-gate Approval
-- Process (Documents Signed/MEW Approval/Architectural Approval/Submit
-- Baladia-KFD/Permit Approved) is dropped along with it -- 3 of its
-- gates existed to feed the now-removed Execution & Tracking stage, and
-- the Approvals & Permits authority-filing system (government_
-- submissions/project_form_entries) already covers real authority
-- filing without it.
--
-- Irreversible: this drops tables and columns outright, not just stops
-- using them (matches every "no dead columns/tables left behind"
-- migration before it -- 0018, 0022). Existing data in a dropped ENUM
-- value is reassigned before the ALTER (a real ENUM value can't be
-- dropped while rows still hold it, same approach as migrations 0019
-- and 0022):
--   - current_stage 'Execution & Tracking'/'Completed' -> 'Government
--     Submission', the new terminal stage.
--   - status 'Completed' -> 'Active' -- there is no replacement
--     "finished" state; a project that was Completed simply has no
--     completion status to hold any more.
--
-- Idempotent -- guarded by information_schema checks throughout, same
-- convention as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0051_remove_execution_tracking_and_completed.sql

SET @db := DATABASE();

-- ---------------------------------------------------------------------------
-- Part 1: reassign data out of the ENUM values about to be dropped
-- ---------------------------------------------------------------------------

UPDATE projects SET current_stage = 'Government Submission' WHERE current_stage IN ('Execution & Tracking', 'Completed');
UPDATE projects SET status = 'Active' WHERE status = 'Completed';

-- ---------------------------------------------------------------------------
-- Part 2: projects -> drop step_set_id (+ its FK) and the completion columns
-- ---------------------------------------------------------------------------

SET @constraint_exists := (
    SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
    WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'projects' AND CONSTRAINT_NAME = 'fk_projects_step_set'
);
SET @sql := IF(@constraint_exists > 0,
    'ALTER TABLE projects DROP FOREIGN KEY fk_projects_step_set',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'projects' AND column_name = 'step_set_id'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE projects DROP COLUMN step_set_id', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'projects' AND column_name = 'completed_at'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE projects DROP COLUMN completed_at', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'projects' AND column_name = 'completion_notes'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE projects DROP COLUMN completion_notes', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'projects' AND column_name = 'deviation_notes'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE projects DROP COLUMN deviation_notes', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------------------------
-- Part 3: projects -> shrink current_stage and status ENUMs
-- ---------------------------------------------------------------------------

SET @needs_narrowing := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'projects' AND COLUMN_NAME = 'current_stage'
        AND (COLUMN_TYPE LIKE '%''Execution & Tracking''%' OR COLUMN_TYPE LIKE '%''Completed''%')
);
SET @sql := IF(@needs_narrowing > 0,
    'ALTER TABLE projects MODIFY COLUMN current_stage ENUM(''Requirement'',''Quotation'',''Contract'',''Design'',''Government Submission'') NOT NULL DEFAULT ''Requirement''',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @needs_narrowing := (
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'projects' AND COLUMN_NAME = 'status'
        AND COLUMN_TYPE LIKE '%''Completed''%'
);
SET @sql := IF(@needs_narrowing > 0,
    'ALTER TABLE projects MODIFY COLUMN status ENUM(''Active'',''On Hold'',''Cancelled'') NOT NULL DEFAULT ''Active''',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------------------------
-- Part 4: drop the scope-tracking is_complete flags
-- ---------------------------------------------------------------------------

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'project_selected_activities' AND column_name = 'is_complete'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE project_selected_activities DROP COLUMN is_complete', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'project_selected_type_activities' AND column_name = 'is_complete'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE project_selected_type_activities DROP COLUMN is_complete', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------------------------
-- Part 5: drop the 5-gate tagging columns
-- ---------------------------------------------------------------------------

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'government_submissions' AND column_name = 'stage_key'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE government_submissions DROP COLUMN stage_key', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'project_documents' AND column_name = 'stage_key'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE project_documents DROP COLUMN stage_key', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------------------------
-- Part 6: drop the execution-step and approval-process tables outright
-- ---------------------------------------------------------------------------
-- Order matters: a child table (one holding the FK) drops before the
-- parent table it points to.

DROP TABLE IF EXISTS project_execution_steps;
DROP TABLE IF EXISTS execution_step_templates;
DROP TABLE IF EXISTS execution_step_set_templates;
DROP TABLE IF EXISTS project_approval_steps;
DROP TABLE IF EXISTS approval_process_templates;

SELECT 'Migration 0051 complete.' AS status;
