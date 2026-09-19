-- Migration 0107: Make sure New Permit Application has something to pick
--
-- New Permit Application (SubmissionFormPage.vue) needs an Authority and
-- a Form, and the Form list is deliberately narrow: only forms of the
-- chosen authority whose `service_tags` name one of the project's
-- services (governmentFormHelpers.formMatchesProjectService -- a form
-- with no tags matches nothing). On an install where nobody has curated
-- Administration > Government Forms / Service Document Map -- a fresh
-- database, or one rebuilt with reset_db_from_schema.sh, which records
-- every earlier seed migration (0046 ...) as applied without running
-- it -- both dropdowns come up empty and the application can't be
-- created at all.
--
-- This seeds the firm's two authorities (the same two its permit types,
-- "Baladia Permits" and "KFD Permits", in permit_catalog_items are
-- named after) and one permit application form for each, with a
-- starting required-documents checklist (every application needs at
-- least one: Confirm Readiness waits for the checklist to be complete,
-- and an empty checklist never is), and tags each form with every
-- Design service in the Services catalog so it is offered for any
-- Design project.
--
-- Everything here is only a starting point -- authorities, forms,
-- checklists and service tags are all editable afterwards in
-- Administration > Government Forms / Service Document Map.
--
-- Non-destructive and idempotent, same INSERT ... SELECT ... WHERE NOT
-- EXISTS pattern as migrations 0040 and 0046:
--   - an authority is only added if no active authority of that
--     category exists yet (so an admin's own "Kuwait Fire Force" isn't
--     duplicated next to a seeded "Kuwait Fire Service Directorate");
--   - a form is only added if its code isn't active already;
--   - service tags are only filled in where a form's tags are empty --
--     tags an admin already curated are never overwritten. A Design
--     service added later needs adding to the form in Service Document
--     Map.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0107_seed_permit_application_authorities_and_forms.sql

SET NAMES utf8mb4;

-- 1. Authorities -----------------------------------------------------------

INSERT INTO government_authorities (name, category, website, description)
SELECT * FROM (
    SELECT
        'Kuwait Municipality' AS name,
        'Municipality' AS category,
        'https://www.baladia.gov.kw' AS website,
        'Kuwait Municipality (Baladia) -- regulates building permits, occupancy, and municipal compliance across Kuwait.' AS description
) AS seed
WHERE NOT EXISTS (
    SELECT 1 FROM government_authorities WHERE category = 'Municipality' AND deleted_at IS NULL
);

INSERT INTO government_authorities (name, category, website, description)
SELECT * FROM (
    SELECT
        'Kuwait Fire Service Directorate' AS name,
        'Fire Department' AS category,
        'https://www.kff.gov.kw' AS website,
        'Kuwait Fire Service Directorate (KFD) -- approves fire and life safety systems for buildings and facilities in Kuwait.' AS description
) AS seed
WHERE NOT EXISTS (
    SELECT 1 FROM government_authorities WHERE category = 'Fire Department' AND deleted_at IS NULL
);

-- 2. Every active Design service, as the JSON array service_tags wants ------
-- (NULL -> '[]' when the catalog has no Design service yet.) Supervision
-- is a separate, monthly-billed branch with no permit filing behind it.

SET SESSION group_concat_max_len = 65535;
SET @design_service_tags = (
    SELECT COALESCE(CONCAT('[', GROUP_CONCAT(JSON_QUOTE(name) ORDER BY id SEPARATOR ','), ']'), '[]')
    FROM service_catalog_items
    WHERE branch = 'Design' AND deleted_at IS NULL
);

-- 3. Forms -------------------------------------------------------------------

INSERT INTO government_forms (
    authority_id, form_code, title, version, language, category, description,
    required_documents, preview_url, template, service_tags, status
)
SELECT * FROM (
    SELECT
        (SELECT id FROM government_authorities WHERE category = 'Municipality' AND deleted_at IS NULL ORDER BY id LIMIT 1) AS authority_id,
        'BALADIA-PERMIT' AS form_code,
        'Baladia Building Permit Application' AS title,
        'v1.0' AS version,
        'English / Arabic' AS language,
        'Building Permit' AS category,
        'Application to Kuwait Municipality for a building permit / design approval for the project.' AS description,
        '["Ownership Proof","Owner Civil ID","Site Plan","Architectural Drawings","Structural Drawings"]' AS required_documents,
        NULL AS preview_url,
        NULL AS template,
        @design_service_tags AS service_tags,
        'Active' AS status
) AS seed
WHERE seed.authority_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM government_forms WHERE form_code = 'BALADIA-PERMIT' AND deleted_at IS NULL
);

INSERT INTO government_forms (
    authority_id, form_code, title, version, language, category, description,
    required_documents, preview_url, template, service_tags, status
)
SELECT * FROM (
    SELECT
        (SELECT id FROM government_authorities WHERE category = 'Fire Department' AND deleted_at IS NULL ORDER BY id LIMIT 1) AS authority_id,
        'KFD-PERMIT' AS form_code,
        'Fire Safety Approval Application' AS title,
        'v1.0' AS version,
        'English / Arabic' AS language,
        'Fire Safety Approval' AS category,
        'Application to the Kuwait Fire Service Directorate for approval of the project''s fire and life safety systems.' AS description,
        '["Architectural Drawings","Fire System Drawings","Material Safety Data Sheets"]' AS required_documents,
        NULL AS preview_url,
        NULL AS template,
        @design_service_tags AS service_tags,
        'Active' AS status
) AS seed
WHERE seed.authority_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM government_forms WHERE form_code = 'KFD-PERMIT' AND deleted_at IS NULL
);

-- 4. Forms that already exist but were never tagged -----------------------

UPDATE government_forms
SET service_tags = @design_service_tags
WHERE form_code IN ('BALADIA-PERMIT', 'KFD-PERMIT')
  AND deleted_at IS NULL
  AND (service_tags IS NULL OR JSON_LENGTH(service_tags) = 0)
  AND JSON_LENGTH(@design_service_tags) > 0;

SELECT 'Migration 0107 complete.' AS status;
