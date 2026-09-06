-- Migration 0065: Admin-configurable SMTP mailbox for sending Quotation/
-- Contract emails, instead of that being reachable only via server-level
-- .env variables (SMTP_HOST etc. in core/config.py, which remain a
-- fallback override -- see app.services.email_service._resolve_smtp_config).
--
-- Single-row settings table, same pattern as company_settings/
-- ai_configuration. password_encrypted is Fernet-encrypted at rest (see
-- app.core.security.encrypt_secret/decrypt_secret), never stored or
-- logged in plaintext.
--
-- Idempotent -- guarded by an information_schema check, same convention
-- as every other migration in this directory.
--
-- Run this against your MySQL/MariaDB database, e.g.:
--   mysql -u <user> -p <database> < backend/migrations/0065_email_settings.sql

CREATE TABLE IF NOT EXISTS email_settings (
    id                  INT PRIMARY KEY DEFAULT 1,
    provider            VARCHAR(20)  NOT NULL DEFAULT 'gmail',
    smtp_host           VARCHAR(255) NOT NULL DEFAULT 'smtp.gmail.com',
    smtp_port           INT UNSIGNED NOT NULL DEFAULT 587,
    smtp_use_tls        TINYINT(1)   NOT NULL DEFAULT 1,
    username            VARCHAR(255) NOT NULL DEFAULT '',
    password_encrypted  TEXT NULL,
    from_email          VARCHAR(255) NOT NULL DEFAULT '',
    from_name           VARCHAR(255) NOT NULL DEFAULT '',
    is_active           TINYINT(1)   NOT NULL DEFAULT 0,
    last_tested_at      DATETIME NULL,
    last_test_ok        TINYINT(1)   NULL,
    last_test_error     VARCHAR(500) NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_email_settings_singleton CHECK (id = 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SELECT 'Migration 0065 complete.' AS status;
