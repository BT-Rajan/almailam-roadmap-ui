-- Migration 0041: Type-activity catalog + project selections
--
-- New feature: the final step of the New Project wizard now offers a
-- category picker (Design/Supervision/etc, admin-managed) followed by a
-- checklist of that category's activities. Selections are stored per
-- project and reconciled against the project's already-selected service
-- activities when quotations are generated: a type-activity whose name
-- matches a selected service activity is considered already covered (no
-- double charge); anything left over adds its own cost on top of the
-- service total.
--
-- 1. type_activity_categories / type_activity_items -- the admin-managed
--    catalog itself, same shape as service_catalog_items/_activities.
-- 2. projects.type_category_name / type_activity_total -- snapshot
--    fields on the project, same pattern as `service`/service_total.
-- 3. project_selected_type_activities -- one row per checked activity,
--    same snapshot approach as project_selected_activities.
--
-- Idempotent -- guarded by information_schema checks throughout, same
-- convention as every other migration in this directory.

SET @db := DATABASE();

-- 1. Catalog tables -----------------------------------------------------

SET @exists := (
    SELECT COUNT(*) FROM information_schema.tables
    WHERE table_schema = @db AND table_name = 'type_activity_categories'
);
SET @sql := IF(@exists = 0,
    'CREATE TABLE type_activity_categories (
        id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        name        VARCHAR(150) NOT NULL,
        created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        deleted_at  DATETIME NULL,
        INDEX idx_type_activity_categories_name (name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exists := (
    SELECT COUNT(*) FROM information_schema.tables
    WHERE table_schema = @db AND table_name = 'type_activity_items'
);
SET @sql := IF(@exists = 0,
    'CREATE TABLE type_activity_items (
        id           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        category_id  BIGINT UNSIGNED NOT NULL,
        name         VARCHAR(150) NOT NULL,
        cost         DECIMAL(12,2) NOT NULL DEFAULT 0,
        CONSTRAINT fk_type_activity_items_category FOREIGN KEY (category_id)
            REFERENCES type_activity_categories(id),
        INDEX idx_type_activity_items_category (category_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2. Project snapshot columns --------------------------------------------

SET @exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'projects' AND column_name = 'type_category_name'
);
SET @sql := IF(@exists = 0,
    'ALTER TABLE projects ADD COLUMN type_category_name VARCHAR(150) NULL AFTER required_permit_documents',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'projects' AND column_name = 'type_activity_total'
);
SET @sql := IF(@exists = 0,
    'ALTER TABLE projects ADD COLUMN type_activity_total DECIMAL(12,2) NULL AFTER type_category_name',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 3. Project selection breakdown ------------------------------------------

SET @exists := (
    SELECT COUNT(*) FROM information_schema.tables
    WHERE table_schema = @db AND table_name = 'project_selected_type_activities'
);
SET @sql := IF(@exists = 0,
    'CREATE TABLE project_selected_type_activities (
        id                     BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        project_id             BIGINT UNSIGNED NOT NULL,
        type_activity_item_id  VARCHAR(20) NOT NULL,
        activity_name          VARCHAR(150) NOT NULL,
        cost                   DECIMAL(12,2) NOT NULL,
        is_covered_by_service  TINYINT(1) NOT NULL DEFAULT 0,
        CONSTRAINT fk_project_selected_type_activities_project FOREIGN KEY (project_id)
            REFERENCES projects(id) ON DELETE CASCADE,
        INDEX idx_project_selected_type_activities_project (project_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 4. Seed the default categories/activities so a fresh install (or this
--    migration running before anyone visits the admin page) isn't
--    empty -- mirrors service_catalog_service.DEFAULT_SERVICE_NAMES.
SET @design_exists := (
    SELECT COUNT(*) FROM type_activity_categories WHERE name = 'Design' AND deleted_at IS NULL
);
INSERT INTO type_activity_categories (name)
SELECT 'Design' WHERE @design_exists = 0;
SET @design_id := (SELECT id FROM type_activity_categories WHERE name = 'Design' AND deleted_at IS NULL LIMIT 1);
INSERT INTO type_activity_items (category_id, name, cost)
SELECT * FROM (SELECT @design_id, 'Site Inspection', 150.00) AS t
WHERE @design_exists = 0;
INSERT INTO type_activity_items (category_id, name, cost)
SELECT * FROM (SELECT @design_id, 'Concept Drawings', 300.00) AS t
WHERE @design_exists = 0;
INSERT INTO type_activity_items (category_id, name, cost)
SELECT * FROM (SELECT @design_id, 'Structural Calculations', 400.00) AS t
WHERE @design_exists = 0;
INSERT INTO type_activity_items (category_id, name, cost)
SELECT * FROM (SELECT @design_id, 'Coordination with Authorities', 200.00) AS t
WHERE @design_exists = 0;

SET @supervision_exists := (
    SELECT COUNT(*) FROM type_activity_categories WHERE name = 'Supervision' AND deleted_at IS NULL
);
INSERT INTO type_activity_categories (name)
SELECT 'Supervision' WHERE @supervision_exists = 0;
SET @supervision_id := (SELECT id FROM type_activity_categories WHERE name = 'Supervision' AND deleted_at IS NULL LIMIT 1);
INSERT INTO type_activity_items (category_id, name, cost)
SELECT * FROM (SELECT @supervision_id, 'Weekly Site Visits', 250.00) AS t
WHERE @supervision_exists = 0;
INSERT INTO type_activity_items (category_id, name, cost)
SELECT * FROM (SELECT @supervision_id, 'Progress Reporting', 100.00) AS t
WHERE @supervision_exists = 0;
INSERT INTO type_activity_items (category_id, name, cost)
SELECT * FROM (SELECT @supervision_id, 'Materials Testing Coordination', 150.00) AS t
WHERE @supervision_exists = 0;
INSERT INTO type_activity_items (category_id, name, cost)
SELECT * FROM (SELECT @supervision_id, 'Snagging & Handover Inspection', 200.00) AS t
WHERE @supervision_exists = 0;

SELECT 'Migration 0041 complete.' AS status;
