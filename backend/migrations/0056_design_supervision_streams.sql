-- Migration 0056: Design and Supervision become two independently
-- selectable engagement streams instead of one exclusive category, and
-- 'Supervision' becomes a real project workflow stage alongside
-- 'Design'.
--
-- The Additional Activities picker used to only allow one
-- type_activity_categories pick per project ("a project has exactly one
-- engagement type"), which is why 'Supervision' had been worked around
-- as an activity item nested inside the 'Design' category instead of
-- its own category. The catalog already seeds 'Design' and
-- 'Supervision' as separate top-level categories (see
-- type_activity_catalog_service.DEFAULT_CATEGORIES) -- this migration
-- catches up the project-side schema to match: each selected type
-- activity now snapshots its own category (rather than the project
-- snapshotting a single category for all of them), and the workflow
-- stage enum gains 'Supervision' so a project can have a Design stage,
-- a Supervision stage, both, or neither, independently.
--
-- Idempotent -- guarded by information_schema checks, same convention
-- as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0056_design_supervision_streams.sql

SET @db := DATABASE();

-- 1. project_selected_type_activities.category_name -- previously only
--    tracked once on the project (type_category_name below), since a
--    project could only ever have activities from one category. Each
--    row now carries its own snapshot, since a project can span both
--    Design and Supervision activities at once.
SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'project_selected_type_activities' AND column_name = 'category_name'
);
SET @sql := IF(@col_exists = 0,
    'ALTER TABLE project_selected_type_activities ADD COLUMN category_name VARCHAR(150) NOT NULL DEFAULT '''' AFTER type_activity_item_id',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Backfill existing rows from the old project-level single category,
-- while that column still exists below -- every row on a project really
-- did belong to that one category under the old single-pick UI.
SET @old_col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'projects' AND column_name = 'type_category_name'
);
SET @sql := IF(@old_col_exists > 0,
    'UPDATE project_selected_type_activities psta
     JOIN projects p ON p.id = psta.project_id
     SET psta.category_name = p.type_category_name
     WHERE p.type_category_name IS NOT NULL AND (psta.category_name = '''' OR psta.category_name IS NULL)',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2. projects.current_stage -- add 'Supervision' to the enum, between
--    Design and Government Submission. MODIFY COLUMN with an identical
--    definition is a safe no-op, so this is naturally idempotent on its
--    own -- still existence-guarded since a MODIFY against a dropped
--    column would fail outright (install.sh reapplies every migration
--    file on every run with no tracking of what already ran).
SET @stage_col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'projects' AND column_name = 'current_stage'
);
SET @sql := IF(@stage_col_exists > 0,
    "ALTER TABLE projects MODIFY COLUMN current_stage ENUM('Requirement','Quotation','Contract','Design','Supervision','Government Submission') NOT NULL DEFAULT 'Requirement'",
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 3. Drop the now-redundant single-category snapshot on projects --
--    replaced by the per-row category_name above.
SET @old_col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'projects' AND column_name = 'type_category_name'
);
SET @sql := IF(@old_col_exists > 0, 'ALTER TABLE projects DROP COLUMN type_category_name', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0056 complete.' AS status;
