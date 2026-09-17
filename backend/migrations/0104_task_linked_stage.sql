-- Migration 0104: collapse tasks.selected_activity_id / selected_permit_id /
-- selected_supervision_activity_id into one polymorphic pair --
-- linked_stage_type ('Design'/'Permit'/'Supervision') + linked_stage_id.
--
-- Migrations 0073 and 0088 gave each track its own nullable FK column on
-- `tasks`, so every place that closes/auto-closes/queries a stage's linked
-- tasks (project_service._set_design_activity_status/_assert_design_tasks_
-- complete/maybe_auto_close_design_activity/maybe_auto_close_permit/
-- maybe_auto_close_supervision_activity/_create_service_tasks,
-- task_service.set_status, status_report_service) exists three times, one
-- per column. A task is linked to at most one of the three (see
-- task_service.set_status's own comment to that effect), so this is one
-- nullable "what kind, which row" pair instead of three separate nullable
-- FKs -- no real column value or business rule changes, only how a task's
-- stage link is stored. No native cross-table FK constraint is possible on
-- a polymorphic id column (it can point at project_selected_activities,
-- project_selected_permits, or project_selected_supervision_activities
-- depending on linked_stage_type), so referential integrity here is
-- enforced in the service layer instead, same as elsewhere in this
-- codebase where a column's target table varies (e.g. audit_service's
-- entity_type/entity_id).
--
-- Idempotent -- guarded by information_schema checks, same convention as
-- every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0104_task_linked_stage.sql

SET @db := DATABASE();

-- 1. Add the new columns.
SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'tasks' AND column_name = 'linked_stage_type'
);
SET @sql := IF(@col_exists = 0,
    "ALTER TABLE tasks
       ADD COLUMN linked_stage_type ENUM('Design','Permit','Supervision') NULL AFTER project_id,
       ADD COLUMN linked_stage_id BIGINT UNSIGNED NULL AFTER linked_stage_type,
       ADD INDEX idx_tasks_linked_stage (linked_stage_type, linked_stage_id)",
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2. Backfill from whichever of the three old columns is set. A task is
--    never linked to more than one (see task_service.set_status), so
--    these three UPDATEs are mutually exclusive in practice.
SET @old_col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'tasks' AND column_name = 'selected_activity_id'
);
SET @sql := IF(@old_col_exists > 0,
    "UPDATE tasks SET linked_stage_type = 'Design', linked_stage_id = selected_activity_id
     WHERE selected_activity_id IS NOT NULL AND linked_stage_id IS NULL",
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @old_col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'tasks' AND column_name = 'selected_permit_id'
);
SET @sql := IF(@old_col_exists > 0,
    "UPDATE tasks SET linked_stage_type = 'Permit', linked_stage_id = selected_permit_id
     WHERE selected_permit_id IS NOT NULL AND linked_stage_id IS NULL",
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @old_col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'tasks' AND column_name = 'selected_supervision_activity_id'
);
SET @sql := IF(@old_col_exists > 0,
    "UPDATE tasks SET linked_stage_type = 'Supervision', linked_stage_id = selected_supervision_activity_id
     WHERE selected_supervision_activity_id IS NOT NULL AND linked_stage_id IS NULL",
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 3. Drop the old FKs, then the old columns (drops their own single-column
--    indexes along with them).
SET @fk_exists := (
    SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
    WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'tasks' AND CONSTRAINT_NAME = 'fk_tasks_selected_activity'
);
SET @sql := IF(@fk_exists > 0, 'ALTER TABLE tasks DROP FOREIGN KEY fk_tasks_selected_activity', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @fk_exists := (
    SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
    WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'tasks' AND CONSTRAINT_NAME = 'fk_tasks_selected_permit'
);
SET @sql := IF(@fk_exists > 0, 'ALTER TABLE tasks DROP FOREIGN KEY fk_tasks_selected_permit', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @fk_exists := (
    SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
    WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'tasks' AND CONSTRAINT_NAME = 'fk_tasks_selected_supervision_activity'
);
SET @sql := IF(@fk_exists > 0, 'ALTER TABLE tasks DROP FOREIGN KEY fk_tasks_selected_supervision_activity', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'tasks' AND column_name = 'selected_activity_id'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE tasks DROP COLUMN selected_activity_id', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'tasks' AND column_name = 'selected_permit_id'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE tasks DROP COLUMN selected_permit_id', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'tasks' AND column_name = 'selected_supervision_activity_id'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE tasks DROP COLUMN selected_supervision_activity_id', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0104 complete.' AS status;
