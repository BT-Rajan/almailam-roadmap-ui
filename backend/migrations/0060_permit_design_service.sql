-- Migration 0060: seed "Permit" as a Design-branch service catalog item,
-- with a single child activity "Approval Service".
--
-- Adds "Permit" alongside the catalog's already-seeded named Design
-- services (Structural Engineering, MEP Design, etc.) so it's pickable
-- like any other billable Design service in the New Project wizard's
-- unified service picker. It has exactly one child activity --
-- "Approval Service" -- deliberately, so the picker's existing select-
-- parent-selects-all-activities / indeterminate-parent-state mechanics
-- (see ServicePickerDialog.vue's toggleService/serviceSelectionState,
-- unchanged by this migration) keep the two checkboxes in lockstep:
-- checking "Permit" checks "Approval Service", and checking "Approval
-- Service" on its own is indistinguishable from checking "Permit"
-- (a service with exactly one activity is "all" selected the moment
-- that one activity is), with no new picker code needed.
--
-- Direct SQL insert rather than relying solely on the lazy
-- service_catalog_service._ensure_seeded() -- that only runs the next
-- time GET /api/service-catalog/services is called, and only fires per
-- item if that item doesn't already exist. This migration guarantees an
-- existing install gets "Permit" without waiting on that.
--
-- Idempotent -- guarded by an existence check, same convention as every
-- other migration in this directory.

SET @db := DATABASE();

SET @permit_service_exists := (
    SELECT COUNT(*) FROM service_catalog_items WHERE name = 'Permit' AND deleted_at IS NULL
);

SET @sql := IF(@permit_service_exists = 0,
    "INSERT INTO service_catalog_items (name, branch) VALUES ('Permit', 'Design')",
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @permit_service_id := (
    SELECT id FROM service_catalog_items WHERE name = 'Permit' AND deleted_at IS NULL LIMIT 1
);

SET @sql := IF(@permit_service_id IS NOT NULL
                AND (SELECT COUNT(*) FROM service_catalog_activities WHERE service_id = @permit_service_id) = 0,
    CONCAT(
        'INSERT INTO service_catalog_activities (service_id, name, fixed_cost) VALUES (',
        @permit_service_id, ", 'Approval Service', 0.00)"
    ),
    'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT 'Migration 0060 complete.' AS status;
