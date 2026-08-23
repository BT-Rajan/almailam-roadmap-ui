-- Migration 0031: default new clients straight to 'Ready' onboarding
-- state instead of 'Information Required'. The New Client wizard now
-- requires full contact, address, identification and consent details
-- up front (see the mandatory-details change to NewClientWizardPage.vue),
-- so there is nothing left for the Information Required -> Documents
-- Required -> Verification Required -> Under Review pipeline to gate --
-- a newly added client can be selected on a project immediately.
--
-- This only changes the column default for future inserts; it does not
-- touch any existing client's current onboarding_state. Run this if
-- anything besides the API's own create_client() (which now sets the
-- value explicitly) inserts client rows relying on the schema default,
-- e.g. bespoke import/seed scripts.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0031_client_default_onboarding_ready.sql

ALTER TABLE clients
    MODIFY COLUMN onboarding_state
        ENUM('Information Required','Documents Required','Verification Required','Under Review','Ready','Rejected','Suspended')
        NOT NULL DEFAULT 'Ready';

SELECT 'Migration 0031 complete.' AS status;
