-- Migration 0042: Scope-based execution tracking
--
-- New feature: the Execution & Tracking stage's real completion gate is
-- now whether the project's actual quoted scope (the specific services/
-- activities picked at creation, not the generic 23-item process
-- checklist) has been delivered, tracked per line via is_complete on
-- project_selected_activities/project_selected_type_activities.
--
-- Additionally, staff can flag work delivered beyond that original
-- scope ("were any additional services rendered?") by checking off
-- items from the existing 23-item execution checklist and answering
-- whether each is covered under the contract -- recorded on
-- project_execution_steps via is_additional_scope/contract_covered.
--
-- Idempotent -- guarded by information_schema checks, same convention
-- as every other migration in this directory.

SET @db := DATABASE();

SET @exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'project_selected_activities' AND column_name = 'is_complete'
);
SET @sql := IF(@exists = 0,
    'ALTER TABLE project_selected_activities ADD COLUMN is_complete TINYINT(1) NOT NULL DEFAULT 0',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'project_selected_type_activities' AND column_name = 'is_complete'
);
SET @sql := IF(@exists = 0,
    'ALTER TABLE project_selected_type_activities ADD COLUMN is_complete TINYINT(1) NOT NULL DEFAULT 0',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'project_execution_steps' AND column_name = 'is_additional_scope'
);
SET @sql := IF(@exists = 0,
    'ALTER TABLE project_execution_steps ADD COLUMN is_additional_scope TINYINT(1) NOT NULL DEFAULT 0',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = @db AND table_name = 'project_execution_steps' AND column_name = 'contract_covered'
);
SET @sql := IF(@exists = 0,
    'ALTER TABLE project_execution_steps ADD COLUMN contract_covered TINYINT(1) NULL',
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0042 complete.' AS status;
