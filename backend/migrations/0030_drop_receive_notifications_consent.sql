-- Migration 0030: remove 'Receive Notifications' as a client consent
-- type. It was a mandatory consent gating New Client onboarding
-- (Consent step of the wizard) but has been dropped as a requirement
-- entirely -- see CONSENT_TYPES in app/models/client.py and
-- CLIENT_CONSENT_TYPE_OPTIONS in src/constants/clientOptions.ts.
--
-- Any previously recorded 'Receive Notifications' consent rows are
-- deleted first -- MySQL/MariaDB refuses to narrow an ENUM column
-- while rows still hold the value being removed, and there is no
-- meaningful way to remap this consent type onto one of the three
-- remaining ones.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0030_drop_receive_notifications_consent.sql

DELETE FROM client_consents WHERE consent_type = 'Receive Notifications';

ALTER TABLE client_consents
    MODIFY COLUMN consent_type ENUM('Process Personal Information','Electronic Communication','Process Documents') NOT NULL;

SELECT 'Migration 0030 complete.' AS status;
