-- Migration 0088: sub-tasks for Permits and Supervision activities (not
-- just Design), a 'Preset' initial task status, and a per-task start
-- date -- foundation for auto-generating one task per selected Design
-- activity/Permit/Supervision activity the moment a project leaves
-- Contract (see project_service._create_service_tasks), so all three
-- tracks are staffed with a to-do the moment they become active, not
-- just Design.
--
-- Idempotent -- guarded by information_schema checks, same convention
-- as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0088_service_tasks.sql

SET @db := DATABASE();

-- ----------------------------------------------------------------------------
-- 1. tasks.status gains 'Preset' -- the initial state for a
--    system-generated service task, distinct from 'Pending' (a
--    manually-created task's own default), until the assigned engineer
--    or the owner/date is touched (see task_service.update_task).
-- ----------------------------------------------------------------------------

ALTER TABLE tasks
  MODIFY COLUMN status ENUM('Preset','Pending','In Progress','Completed') NOT NULL DEFAULT 'Pending';

-- ----------------------------------------------------------------------------
-- 2. tasks: start_date, plus links to the Permit/Supervision activity a
--    task belongs to (selected_activity_id, for Design, already exists
--    since migration 0073).
-- ----------------------------------------------------------------------------

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'tasks' AND column_name = 'start_date'
);
SET @sql := IF(@col_exists = 0,
    'ALTER TABLE tasks
       ADD COLUMN start_date DATE NULL AFTER selected_activity_id',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'tasks' AND column_name = 'selected_permit_id'
);
SET @sql := IF(@col_exists = 0,
    'ALTER TABLE tasks
       ADD COLUMN selected_permit_id BIGINT UNSIGNED NULL AFTER selected_activity_id,
       ADD CONSTRAINT fk_tasks_selected_permit FOREIGN KEY (selected_permit_id)
           REFERENCES project_selected_permits(id) ON DELETE SET NULL,
       ADD INDEX idx_tasks_selected_permit (selected_permit_id)',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'tasks' AND column_name = 'selected_supervision_activity_id'
);
SET @sql := IF(@col_exists = 0,
    'ALTER TABLE tasks
       ADD COLUMN selected_supervision_activity_id BIGINT UNSIGNED NULL AFTER selected_permit_id,
       ADD CONSTRAINT fk_tasks_selected_supervision_activity FOREIGN KEY (selected_supervision_activity_id)
           REFERENCES project_selected_supervision_activities(id) ON DELETE SET NULL,
       ADD INDEX idx_tasks_selected_supervision_activity (selected_supervision_activity_id)',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0088 complete.' AS status;
