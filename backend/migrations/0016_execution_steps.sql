-- Migration 0016: linear execution-step checklist, replacing manually
-- typed project progress with a computed one
--
-- Two tables:
--   execution_step_templates -- the admin-configurable master list of
--     the real, tangible-act execution steps (First Meeting through
--     Lighting drawings), each with a weight_percentage. Seeded once
--     below from the source process document, expected to be tuned
--     from Admin afterward, not treated as final.
--   project_execution_steps -- each project's own independent copy of
--     that list, snapshotted at creation time (see
--     execution_step_service.py) so editing the template later never
--     retroactively shifts an in-progress project's completion
--     percentage.
--
-- project.progress becomes a computed value (sum of completed steps'
-- weight_percentage) rather than a number staff type in by hand --
-- that recalculation is application-layer (execution_step_service.
-- recompute_progress), not something this migration needs to touch.
--
-- Also backfills project_execution_steps for every project that
-- already existed before this migration ran -- without it, every
-- pre-existing project would be permanently stuck with an empty
-- checklist, since the snapshot only ever happens inside
-- project_service.create_project's own code path. Deliberately does
-- NOT touch those projects' existing progress value -- see the
-- backfill's own comment below for why.
--
-- Idempotent -- CREATE TABLE IF NOT EXISTS is naturally safe to re-run;
-- the seed INSERT is guarded to only fire on a genuinely empty table,
-- same backfill-guard pattern as migrations 0006/0007/0009.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0016_execution_steps.sql

CREATE TABLE IF NOT EXISTS execution_step_templates (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name                VARCHAR(200) NOT NULL,
    sequence_number     INT NOT NULL,
    weight_percentage   DECIMAL(5,2) NOT NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at          DATETIME NULL,
    INDEX idx_execution_step_templates_sequence (sequence_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS project_execution_steps (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id          BIGINT UNSIGNED NOT NULL,
    name                VARCHAR(200) NOT NULL,
    sequence_number     INT NOT NULL,
    weight_percentage   DECIMAL(5,2) NOT NULL,
    status              ENUM('Pending','Completed') NOT NULL DEFAULT 'Pending',
    completed_at        DATETIME NULL,
    completed_by        BIGINT UNSIGNED NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_project_execution_steps_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_project_execution_steps_completed_by FOREIGN KEY (completed_by) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT uq_project_execution_steps_project_sequence UNIQUE (project_id, sequence_number),
    INDEX idx_project_execution_steps_project (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO execution_step_templates (name, sequence_number, weight_percentage)
SELECT * FROM (
    SELECT 'Client requests captured' AS name, 1 AS sequence_number, 4.35 AS weight_percentage
    UNION ALL SELECT 'Quotation prepared', 2, 4.35
    UNION ALL SELECT 'Client Civil ID collected', 3, 4.35
    UNION ALL SELECT 'Ownership document collected', 4, 4.35
    UNION ALL SELECT 'Documents prepared for client signature (Baladia/KFD/MEW)', 5, 4.35
    UNION ALL SELECT 'MEW approval request submitted', 6, 4.35
    UNION ALL SELECT 'Contract initiated', 7, 4.35
    UNION ALL SELECT 'Architectural drawings completed', 8, 4.35
    UNION ALL SELECT 'Drawings submitted to Baladia/KFD (post client approval)', 9, 4.35
    UNION ALL SELECT '3D design completed', 10, 4.35
    UNION ALL SELECT 'Soil investigation report completed', 11, 4.35
    UNION ALL SELECT 'Structural drawings completed', 12, 4.35
    UNION ALL SELECT 'Window and door schedules completed', 13, 4.35
    UNION ALL SELECT 'Furniture plans completed', 14, 4.35
    UNION ALL SELECT 'Dimension plans completed', 15, 4.35
    UNION ALL SELECT 'Flooring plans completed', 16, 4.35
    UNION ALL SELECT 'Bathroom detail drawings completed', 17, 4.35
    UNION ALL SELECT 'Electrical power points completed', 18, 4.35
    UNION ALL SELECT 'Sanitary plans completed', 19, 4.34
    UNION ALL SELECT 'A/C drawings completed', 20, 4.34
    UNION ALL SELECT 'Structural drawings revised for A/C', 21, 4.34
    UNION ALL SELECT 'False ceiling drawings completed', 22, 4.34
    UNION ALL SELECT 'Lighting drawings completed', 23, 4.34
) AS seed
WHERE NOT EXISTS (SELECT 1 FROM execution_step_templates);

-- Backfill: every project that already existed before this migration
-- (created through raw seed data, or simply before this feature
-- shipped) has zero rows in project_execution_steps -- the snapshot
-- only ever happens inside create_project's own code path. Left
-- alone, every existing project would be permanently stuck showing an
-- empty checklist with no way to ever populate it, since nothing else
-- ever calls the snapshot.
--
-- Deliberately does NOT touch projects.progress here -- an in-flight
-- project that currently shows, say, 60% complete would otherwise
-- jump to 0% the moment this migration runs, which is a worse, more
-- confusing outcome than leaving that number exactly as it was until
-- someone actually starts checking off real steps for that project
-- (at which point execution_step_service's own recompute takes over
-- and the number becomes genuinely accurate going forward). This is a
-- deliberate, one-time exception to "progress is always computed,
-- never hand-set" -- it's not being hand-set, it's being left alone.
--
-- Guarded per-project (WHERE NOT EXISTS ... project_execution_steps),
-- so this is safe to re-run: only projects that still have zero steps
-- get backfilled, already-backfilled or newly-created projects are
-- left untouched.
--
-- The status column this originally inserted was dropped by migration
-- 0022 (replaced with completion_percentage, which defaults to 0) --
-- install.sh reapplies every migration file on every run with no
-- tracking of what already ran, so this file executes again on a
-- database that's already past 0022, at which point a hardcoded
-- reference to status would fail with "Unknown column". Branches on
-- whether the column is still there so this keeps working on both a
-- true first-time sequential install and a re-run against an
-- already-fully-migrated database.
SET @has_status = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'project_execution_steps' AND COLUMN_NAME = 'status'
);
SET @sql = IF(@has_status > 0,
  'INSERT INTO project_execution_steps (project_id, name, sequence_number, weight_percentage, status)
   SELECT p.id, t.name, t.sequence_number, t.weight_percentage, ''Pending''
   FROM projects p
   CROSS JOIN execution_step_templates t
   WHERE t.deleted_at IS NULL
     AND NOT EXISTS (SELECT 1 FROM project_execution_steps pes WHERE pes.project_id = p.id)',
  'INSERT INTO project_execution_steps (project_id, name, sequence_number, weight_percentage)
   SELECT p.id, t.name, t.sequence_number, t.weight_percentage
   FROM projects p
   CROSS JOIN execution_step_templates t
   WHERE t.deleted_at IS NULL
     AND NOT EXISTS (SELECT 1 FROM project_execution_steps pes WHERE pes.project_id = p.id)'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0016 complete.' AS status;
