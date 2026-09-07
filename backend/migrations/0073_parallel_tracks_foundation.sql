-- Migration 0073: foundation for Design/Permit/Supervision running as
-- independent parallel tracks (instead of the strict linear Contract ->
-- [Design] -> Government Submission -> [Supervision] chain) and for a
-- real, gated "Completed" project status.
--
-- Purely additive -- every new column is nullable/defaulted and every
-- new table is new, so existing flows keep working unmodified until
-- later migrations' application code starts using them. See
-- app/models/project.py, task.py, government.py,
-- permit_selection.py, prerequisite.py, document_requirement.py,
-- handover_checklist.py for the SQLAlchemy models these correspond to.
--
-- Idempotent -- guarded by information_schema checks / CREATE TABLE IF
-- NOT EXISTS, same convention as every other migration here.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0073_parallel_tracks_foundation.sql

SET @db := DATABASE();

-- ----------------------------------------------------------------------------
-- 1. projects.status gains 'Completed'
-- ----------------------------------------------------------------------------

ALTER TABLE projects
  MODIFY COLUMN status ENUM('Active','On Hold','Cancelled','Completed') NOT NULL DEFAULT 'Active';

-- ----------------------------------------------------------------------------
-- 2. projects: handover + new staleness-style notification guards
-- ----------------------------------------------------------------------------

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'projects' AND column_name = 'handover_sent_at'
);
SET @sql := IF(@col_exists = 0,
    'ALTER TABLE projects
       ADD COLUMN handover_sent_at DATETIME NULL,
       ADD COLUMN handover_acknowledged_at DATETIME NULL,
       ADD COLUMN unpaid_completion_notified_at DATETIME NULL,
       ADD COLUMN overdue_notified_at DATETIME NULL',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ----------------------------------------------------------------------------
-- 3. project_selected_activities: status / closed_at / closed_by
-- ----------------------------------------------------------------------------

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'project_selected_activities' AND column_name = 'status'
);
SET @sql := IF(@col_exists = 0,
    "ALTER TABLE project_selected_activities
       ADD COLUMN status ENUM('Not Started','In Progress','Complete','Cancelled') NOT NULL DEFAULT 'Not Started',
       ADD COLUMN closed_at DATETIME NULL,
       ADD COLUMN closed_by BIGINT UNSIGNED NULL,
       ADD CONSTRAINT fk_project_selected_activities_closed_by FOREIGN KEY (closed_by) REFERENCES users(id) ON DELETE SET NULL",
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ----------------------------------------------------------------------------
-- 4. project_selected_supervision_activities: status / closed_at / closed_by
-- ----------------------------------------------------------------------------

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'project_selected_supervision_activities' AND column_name = 'status'
);
SET @sql := IF(@col_exists = 0,
    "ALTER TABLE project_selected_supervision_activities
       ADD COLUMN status ENUM('Not Started','In Progress','Complete','Cancelled') NOT NULL DEFAULT 'Not Started',
       ADD COLUMN closed_at DATETIME NULL,
       ADD COLUMN closed_by BIGINT UNSIGNED NULL,
       ADD CONSTRAINT fk_project_selected_supervision_activities_closed_by FOREIGN KEY (closed_by) REFERENCES users(id) ON DELETE SET NULL",
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ----------------------------------------------------------------------------
-- 5. project_selected_permits (new table -- the missing "permits
--    selected onto a project" counterpart to the two tables above)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS project_selected_permits (
    id                        BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id                BIGINT UNSIGNED NOT NULL,
    permit_catalog_item_id    BIGINT UNSIGNED NULL,
    permit_name               VARCHAR(150) NOT NULL,
    status                    ENUM('Planned','Eligible','In Progress','Complete','Cancelled') NOT NULL DEFAULT 'Planned',
    eligibility_met_at        DATETIME NULL,
    eligibility_notified_at   DATETIME NULL,
    closed_at                 DATETIME NULL,
    closed_by                 BIGINT UNSIGNED NULL,
    CONSTRAINT fk_project_selected_permits_project FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_project_selected_permits_catalog_item FOREIGN KEY (permit_catalog_item_id)
        REFERENCES permit_catalog_items(id) ON DELETE SET NULL,
    CONSTRAINT fk_project_selected_permits_closed_by FOREIGN KEY (closed_by)
        REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_project_selected_permits_project (project_id),
    INDEX idx_project_selected_permits_catalog_item (permit_catalog_item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- 6. permit_prerequisites / supervision_prerequisites (new tables --
--    admin-configured "N design activities required before eligible")
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS permit_prerequisites (
    id                       BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    permit_catalog_item_id   BIGINT UNSIGNED NOT NULL,
    design_activity_id       BIGINT UNSIGNED NOT NULL,
    CONSTRAINT fk_permit_prerequisites_permit FOREIGN KEY (permit_catalog_item_id)
        REFERENCES permit_catalog_items(id) ON DELETE CASCADE,
    CONSTRAINT fk_permit_prerequisites_design_activity FOREIGN KEY (design_activity_id)
        REFERENCES service_catalog_activities(id) ON DELETE CASCADE,
    UNIQUE KEY uq_permit_prerequisites_pair (permit_catalog_item_id, design_activity_id),
    INDEX idx_permit_prerequisites_design_activity (design_activity_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS supervision_prerequisites (
    id                       BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    supervision_activity_id  BIGINT UNSIGNED NOT NULL,
    design_activity_id       BIGINT UNSIGNED NOT NULL,
    CONSTRAINT fk_supervision_prerequisites_supervision_activity FOREIGN KEY (supervision_activity_id)
        REFERENCES service_catalog_activities(id) ON DELETE CASCADE,
    CONSTRAINT fk_supervision_prerequisites_design_activity FOREIGN KEY (design_activity_id)
        REFERENCES service_catalog_activities(id) ON DELETE CASCADE,
    UNIQUE KEY uq_supervision_prerequisites_pair (supervision_activity_id, design_activity_id),
    INDEX idx_supervision_prerequisites_design_activity (design_activity_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- 7. document_requirements / document_requirement_links (new tables --
--    admin-defined, reusable, informational-only document reference list)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS document_requirements (
    id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(150) NOT NULL,
    description   VARCHAR(500) NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at    DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS document_requirement_links (
    id                        BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    document_requirement_id   BIGINT UNSIGNED NOT NULL,
    target_type               ENUM('Design','Permit','Supervision') NOT NULL,
    target_catalog_id         BIGINT UNSIGNED NOT NULL,
    CONSTRAINT fk_document_requirement_links_requirement FOREIGN KEY (document_requirement_id)
        REFERENCES document_requirements(id) ON DELETE CASCADE,
    UNIQUE KEY uq_document_requirement_links_target (document_requirement_id, target_type, target_catalog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- 8. handover_checklist_items (new table)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS handover_checklist_items (
    id             BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id     BIGINT UNSIGNED NOT NULL,
    source_type    ENUM('Design','Permit','Supervision') NOT NULL,
    source_id      BIGINT UNSIGNED NOT NULL,
    title          VARCHAR(150) NOT NULL,
    completed_at   DATETIME NOT NULL,
    CONSTRAINT fk_handover_checklist_items_project FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE KEY uq_handover_checklist_items_source (project_id, source_type, source_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- 9. tasks.selected_activity_id (optional link to the Design activity a
--    task belongs to -- Permit/Supervision tracks have no sub-tasks)
-- ----------------------------------------------------------------------------

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'tasks' AND column_name = 'selected_activity_id'
);
SET @sql := IF(@col_exists = 0,
    'ALTER TABLE tasks
       ADD COLUMN selected_activity_id BIGINT UNSIGNED NULL AFTER project_id,
       ADD CONSTRAINT fk_tasks_selected_activity FOREIGN KEY (selected_activity_id)
           REFERENCES project_selected_activities(id) ON DELETE SET NULL,
       ADD INDEX idx_tasks_selected_activity (selected_activity_id)',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ----------------------------------------------------------------------------
-- 10. government_submissions.project_selected_permit_id (optional link
--     back to the planned permit an application fulfils)
-- ----------------------------------------------------------------------------

SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'government_submissions' AND column_name = 'project_selected_permit_id'
);
SET @sql := IF(@col_exists = 0,
    'ALTER TABLE government_submissions
       ADD COLUMN project_selected_permit_id BIGINT UNSIGNED NULL AFTER form_id,
       ADD CONSTRAINT fk_government_submissions_selected_permit FOREIGN KEY (project_selected_permit_id)
           REFERENCES project_selected_permits(id) ON DELETE SET NULL,
       ADD INDEX idx_government_submissions_selected_permit (project_selected_permit_id)',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0073 complete.' AS status;
