-- Migration 0060: (retired) seed "Permit" as a Design-branch service.
--
-- This used to insert a Design service named "Permit" with one activity,
-- "Approval Service". Permits have since moved to the Permit Catalog, and
-- a Design service may no longer be named "Permit" (see
-- service_catalog_service._assert_design_name_allowed), so the seed now
-- contradicts the catalog rules -- and it kept reappearing after an admin
-- deleted it.
--
-- Kept as a no-op so the numbering and the schema_migrations history
-- stay intact: servers that already ran it are unaffected (it never runs
-- twice), and a fresh install no longer gets the reserved-name service.

SELECT 'Migration 0060 retired (no-op).' AS status;
