-- Migration 0093: remove Project.priority
--
-- Project priority (High/Medium/Low) was a separate, unrelated feature
-- from Task priority/severity (removed from Tasks in an earlier pass --
-- see the "Remove Priority and Severity from Tasks entirely" work,
-- which explicitly left this Project column alone as out of scope).
-- It's now being removed for real: the New Project wizard never had a
-- step to choose it (every project silently got "Medium"), and nothing
-- in the product surfaced it as meaningful -- it was just a filter/
-- column/badge on the Projects list (ProjectsPage.vue), the Edit
-- dialog, the Overview tab, and the per-project report. All of that
-- frontend surface area, the /api/reports/projects-by-priority report
-- endpoint, and the backend field/validators are removed together with
-- this column.
--
-- Idempotent -- guarded by an information_schema check, same
-- convention as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0093_remove_project_priority.sql

SET @db := DATABASE();

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'projects' AND column_name = 'priority'
);
SET @sql := IF(@col_exists > 0, 'ALTER TABLE projects DROP COLUMN priority', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0093 complete.' AS status;
