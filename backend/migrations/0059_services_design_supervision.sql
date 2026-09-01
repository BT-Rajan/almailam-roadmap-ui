-- Migration 0059: Collapse "Service Catalog" + "Additional Activity Catalog"
-- into one "Services" catalog with exactly two branches, Design and
-- Supervision, and give Supervision real monthly/prorated billing.
--
-- Before: two independent catalogs (service_catalog_items/_activities,
-- and type_activity_categories/_items with a free-renamable "Design" and
-- "Supervision" category), reconciled at project-selection time so a
-- same-named pick in one wasn't double-billed against the other. After:
-- service_catalog_items gains a `branch` column (Design/Supervision) --
-- every existing named service becomes Design-branch (the default), and
-- a single new "Supervision" service is seeded from the old type-activity
-- Supervision category's items (same names/costs, now interpreted as
-- MONTHLY rates instead of one-time). The old type-activity Design
-- category is dropped outright -- real named services already cover
-- that ground, so it was pure duplication. No more coverage
-- reconciliation: Design and Supervision are different deliverables on
-- different billing cycles, there's no realistic overlap to reconcile.
--
-- project_selected_type_activities (generic, any category, with
-- is_covered_by_service) is replaced by project_selected_supervision_
-- activities (Supervision only, with its own start_date/end_date per
-- activity -- see project_service.py). projects gains an overall
-- supervision_start_date/supervision_end_date pair (separate from each
-- activity's own dates), and type_activity_total is renamed to
-- supervision_monthly_total (the nominal combined monthly rate across
-- selected activities, not prorated -- informational only; the real
-- prorated schedule lives in payment_obligations once a Supervision
-- financial agreement is created).
--
-- financial_agreements gains a `stream` column (Design/Supervision) and
-- its one-per-project uniqueness relaxes to one-per-(project, stream),
-- since a project can now have both a one-time Design agreement and a
-- recurring Supervision agreement side by side.
--
-- Test/demo data only in this app at the time of writing -- this
-- migration restructures directly rather than preserving a parallel
-- legacy shape.
--
-- Idempotent -- guarded by information_schema checks / conditional
-- inserts, same convention as every other migration in this directory.

SET @db := DATABASE();

-- ----------------------------------------------------------------------------
-- 1. service_catalog_items.branch
-- ----------------------------------------------------------------------------

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'service_catalog_items' AND column_name = 'branch'
);
SET @sql := IF(@col_exists = 0,
    "ALTER TABLE service_catalog_items ADD COLUMN branch ENUM('Design','Supervision') NOT NULL DEFAULT 'Design' AFTER name",
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ----------------------------------------------------------------------------
-- 2. Seed the "Supervision" service from the old type-activity category's
--    items (whatever an admin has them at right now, not the original
--    seed values, in case they were already edited) -- only if it
--    doesn't already exist and the old catalog is still present.
-- ----------------------------------------------------------------------------

SET @type_activity_table_exists := (
    SELECT COUNT(*) FROM information_schema.tables
    WHERE table_schema = @db AND table_name = 'type_activity_categories'
);
SET @supervision_service_exists := (
    SELECT COUNT(*) FROM service_catalog_items WHERE name = 'Supervision' AND deleted_at IS NULL
);

SET @sql := IF(@type_activity_table_exists > 0 AND @supervision_service_exists = 0,
    "INSERT INTO service_catalog_items (name, branch) VALUES ('Supervision', 'Supervision')",
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @supervision_service_id := (
    SELECT id FROM service_catalog_items WHERE name = 'Supervision' AND deleted_at IS NULL LIMIT 1
);

SET @sql := IF(@type_activity_table_exists > 0 AND @supervision_service_id IS NOT NULL
                AND (SELECT COUNT(*) FROM service_catalog_activities WHERE service_id = @supervision_service_id) = 0,
    CONCAT(
        'INSERT INTO service_catalog_activities (service_id, name, fixed_cost) ',
        'SELECT ', @supervision_service_id, ', tai.name, tai.cost ',
        'FROM type_activity_items tai ',
        'JOIN type_activity_categories tac ON tac.id = tai.category_id ',
        "WHERE tac.name = 'Supervision'"
    ),
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ----------------------------------------------------------------------------
-- 3. project_selected_supervision_activities (replaces
--    project_selected_type_activities)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS project_selected_supervision_activities (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id      BIGINT UNSIGNED NOT NULL,
    activity_id     VARCHAR(20) NOT NULL,
    activity_name   VARCHAR(150) NOT NULL,
    monthly_rate    DECIMAL(12,2) NOT NULL,
    start_date      DATE NOT NULL,
    end_date        DATE NULL,
    CONSTRAINT fk_project_selected_supervision_activities_project FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_project_selected_supervision_activities_project (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET @old_selection_table_exists := (
    SELECT COUNT(*) FROM information_schema.tables
    WHERE table_schema = @db AND table_name = 'project_selected_type_activities'
);
SET @sql := IF(@old_selection_table_exists > 0,
    'DROP TABLE project_selected_type_activities',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := IF(@type_activity_table_exists > 0,
    'DROP TABLE IF EXISTS type_activity_items',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := IF(@type_activity_table_exists > 0,
    'DROP TABLE IF EXISTS type_activity_categories',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ----------------------------------------------------------------------------
-- 4. projects: overall supervision window + rename type_activity_total
-- ----------------------------------------------------------------------------

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'projects' AND column_name = 'supervision_start_date'
);
SET @sql := IF(@col_exists = 0,
    'ALTER TABLE projects ADD COLUMN supervision_start_date DATE NULL, ADD COLUMN supervision_end_date DATE NULL',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @old_total_col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'projects' AND column_name = 'type_activity_total'
);
SET @new_total_col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'projects' AND column_name = 'supervision_monthly_total'
);
SET @sql := IF(@old_total_col_exists > 0 AND @new_total_col_exists = 0,
    'ALTER TABLE projects CHANGE COLUMN type_activity_total supervision_monthly_total DECIMAL(12,2) NULL',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ----------------------------------------------------------------------------
-- 5. financial_agreements.stream + relax uniqueness to per-stream
-- ----------------------------------------------------------------------------

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'financial_agreements' AND column_name = 'stream'
);
SET @sql := IF(@col_exists = 0,
    "ALTER TABLE financial_agreements ADD COLUMN stream ENUM('Design','Supervision') NOT NULL DEFAULT 'Design' AFTER project_id",
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @old_unique_exists := (
    SELECT COUNT(*) FROM information_schema.table_constraints
    WHERE table_schema = @db AND table_name = 'financial_agreements' AND constraint_name = 'uq_financial_agreements_project'
);
SET @sql := IF(@old_unique_exists > 0,
    'ALTER TABLE financial_agreements DROP INDEX uq_financial_agreements_project',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @new_unique_exists := (
    SELECT COUNT(*) FROM information_schema.table_constraints
    WHERE table_schema = @db AND table_name = 'financial_agreements' AND constraint_name = 'uq_financial_agreements_project_stream'
);
SET @sql := IF(@new_unique_exists = 0,
    'ALTER TABLE financial_agreements ADD CONSTRAINT uq_financial_agreements_project_stream UNIQUE (project_id, stream)',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0059 complete.' AS status;
