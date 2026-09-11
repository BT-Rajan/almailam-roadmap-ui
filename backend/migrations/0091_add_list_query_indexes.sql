-- Migration 0091: indexes covering the columns projects/tasks/clients are
-- actually filtered and sorted by on every list page load.
--
-- Purely additive -- no columns, data, or query behavior change, just
-- indexes MySQL/MariaDB can choose to use. Safe to run on a database of
-- any size; on a small one the optimizer may not even pick them yet
-- (a full scan of a few hundred rows is already fast), but the queries
-- below get slower as each table grows *without* an index change, and
-- adding one after the fact means an ALTER TABLE that locks/rebuilds a
-- much bigger table later. Cheaper to add now while it's a no-op.
--
-- Every one of the tables below uses the same soft-delete pattern
-- (deleted_at IS NULL for the normal view), applied on top of whichever
-- other filter is active -- see project_service.list_projects,
-- task_service.list_tasks, client_service.list_clients. None of
-- deleted_at/status/current_stage/due_date had an index of their own
-- before this (unlike the foreign-key columns, which already do):
--
--   projects: deleted_at + current_stage  -- stage-scoped views (the
--     dashboard, ProjectsPage's stage filter)
--   projects: deleted_at + status         -- ProjectsPage's status filter
--   tasks: deleted_at + due_date          -- sort_and_paginate's own
--     default sort for every Tasks list call, filtered or not (see
--     task_service.list_tasks: `sort or "dueDate"`) -- this one runs on
--     literally every page load of every Tasks view, not just a filtered
--     subset of them.
--   tasks: deleted_at + status            -- a project's own Tasks tab,
--     scoped to one stage's service tasks, and the Task Board's
--     status grouping
--   clients: deleted_at + status          -- ClientsPage's status filter
--
-- Idempotent -- guarded by an information_schema.statistics check (the
-- index equivalent of the .columns check every other additive migration
-- here uses for new columns), safe to rerun.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0091_add_list_query_indexes.sql

SET @db := DATABASE();

SET @idx_exists := (
    SELECT COUNT(*) FROM information_schema.statistics
    WHERE table_schema = @db AND table_name = 'projects' AND index_name = 'idx_projects_deleted_stage'
);
SET @sql := IF(@idx_exists = 0,
    'ALTER TABLE projects ADD INDEX idx_projects_deleted_stage (deleted_at, current_stage)',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_exists := (
    SELECT COUNT(*) FROM information_schema.statistics
    WHERE table_schema = @db AND table_name = 'projects' AND index_name = 'idx_projects_deleted_status'
);
SET @sql := IF(@idx_exists = 0,
    'ALTER TABLE projects ADD INDEX idx_projects_deleted_status (deleted_at, status)',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_exists := (
    SELECT COUNT(*) FROM information_schema.statistics
    WHERE table_schema = @db AND table_name = 'tasks' AND index_name = 'idx_tasks_deleted_due_date'
);
SET @sql := IF(@idx_exists = 0,
    'ALTER TABLE tasks ADD INDEX idx_tasks_deleted_due_date (deleted_at, due_date)',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_exists := (
    SELECT COUNT(*) FROM information_schema.statistics
    WHERE table_schema = @db AND table_name = 'tasks' AND index_name = 'idx_tasks_deleted_status'
);
SET @sql := IF(@idx_exists = 0,
    'ALTER TABLE tasks ADD INDEX idx_tasks_deleted_status (deleted_at, status)',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_exists := (
    SELECT COUNT(*) FROM information_schema.statistics
    WHERE table_schema = @db AND table_name = 'clients' AND index_name = 'idx_clients_deleted_status'
);
SET @sql := IF(@idx_exists = 0,
    'ALTER TABLE clients ADD INDEX idx_clients_deleted_status (deleted_at, status)',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0091 complete.' AS status;
