-- Migration 0032: drop "Verification Required" from clients.onboarding_state
--
-- Client onboarding completeness is now judged on Identification and
-- Consent being on file (see src/utils/clientHelpers.ts's
-- calculateOnboardingState and CLIENT_ONBOARDING_REQUIREMENTS in
-- src/constants/clientOptions.ts), not on document verification.
-- "Documents Required" now transitions straight to "Under Review" --
-- see app/core/status_transitions.py's CLIENT_ONBOARDING_ALLOWED_TRANSITIONS.
-- Document verification itself (ClientVerification records, the
-- per-document "Verify" action) is unaffected by this migration -- it
-- simply no longer gates onboarding or has its own workspace tab.
--
-- ENUM columns can't just be narrowed directly if existing rows use a
-- value being removed -- MySQL would either reject the ALTER outright
-- (strict mode) or silently blank those rows to '' (non-strict mode).
-- Any client currently sitting at "Verification Required" is moved to
-- "Under Review", the state immediately after it in the old flow, so
-- clients don't jump backward or skip stages they'd already cleared.
-- Default carried forward as 'Ready', matching migration 0031's change
-- (new clients no longer start the onboarding pipeline at all -- see
-- client_service.py's create_client). Each step re-runs harmlessly if
-- this migration is applied more than once.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0032_remove_verification_required_onboarding_state.sql

UPDATE clients SET onboarding_state = 'Under Review' WHERE onboarding_state = 'Verification Required';

ALTER TABLE clients
  MODIFY COLUMN onboarding_state ENUM('Information Required','Documents Required','Under Review','Ready','Rejected','Suspended')
    NOT NULL DEFAULT 'Ready';

SELECT 'Migration 0032 complete.' AS status;
