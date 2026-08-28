SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS users (
    id                      BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username                VARCHAR(50)  NOT NULL UNIQUE,
    employee_id             VARCHAR(30)  NULL UNIQUE,
    -- Customer Portal login identifier -- same idea as employee_id above,
    -- an alternate way to resolve the same users table to one login
    -- mechanism instead of a separate one. client_id scopes a Customer
    -- account to the one client record it's allowed to see projects for.
    customer_id             VARCHAR(30)  NULL UNIQUE,
    client_id               BIGINT UNSIGNED NULL,
    email                   VARCHAR(120) NOT NULL UNIQUE,
    password_hash           VARCHAR(255) NOT NULL,
    full_name               VARCHAR(120) NOT NULL,
    designation             VARCHAR(120) NULL,
    mobile                  VARCHAR(30)  NULL,
    role                    ENUM('Administrator','Project Manager','Engineer','Document Controller','Viewer','Customer')
                                NOT NULL DEFAULT 'Viewer',
    is_active               TINYINT(1) NOT NULL DEFAULT 1,
    failed_login_attempts   SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    locked_until            DATETIME NULL,
    created_at              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at              DATETIME NULL,
    CONSTRAINT fk_users_client FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE RESTRICT,
    INDEX idx_users_role (role),
    INDEX idx_users_deleted_at (deleted_at),
    INDEX idx_users_client (client_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS role_definitions (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    role            VARCHAR(50) NOT NULL,
    description     VARCHAR(500) NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_role_definitions_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS role_permissions (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    role_id         BIGINT UNSIGNED NOT NULL,
    module          VARCHAR(50) NOT NULL,
    can_view        TINYINT(1) NOT NULL DEFAULT 0,
    can_edit        TINYINT(1) NOT NULL DEFAULT 0,
    can_delete      TINYINT(1) NOT NULL DEFAULT 0,
    CONSTRAINT fk_role_permissions_role
        FOREIGN KEY (role_id) REFERENCES role_definitions(id) ON DELETE CASCADE,
    UNIQUE KEY uq_role_permissions_role_module (role_id, module)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    jti             CHAR(36)     NOT NULL UNIQUE,
    user_id         BIGINT UNSIGNED NOT NULL,
    revoked         TINYINT(1)   NOT NULL DEFAULT 0,
    expires_at      DATETIME     NOT NULL,
    created_at      DATETIME     NOT NULL,
    last_used_at    DATETIME     NOT NULL,
    CONSTRAINT fk_refresh_tokens_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_refresh_tokens_user (user_id),
    INDEX idx_refresh_tokens_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS number_series (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    doc_type        VARCHAR(30) NOT NULL,   -- 'QUOTATION', 'CONTRACT', 'GOVERNMENT_SUBMISSION'
    year            SMALLINT UNSIGNED NOT NULL,
    prefix          VARCHAR(10) NOT NULL,   -- e.g. 'QUO', 'CON', 'SUB'
    next_number     INT UNSIGNED NOT NULL DEFAULT 1,
    padding         TINYINT UNSIGNED NOT NULL DEFAULT 3,  -- QUO-2026-014
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_number_series_doc_type_year (doc_type, year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS audit_log (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    entity_type     VARCHAR(40)  NOT NULL,   -- 'CLIENT', 'FINANCIAL_AGREEMENT', ...
    entity_id       BIGINT UNSIGNED NOT NULL,
    event_label     VARCHAR(120) NOT NULL,   -- 'Client created', 'Payment Received', ...
    previous_value  TEXT NULL,
    new_value       TEXT NULL,
    reason          TEXT NULL,
    changed_by      BIGINT UNSIGNED NULL,
    changed_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_log_user
        FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_audit_log_entity (entity_type, entity_id),
    INDEX idx_audit_log_changed_at (changed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS clients (
    id                              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    client_type                     ENUM('Individual','Company','Organisation','Government Entity','Other') NOT NULL,
    company_name                    VARCHAR(200) NOT NULL,
    contact_person                  VARCHAR(120) NOT NULL,
    mobile                          VARCHAR(30)  NOT NULL,
    email                           VARCHAR(120) NOT NULL,
    city                            VARCHAR(80)  NOT NULL,
    status                          ENUM('Active','Inactive') NOT NULL DEFAULT 'Active',
    onboarding_state                ENUM('Information Required','Documents Required','Under Review','Ready','Rejected','Suspended')
                                        NOT NULL DEFAULT 'Ready',
    onboarding_notified_at          DATETIME NULL,
    ind_full_legal_name             VARCHAR(150) NULL,
    ind_preferred_name              VARCHAR(100) NULL,
    ind_nationality                 VARCHAR(80)  NULL,
    ind_date_of_birth               DATE NULL,
    ind_country_of_residence        VARCHAR(80)  NULL,
    org_legal_name                  VARCHAR(200) NULL,
    org_trade_name                  VARCHAR(200) NULL,
    org_organisation_type           VARCHAR(100) NULL,
    org_registration_number         VARCHAR(60)  NULL,
    org_trade_licence_number        VARCHAR(60)  NULL,
    org_tax_identification_number   VARCHAR(60)  NULL,
    org_country_of_registration     VARCHAR(80)  NULL,
    org_date_of_incorporation       DATE NULL,
    org_website                     VARCHAR(200) NULL,
    preferred_language              VARCHAR(40)  NOT NULL DEFAULT 'English',
    preferred_channel               ENUM('Email','WhatsApp','SMS','Phone') NOT NULL DEFAULT 'Email',
    email_consent                   TINYINT(1) NOT NULL DEFAULT 0,
    whatsapp_consent                TINYINT(1) NOT NULL DEFAULT 0,
    sms_consent                     TINYINT(1) NOT NULL DEFAULT 0,
    account_manager_id              BIGINT UNSIGNED NULL,
    notes                           VARCHAR(2000) NULL,
    created_at                      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at                      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at                      DATETIME NULL,
    CONSTRAINT fk_clients_account_manager FOREIGN KEY (account_manager_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_clients_status (status),
    INDEX idx_clients_onboarding_state (onboarding_state),
    INDEX idx_clients_deleted_at (deleted_at),
    INDEX idx_clients_account_manager (account_manager_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS client_contacts (
    id                          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    client_id                   BIGINT UNSIGNED NOT NULL,
    name                        VARCHAR(120) NOT NULL,
    contact_type                ENUM('Primary Contact','Billing Contact','Legal Contact','Authorised Representative','Technical Contact','Other') NOT NULL,
    mobile                      VARCHAR(30)  NOT NULL,
    email                       VARCHAR(120) NOT NULL,
    is_authorised_representative TINYINT(1) NOT NULL DEFAULT 0,
    deleted_at                  DATETIME NULL,
    CONSTRAINT fk_client_contacts_client FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    INDEX idx_client_contacts_client (client_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS client_addresses (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    client_id       BIGINT UNSIGNED NOT NULL,
    address_type    ENUM('Registered','Operating','Residential','Mailing') NOT NULL,
    country         VARCHAR(80)  NOT NULL,
    state           VARCHAR(80)  NOT NULL,
    city            VARCHAR(80)  NOT NULL,
    area            VARCHAR(120) NULL,
    street          VARCHAR(150) NULL,
    building        VARCHAR(120) NULL,
    deleted_at      DATETIME NULL,
    CONSTRAINT fk_client_addresses_client FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    INDEX idx_client_addresses_client (client_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS client_identifications (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    client_id           BIGINT UNSIGNED NOT NULL,
    document_type       ENUM('Civil ID','Passport','Trade Licence','Other') NOT NULL,
    document_number     VARCHAR(60) NOT NULL,
    issue_date          DATE NOT NULL,
    expiry_date         DATE NOT NULL,
    issuing_country     VARCHAR(80) NOT NULL,
    deleted_at          DATETIME NULL,
    CONSTRAINT fk_client_identifications_client FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    INDEX idx_client_identifications_client (client_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS client_consents (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    client_id       BIGINT UNSIGNED NOT NULL,
    consent_type    ENUM('Process Personal Information','Electronic Communication','Process Documents') NOT NULL,
    version         VARCHAR(20)  NOT NULL,
    granted         TINYINT(1)   NOT NULL,
    recorded_at     DATETIME     NOT NULL,
    method          VARCHAR(150) NOT NULL,
    recorded_by     BIGINT UNSIGNED NOT NULL,
    CONSTRAINT fk_client_consents_client FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    CONSTRAINT fk_client_consents_user FOREIGN KEY (recorded_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_client_consents_client (client_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS client_documents (
    id                   BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    client_id            BIGINT UNSIGNED NOT NULL,
    category             ENUM('Identity Document','Passport','Trade Licence','Registration Document','Authorisation Document','Other') NOT NULL,
    title                VARCHAR(150) NOT NULL,
    issue_date           DATE NULL,
    expiry_date          DATE NULL,
    issuing_authority    VARCHAR(150) NULL,
    version              INT UNSIGNED NOT NULL DEFAULT 1,
    verification_status  ENUM('Pending','Verified','Rejected') NOT NULL DEFAULT 'Pending',
    uploaded_by           BIGINT UNSIGNED NOT NULL,
    upload_date          DATETIME NOT NULL,
    storage_key          VARCHAR(255) NOT NULL,
    original_filename    VARCHAR(255) NOT NULL,
    file_size_bytes       BIGINT UNSIGNED NOT NULL DEFAULT 0,
    deleted_at            DATETIME NULL,
    CONSTRAINT fk_client_documents_client FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    CONSTRAINT fk_client_documents_user FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_client_documents_client (client_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS client_document_versions (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    document_id         BIGINT UNSIGNED NOT NULL,
    version             INT UNSIGNED NOT NULL,
    uploaded_by         BIGINT UNSIGNED NOT NULL,
    upload_date         DATETIME NOT NULL,
    notes               VARCHAR(500) NOT NULL DEFAULT '',
    storage_key         VARCHAR(255) NOT NULL,
    original_filename   VARCHAR(255) NOT NULL,
    file_size_bytes     BIGINT UNSIGNED NOT NULL DEFAULT 0,
    CONSTRAINT fk_client_document_versions_document FOREIGN KEY (document_id) REFERENCES client_documents(id) ON DELETE CASCADE,
    CONSTRAINT fk_client_document_versions_user FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_client_document_versions_document (document_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS client_verifications (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    client_id       BIGINT UNSIGNED NOT NULL,
    document_id     BIGINT UNSIGNED NULL,
    item            VARCHAR(150) NOT NULL,
    result          ENUM('Pending','Verified','Rejected') NOT NULL,
    verified_by     BIGINT UNSIGNED NOT NULL,
    verified_date   DATETIME NOT NULL,
    notes           VARCHAR(1000) NULL,
    CONSTRAINT fk_client_verifications_client FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    CONSTRAINT fk_client_verifications_document FOREIGN KEY (document_id) REFERENCES client_documents(id) ON DELETE SET NULL,
    CONSTRAINT fk_client_verifications_user FOREIGN KEY (verified_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_client_verifications_client (client_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS projects (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_no      VARCHAR(20)  NOT NULL UNIQUE,
    project_name    VARCHAR(200) NOT NULL,
    description     VARCHAR(2000) NULL,
    -- Internal approval of the scope-of-work text above -- set by the
    -- Requirement stage's Approve action (migration 0038), which is what
    -- gates the automatic move to "Quotation". scope_approved_at/_by
    -- record when/who; both NULL until first approved.
    scope_status        ENUM('Draft','Approved') NOT NULL DEFAULT 'Draft',
    scope_approved_at   DATETIME NULL,
    scope_approved_by   BIGINT UNSIGNED NULL,
    client_id       BIGINT UNSIGNED NOT NULL,
    service         VARCHAR(100) NOT NULL,
    engineer_id     BIGINT UNSIGNED NOT NULL,
    -- "Correction" was merged into "Review" (migration 0019) -- a
    -- correction cycle during review is logged as a reason-carrying
    -- project timeline note now, not a separate stage. "Enquiry" was
    -- itself renamed to "Requirement" (migration 0038) -- see
    -- project_scope_revisions below for the scope-of-work revision
    -- history that stage now manages. "Execution & Tracking" and
    -- "Completed" were removed entirely (migration 0051), along with
    -- the 5-gate Approval Process that used to gate entry into them --
    -- "Government Submission" is now the terminal stage.
    current_stage   ENUM('Requirement','Quotation','Contract','Design','Government Submission')
                        NOT NULL DEFAULT 'Requirement',
    progress        SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    priority        ENUM('High','Medium','Low') NOT NULL DEFAULT 'Medium',
    start_date      DATE NOT NULL,
    target_date     DATE NOT NULL,
    -- No "Completed" value (removed in migration 0051) -- a project
    -- never reaches a terminal "done" status, only Active/On
    -- Hold/Cancelled.
    status          ENUM('Active','On Hold','Cancelled') NOT NULL DEFAULT 'Active',
    stale_notified_at DATETIME NULL,
    service_total   DECIMAL(12,2) NULL,
    -- Permit names the client confirmed, at project setup, they already
    -- hold -- each becomes a mandatory upload requirement on the
    -- Documents tab (see ProjectDocumentsTab.vue's permitChecklist).
    required_permit_documents JSON NOT NULL DEFAULT (JSON_ARRAY()),
    type_category_name  VARCHAR(150) NULL,
    type_activity_total DECIMAL(12,2) NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at      DATETIME NULL,
    CONSTRAINT fk_projects_client FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE RESTRICT,
    CONSTRAINT fk_projects_engineer FOREIGN KEY (engineer_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_projects_scope_approved_by FOREIGN KEY (scope_approved_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_projects_client (client_id),
    INDEX idx_projects_status (status),
    INDEX idx_projects_deleted_at (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS project_scope_revisions (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id          BIGINT UNSIGNED NOT NULL,
    revision            VARCHAR(10) NOT NULL,
    scope_text          TEXT NOT NULL,
    storage_key         VARCHAR(300) NULL,
    original_filename   VARCHAR(255) NULL,
    file_size_bytes     BIGINT UNSIGNED NULL,
    revised_at          DATE NOT NULL,
    changed_by          BIGINT UNSIGNED NOT NULL,
    summary             TEXT NOT NULL,
    CONSTRAINT fk_project_scope_revisions_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_project_scope_revisions_user FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_project_scope_revisions_project (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS project_selected_activities (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id      BIGINT UNSIGNED NOT NULL,
    service_id      VARCHAR(20) NOT NULL,
    service_name    VARCHAR(150) NOT NULL,
    activity_id     VARCHAR(20) NOT NULL,
    activity_name   VARCHAR(150) NOT NULL,
    fixed_cost      DECIMAL(12,2) NOT NULL,
    CONSTRAINT fk_project_selected_activities_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_project_selected_activities_project (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS government_authorities (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    category        ENUM('Municipality','Fire Department','Electricity','Water','Environment') NOT NULL,
    website         VARCHAR(200) NOT NULL,
    description     TEXT NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at      DATETIME NULL,
    INDEX idx_government_authorities_deleted_at (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS government_forms (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    authority_id        BIGINT UNSIGNED NOT NULL,
    form_code           VARCHAR(40)  NOT NULL,
    title               VARCHAR(200) NOT NULL,
    version             VARCHAR(20)  NOT NULL,
    language            ENUM('English','Arabic','English / Arabic') NOT NULL,
    category            ENUM('Building Permit','Occupancy Certificate','Fire Safety Approval','Utility Connection','Environmental Clearance','Business License','Agreement','Legal Undertaking') NOT NULL,
    description         TEXT NOT NULL,
    required_documents  JSON NOT NULL,
    preview_url         VARCHAR(300) NULL,
    -- {{token}} merge-field body, e.g. {{clientName}}, {{projectName}},
    -- {{companyName}}, {{date}} -- see app/services/pdf_render.py and
    -- src/utils/governmentFormHelpers.ts's renderGovernmentFormTemplate.
    -- NULL for a form that's just a reference document, nothing to fill.
    template            TEXT NULL,
    -- Service Catalog service names this form is suggested for -- see
    -- governmentFormHelpers.formMatchesProjectService.
    service_tags        JSON NULL,
    -- Which {{token}}s in `template` get a dropdown or radio group
    -- instead of a plain text box when a project fills this form in --
    -- [{token, label, type, options}], type one of 'text'/'select'/
    -- 'radio'. A token with no entry here just falls back to text.
    fields               JSON NULL,
    -- An uploaded reference copy of the real government form -- not
    -- parsed, purely an attachment admin can check the template/fields
    -- against.
    sample_file_storage_key            VARCHAR(300) NULL,
    sample_file_original_filename      VARCHAR(255) NULL,
    sample_file_size_bytes             BIGINT NULL,
    status              ENUM('Active','Archived') NOT NULL DEFAULT 'Active',
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at          DATETIME NULL,
    CONSTRAINT fk_government_forms_authority FOREIGN KEY (authority_id) REFERENCES government_authorities(id) ON DELETE RESTRICT,
    INDEX idx_government_forms_authority (authority_id),
    INDEX idx_government_forms_deleted_at (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS government_submissions (
    id                          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    submission_no               VARCHAR(20) NOT NULL UNIQUE,
    project_id                  BIGINT UNSIGNED NOT NULL,
    authority_id                BIGINT UNSIGNED NOT NULL,
    form_id                     BIGINT UNSIGNED NOT NULL,
    status                      ENUM('Draft','Submitted','Under Review','Comments Received','Approved','Rejected','Withdrawn') NOT NULL DEFAULT 'Draft',
    submitted_date               DATE NULL,
    expected_decision_date       DATE NULL,
    decision_date                DATE NULL,
    notes                        TEXT NULL,
    proof_of_submission_storage_key   VARCHAR(300) NULL,
    proof_of_submission_filename      VARCHAR(255) NULL,
    proof_of_submission_size_bytes    BIGINT UNSIGNED NULL,
    proof_of_submission_uploaded_by   BIGINT UNSIGNED NULL,
    proof_of_submission_upload_date   DATE NULL,
    proof_of_response_storage_key     VARCHAR(300) NULL,
    proof_of_response_filename        VARCHAR(255) NULL,
    proof_of_response_size_bytes      BIGINT UNSIGNED NULL,
    proof_of_response_uploaded_by     BIGINT UNSIGNED NULL,
    proof_of_response_upload_date     DATE NULL,
    response_outcome                  ENUM('Approved','Rejected','No Response') NULL,
    created_at                   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at                   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at                   DATETIME NULL,
    CONSTRAINT fk_government_submissions_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_government_submissions_authority FOREIGN KEY (authority_id) REFERENCES government_authorities(id) ON DELETE RESTRICT,
    CONSTRAINT fk_government_submissions_form FOREIGN KEY (form_id) REFERENCES government_forms(id) ON DELETE RESTRICT,
    CONSTRAINT fk_government_submissions_proof_submission_by FOREIGN KEY (proof_of_submission_uploaded_by) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_government_submissions_proof_response_by FOREIGN KEY (proof_of_response_uploaded_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_government_submissions_project (project_id),
    INDEX idx_government_submissions_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS submission_documents (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    submission_id   BIGINT UNSIGNED NOT NULL,
    name            VARCHAR(150) NOT NULL,
    status          ENUM('Pending','Uploaded','Verified') NOT NULL DEFAULT 'Pending',
    storage_key       VARCHAR(300) NULL,
    original_filename VARCHAR(255) NULL,
    file_size_bytes    BIGINT UNSIGNED NULL,
    uploaded_by         BIGINT UNSIGNED NULL,
    upload_date          DATE NULL,
    CONSTRAINT fk_submission_documents_submission FOREIGN KEY (submission_id) REFERENCES government_submissions(id) ON DELETE CASCADE,
    CONSTRAINT fk_submission_documents_uploaded_by FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_submission_documents_submission (submission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS submission_followups (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    submission_id   BIGINT UNSIGNED NOT NULL,
    followup_date   DATE NOT NULL,
    followup_time   VARCHAR(20) NOT NULL,
    contact_person  VARCHAR(150) NOT NULL,
    notes           TEXT NULL,
    created_by      BIGINT UNSIGNED NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_submission_followups_submission FOREIGN KEY (submission_id) REFERENCES government_submissions(id) ON DELETE CASCADE,
    CONSTRAINT fk_submission_followups_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_submission_followups_submission (submission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS quotations (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    quotation_no        VARCHAR(20) NOT NULL UNIQUE,
    project_id          BIGINT UNSIGNED NOT NULL,
    revision            VARCHAR(10) NOT NULL DEFAULT 'R0',
    issue_date          DATE NOT NULL,
    validity            DATE NOT NULL,
    status              ENUM('Draft','Approved','Rejected','Expired') NOT NULL DEFAULT 'Draft',
    currency            VARCHAR(10) NOT NULL DEFAULT 'KWD',
    prepared_by         BIGINT UNSIGNED NOT NULL,
    discount_amount     DECIMAL(12,2) NOT NULL DEFAULT 0,
    notes               TEXT NULL,
    terms_and_conditions JSON NOT NULL,
    amount              DECIMAL(12,2) NOT NULL DEFAULT 0,
    -- NULL while still an editable draft; set once saved as Final,
    -- after which content is locked (migration 0053 removed the
    -- lettered-template fields this used to also gate -- the lock
    -- itself applies to every quotation, not just those).
    finalized_at        DATETIME NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at          DATETIME NULL,
    CONSTRAINT fk_quotations_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_quotations_prepared_by FOREIGN KEY (prepared_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_quotations_project (project_id),
    INDEX idx_quotations_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS quotation_line_items (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    quotation_id    BIGINT UNSIGNED NOT NULL,
    description     VARCHAR(300) NOT NULL,
    quantity        DECIMAL(10,2) NOT NULL,
    unit_price      DECIMAL(12,2) NOT NULL,
    CONSTRAINT fk_quotation_line_items_quotation FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE CASCADE,
    INDEX idx_quotation_line_items_quotation (quotation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS quotation_revisions (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    quotation_id    BIGINT UNSIGNED NOT NULL,
    revision        VARCHAR(10) NOT NULL,
    revised_at      DATE NOT NULL,
    changed_by      BIGINT UNSIGNED NOT NULL,
    summary         TEXT NOT NULL,
    CONSTRAINT fk_quotation_revisions_quotation FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE CASCADE,
    CONSTRAINT fk_quotation_revisions_user FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_quotation_revisions_quotation (quotation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS contracts (
    id                      BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    contract_no             VARCHAR(20) NOT NULL UNIQUE,
    project_id              BIGINT UNSIGNED NOT NULL,
    -- The quotation this contract was generated from (migration 0033).
    -- Nullable only for contracts that predate the rule that a contract
    -- must come from an Approved, finalized quotation.
    quotation_id            BIGINT UNSIGNED NULL,
    template_name           VARCHAR(150) NOT NULL,
    revision                VARCHAR(10) NOT NULL DEFAULT 'R0',
    currency                VARCHAR(10) NOT NULL DEFAULT 'KWD',
    contract_value          DECIMAL(12,2) NOT NULL,
    issue_date              DATE NOT NULL,
    signed_date             DATE NULL,
    expiry_date             DATE NOT NULL,
    status                  ENUM('Draft','Signed','Active','Expired','Terminated') NOT NULL DEFAULT 'Draft',
    prepared_by             BIGINT UNSIGNED NOT NULL,
    client_representative   VARCHAR(150) NOT NULL,
    scope_summary           TEXT NOT NULL,
    -- NULL while still an editable draft; set once saved as Final,
    -- after which content is locked (migration 0053 removed the
    -- lettered-template fields this used to also gate -- the lock
    -- itself applies to every contract, not just those).
    finalized_at            DATETIME NULL,
    created_at              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at              DATETIME NULL,
    CONSTRAINT fk_contracts_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_contracts_prepared_by FOREIGN KEY (prepared_by) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_contracts_quotation FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE RESTRICT,
    INDEX idx_contracts_project (project_id),
    INDEX idx_contracts_status (status),
    INDEX idx_contracts_quotation (quotation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS contract_clauses (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    contract_id     BIGINT UNSIGNED NOT NULL,
    title           VARCHAR(150) NOT NULL,
    content         TEXT NOT NULL,
    sort_order      INT NOT NULL DEFAULT 0,
    CONSTRAINT fk_contract_clauses_contract FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
    INDEX idx_contract_clauses_contract (contract_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS contract_revisions (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    contract_id     BIGINT UNSIGNED NOT NULL,
    revision        VARCHAR(10) NOT NULL,
    revised_at      DATE NOT NULL,
    changed_by      BIGINT UNSIGNED NOT NULL,
    summary         TEXT NOT NULL,
    CONSTRAINT fk_contract_revisions_contract FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
    CONSTRAINT fk_contract_revisions_user FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_contract_revisions_contract (contract_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS financial_agreements (
    id                      BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id              BIGINT UNSIGNED NOT NULL,
    contract_amount         DECIMAL(12,2) NOT NULL,
    currency                VARCHAR(10) NOT NULL DEFAULT 'KWD',
    contract_start_date     DATE NOT NULL,
    contract_end_date       DATE NULL,
    agreement_date          DATE NOT NULL,
    quotation_reference     VARCHAR(30) NULL,
    contract_reference      VARCHAR(30) NULL,
    payment_mode            ENUM('Cash','Bank Transfer','Credit Card','Debit Card','Online Payment','Cheque','Other') NOT NULL,
    payment_frequency       ENUM('One-time','Daily','Weekly','Monthly','Quarterly','Half-yearly','Yearly','Custom') NOT NULL,
    CONSTRAINT fk_financial_agreements_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    -- Only one agreement per project -- the staff UI already only ever
    -- offers "Create Agreement" when none exists yet, this makes that a
    -- real, enforced rule rather than just a UI convention (see
    -- migration 0015 and payment_service.create_agreement's own
    -- proactive check for a clearer error message than a raw
    -- constraint violation).
    CONSTRAINT uq_financial_agreements_project UNIQUE (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS payment_obligations (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    agreement_id        BIGINT UNSIGNED NOT NULL,
    sequence_number     SMALLINT UNSIGNED NOT NULL,
    description         VARCHAR(200) NOT NULL,
    amount_due          DECIMAL(12,2) NOT NULL,
    due_date            DATE NOT NULL,
    amount_received     DECIMAL(12,2) NOT NULL DEFAULT 0,
    manual_status       ENUM('Cancelled','Waived') NULL,
    date_paid           DATE NULL,
    payment_method      ENUM('Cash','Bank Transfer','Credit Card','Debit Card','Online Payment','Cheque','Other') NULL,
    reference_number    VARCHAR(60) NULL,
    notes               TEXT NULL,
    reminder_before_sent_at DATETIME NULL,
    reminder_due_sent_at    DATETIME NULL,
    reminder_after_sent_at  DATETIME NULL,
    CONSTRAINT fk_payment_obligations_agreement FOREIGN KEY (agreement_id) REFERENCES financial_agreements(id) ON DELETE CASCADE,
    UNIQUE KEY uq_payment_obligations_agreement_sequence (agreement_id, sequence_number),
    INDEX idx_payment_obligations_agreement (agreement_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS payments (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    agreement_id        BIGINT UNSIGNED NOT NULL,
    project_id          BIGINT UNSIGNED NOT NULL,
    amount_received     DECIMAL(12,2) NOT NULL,
    payment_date        DATE NOT NULL,
    payment_mode        ENUM('Cash','Bank Transfer','Credit Card','Debit Card','Online Payment','Cheque','Other') NOT NULL,
    reference_number    VARCHAR(60) NULL,
    payer               VARCHAR(150) NOT NULL,
    receiving_account   VARCHAR(150) NULL,
    notes               TEXT NULL,
    created_by          BIGINT UNSIGNED NOT NULL,
    created_at          DATETIME NOT NULL,
    CONSTRAINT fk_payments_agreement FOREIGN KEY (agreement_id) REFERENCES financial_agreements(id) ON DELETE RESTRICT,
    CONSTRAINT fk_payments_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_payments_user FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_payments_agreement (agreement_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS payment_allocations (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    payment_id          BIGINT UNSIGNED NOT NULL,
    obligation_id       BIGINT UNSIGNED NOT NULL,
    amount_allocated    DECIMAL(12,2) NOT NULL,
    CONSTRAINT fk_payment_allocations_payment FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE CASCADE,
    CONSTRAINT fk_payment_allocations_obligation FOREIGN KEY (obligation_id) REFERENCES payment_obligations(id) ON DELETE RESTRICT,
    INDEX idx_payment_allocations_payment (payment_id),
    INDEX idx_payment_allocations_obligation (obligation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS refunds (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    payment_id          BIGINT UNSIGNED NULL,
    agreement_id        BIGINT UNSIGNED NOT NULL,
    obligation_id       BIGINT UNSIGNED NOT NULL,
    refund_amount       DECIMAL(12,2) NOT NULL,
    refund_date         DATE NOT NULL,
    reason              TEXT NOT NULL,
    authorising_user    BIGINT UNSIGNED NOT NULL,
    reference           VARCHAR(60) NULL,
    CONSTRAINT fk_refunds_payment FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE SET NULL,
    CONSTRAINT fk_refunds_agreement FOREIGN KEY (agreement_id) REFERENCES financial_agreements(id) ON DELETE RESTRICT,
    CONSTRAINT fk_refunds_obligation FOREIGN KEY (obligation_id) REFERENCES payment_obligations(id) ON DELETE RESTRICT,
    CONSTRAINT fk_refunds_user FOREIGN KEY (authorising_user) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_refunds_agreement (agreement_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS adjustments (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    agreement_id        BIGINT UNSIGNED NOT NULL,
    obligation_id       BIGINT UNSIGNED NOT NULL,
    type                ENUM('Increase','Decrease','Correction') NOT NULL,
    amount              DECIMAL(12,2) NOT NULL,
    reason              TEXT NOT NULL,
    authorising_user    BIGINT UNSIGNED NOT NULL,
    adjusted_at         DATE NOT NULL,
    CONSTRAINT fk_adjustments_agreement FOREIGN KEY (agreement_id) REFERENCES financial_agreements(id) ON DELETE RESTRICT,
    CONSTRAINT fk_adjustments_obligation FOREIGN KEY (obligation_id) REFERENCES payment_obligations(id) ON DELETE RESTRICT,
    CONSTRAINT fk_adjustments_user FOREIGN KEY (authorising_user) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_adjustments_agreement (agreement_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS project_documents (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    document_no         VARCHAR(20) NOT NULL UNIQUE,
    project_id          BIGINT UNSIGNED NOT NULL,
    title               VARCHAR(200) NOT NULL,
    -- 'Government Agreement' is a PDF generated by filling in a
    -- government form's template for this project (see
    -- government_service.fill_form) -- distinct from 'Municipality
    -- Form', a manually uploaded scan with no generation involved.
    type                ENUM('Drawing','Report','Contract','Quotation','Municipality Form','Calculation Sheet','Government Agreement') NOT NULL,
    revision            VARCHAR(10) NOT NULL DEFAULT 'Rev A',
    -- Which GovernmentForm this was generated from (see
    -- government_service.fill_form) -- NULL for anything not generated
    -- that way (uploads, contracts, quotations, etc.).
    source_form_id      BIGINT UNSIGNED NULL,
    uploaded_by         BIGINT UNSIGNED NOT NULL,
    upload_date         DATE NOT NULL,
    status              ENUM('Draft','Under Review','Approved','Rejected') NOT NULL DEFAULT 'Draft',
    -- All three NULL -- a row can be a plain external link with no
    -- uploaded file at all (see external_link below), an uploaded file
    -- with no link, or both; document_service.create_document requires
    -- at least one of the two at the application layer.
    storage_key         VARCHAR(300) NULL,
    original_filename   VARCHAR(255) NULL,
    file_size_bytes     BIGINT UNSIGNED NULL,
    -- A link to a document that lives outside the app (a shared drive,
    -- cloud folder, etc.) -- same idea as ProjectLinkDocument, but on
    -- ProjectDocument itself so the Design tab's list can mix uploaded
    -- files and external links in one CRUD table.
    external_link       VARCHAR(1000) NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at          DATETIME NULL,
    CONSTRAINT fk_project_documents_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_project_documents_user FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_project_documents_source_form FOREIGN KEY (source_form_id) REFERENCES government_forms(id) ON DELETE SET NULL,
    INDEX idx_project_documents_project (project_id),
    INDEX idx_project_documents_status (status),
    INDEX idx_project_documents_source_form (source_form_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- One government form, filled in and saved for one project -- the
-- Approvals & Permits tab's own record, organized by the form's
-- authority (MEW/KFD/Baladia/...) there. Saving does two things in one
-- action: persists field_values here AND renders the same data to a PDF
-- saved as a project_documents row (document_id) -- see
-- project_form_service.create_project_form_entry. A project can only
-- have one entry per form (uq_project_form_entries_project_form below)
-- -- refilling means editing this same entry, not creating a second one.
CREATE TABLE IF NOT EXISTS project_form_entries (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id          BIGINT UNSIGNED NOT NULL,
    form_id             BIGINT UNSIGNED NOT NULL,
    -- Keyed by the template's {{token}} names -- see government_forms.
    -- fields for which of them are dropdowns/radio groups vs. text.
    field_values        JSON NOT NULL,
    status              ENUM('Draft','Submitted','Under Review','Comments Received','Approved','Rejected','Withdrawn') NOT NULL DEFAULT 'Draft',
    -- The generated PDF -- see project_documents above. Download/Print
    -- are only ever offered once this row exists at all.
    document_id         BIGINT UNSIGNED NULL,
    created_by           BIGINT UNSIGNED NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_project_form_entries_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_project_form_entries_form FOREIGN KEY (form_id) REFERENCES government_forms(id) ON DELETE RESTRICT,
    CONSTRAINT fk_project_form_entries_document FOREIGN KEY (document_id) REFERENCES project_documents(id) ON DELETE SET NULL,
    CONSTRAINT fk_project_form_entries_user FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT uq_project_form_entries_project_form UNIQUE (project_id, form_id),
    INDEX idx_project_form_entries_project (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS document_versions (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    document_id         BIGINT UNSIGNED NOT NULL,
    revision            VARCHAR(10) NOT NULL,
    uploaded_by         BIGINT UNSIGNED NOT NULL,
    upload_date         DATE NOT NULL,
    notes               TEXT NOT NULL,
    storage_key         VARCHAR(300) NOT NULL,
    original_filename   VARCHAR(255) NOT NULL,
    file_size_bytes     BIGINT UNSIGNED NOT NULL,
    CONSTRAINT fk_document_versions_document FOREIGN KEY (document_id) REFERENCES project_documents(id) ON DELETE CASCADE,
    CONSTRAINT fk_document_versions_user FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_document_versions_document (document_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS project_link_documents (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    link_document_no    VARCHAR(20) NOT NULL UNIQUE,
    project_id          BIGINT UNSIGNED NOT NULL,
    category            ENUM('Property','Government','Others','Project Closure') NOT NULL,
    name                VARCHAR(200) NOT NULL,
    path                VARCHAR(1000) NOT NULL,
    added_by            BIGINT UNSIGNED NOT NULL,
    added_date          DATE NOT NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at          DATETIME NULL,
    CONSTRAINT fk_project_link_documents_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_project_link_documents_user FOREIGN KEY (added_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_project_link_documents_project (project_id),
    INDEX idx_project_link_documents_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS knowledge_documents (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    document_no         VARCHAR(20) NOT NULL UNIQUE,
    title               VARCHAR(200) NOT NULL,
    storage_key         VARCHAR(300) NOT NULL,
    original_filename   VARCHAR(255) NOT NULL,
    file_size_bytes     BIGINT UNSIGNED NOT NULL,
    -- Extracted-text file kind, not the browser MIME type: pdf|docx|txt.
    content_type        VARCHAR(20) NOT NULL,
    extracted_text       LONGTEXT NOT NULL,
    char_count          INT UNSIGNED NOT NULL DEFAULT 0,
    truncated           TINYINT(1) NOT NULL DEFAULT 0,
    extraction_ok        TINYINT(1) NOT NULL DEFAULT 1,
    extraction_error     VARCHAR(500) NOT NULL DEFAULT '',
    is_active           TINYINT(1) NOT NULL DEFAULT 1,
    uploaded_by         BIGINT UNSIGNED NOT NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_knowledge_documents_user FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_knowledge_documents_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Caches an LLM answer for a (document scope, normalized question) pair so
-- an identical question against the same document(s) doesn't re-call the
-- provider -- see AIConfiguration.cache_duration_minutes for the TTL and
-- app/services/knowledge_service.py for the cache key construction.
CREATE TABLE IF NOT EXISTS knowledge_qa_cache (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    scope_key           VARCHAR(64) NOT NULL,
    question_hash       CHAR(64) NOT NULL,
    question_text       TEXT NOT NULL,
    answer_text         MEDIUMTEXT NOT NULL,
    source_document_ids JSON NOT NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_knowledge_qa_cache_scope_question (scope_key, question_hash),
    INDEX idx_knowledge_qa_cache_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS tasks (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    task_no         VARCHAR(20) NOT NULL UNIQUE,
    project_id      BIGINT UNSIGNED NOT NULL,
    title           VARCHAR(200) NOT NULL,
    assigned_to     BIGINT UNSIGNED NOT NULL,
    priority        ENUM('High','Medium','Low') NOT NULL DEFAULT 'Medium',
    severity        ENUM('Critical','Major','Minor') NOT NULL DEFAULT 'Minor',
    due_date        DATE NOT NULL,
    due_time        TIME NOT NULL,
    status          ENUM('Pending','In Progress','Completed') NOT NULL DEFAULT 'Pending',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at      DATETIME NULL,
    CONSTRAINT fk_tasks_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_tasks_assignee FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_tasks_project (project_id),
    INDEX idx_tasks_status (status),
    INDEX idx_tasks_assignee (assigned_to)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS notifications (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    notification_no     VARCHAR(20) NOT NULL UNIQUE,
    user_id             BIGINT UNSIGNED NOT NULL,
    title               VARCHAR(150) NOT NULL,
    message             TEXT NOT NULL,
    category            ENUM('Project','Task','Government','Payment','AI','System') NOT NULL,
    created_at          DATETIME NOT NULL,
    `read`              TINYINT(1) NOT NULL DEFAULT 0,
    link_route_name     VARCHAR(100) NULL,
    link_params         JSON NULL,
    CONSTRAINT fk_notifications_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_notifications_user (user_id),
    INDEX idx_notifications_user_read (user_id, `read`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS message_templates (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    channel         ENUM('Email','SMS','WhatsApp') NOT NULL,
    body            TEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS message_log (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    client_id       BIGINT UNSIGNED NOT NULL,
    channel         ENUM('Email','SMS','WhatsApp') NOT NULL,
    template_id     BIGINT UNSIGNED NULL,
    body            TEXT NOT NULL,
    project_id      BIGINT UNSIGNED NULL,
    status          ENUM('Sent','Failed') NOT NULL,
    sent_at         DATETIME NOT NULL,
    CONSTRAINT fk_message_log_client FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE RESTRICT,
    CONSTRAINT fk_message_log_template FOREIGN KEY (template_id) REFERENCES message_templates(id) ON DELETE SET NULL,
    CONSTRAINT fk_message_log_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
    INDEX idx_message_log_client (client_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Note: no generic, admin-editable "workflow_templates"/"workflow_stages"
-- system exists here. One used to, but it was never wired to anything
-- real (projects.current_stage, defined above, is a fixed ENUM, not
-- driven by rows in a table) -- it only duplicated and drifted from
-- the real stage list. Removed rather than kept as unused surface area
-- (migration 0018). projects.current_stage (defined above) is the only
-- notion of "the stages a project goes through" -- the execution-step
-- checklist and Project Approval Process that used to run alongside it
-- were removed entirely in migration 0051.

CREATE TABLE IF NOT EXISTS service_catalog_items (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at      DATETIME NULL,
    -- NULL for soft-deleted rows (so a deleted service's name can be
    -- reused), the lowercased name for active ones -- MySQL/MariaDB
    -- treat multiple NULLs in a UNIQUE index as non-conflicting, so
    -- this enforces case-insensitive uniqueness only among active rows,
    -- matching what _assert_name_available already checks at the
    -- application layer, now also as a real, race-proof constraint
    -- (see migration 0037).
    active_name_lower VARCHAR(150) GENERATED ALWAYS AS (IF(deleted_at IS NULL, LOWER(name), NULL)) STORED,
    INDEX idx_service_catalog_items_name (name),
    UNIQUE KEY uq_service_catalog_items_active_name (active_name_lower)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS service_catalog_activities (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    service_id      BIGINT UNSIGNED NOT NULL,
    name            VARCHAR(150) NOT NULL,
    fixed_cost      DECIMAL(12,2) NOT NULL DEFAULT 0,
    CONSTRAINT fk_service_catalog_activities_service
        FOREIGN KEY (service_id) REFERENCES service_catalog_items(id) ON DELETE CASCADE,
    INDEX idx_service_catalog_activities_service (service_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Was referenced by app/models/permit_catalog.py and queried by
-- /api/permit-catalog/permits (the New Project wizard's Permits step),
-- but missing here entirely -- a fresh install 500s that step the
-- moment it loads. Flat, like service_catalog_items minus the
-- activities sub-level (see PermitCatalogItem's own docstring): a
-- permit is picked as a whole, not broken into priced sub-items.
CREATE TABLE IF NOT EXISTS permit_catalog_items (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at      DATETIME NULL,
    INDEX idx_permit_catalog_items_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Almailam only ever files for these two Kuwait authorities -- seeded
-- here rather than left for an admin to type in by hand on day one.
-- Still fully admin-editable afterward from Admin > Permit Catalog.
INSERT INTO permit_catalog_items (name) VALUES ('Baladia Permits'), ('KFD Permits');

-- New Project wizard's final step: pick an engagement type category
-- (Design/Supervision/etc, admin-managed here) then check off which of
-- its activities apply. Same shape as service_catalog_items/_activities
-- above -- see type_activity_catalog.py's model docstrings for why this
-- is a separate catalog from services rather than reusing that one.
CREATE TABLE IF NOT EXISTS type_activity_categories (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at  DATETIME NULL,
    INDEX idx_type_activity_categories_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS type_activity_items (
    id           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    category_id  BIGINT UNSIGNED NOT NULL,
    name         VARCHAR(150) NOT NULL,
    cost         DECIMAL(12,2) NOT NULL DEFAULT 0,
    CONSTRAINT fk_type_activity_items_category FOREIGN KEY (category_id)
        REFERENCES type_activity_categories(id),
    INDEX idx_type_activity_items_category (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO type_activity_categories (id, name) VALUES
    (1, 'Design'),
    (2, 'Supervision');

INSERT INTO type_activity_items (category_id, name, cost) VALUES
    (1, 'Site Inspection', 150.00),
    (1, 'Concept Drawings', 300.00),
    (1, 'Structural Calculations', 400.00),
    (1, 'Coordination with Authorities', 200.00),
    (2, 'Weekly Site Visits', 250.00),
    (2, 'Progress Reporting', 100.00),
    (2, 'Materials Testing Coordination', 150.00),
    (2, 'Snagging & Handover Inspection', 200.00);

-- One row per activity checked in that final wizard step -- snapshot of
-- name/cost/coverage at creation time, same reasoning as
-- project_selected_activities above (a later catalog rename or price
-- change shouldn't retroactively alter what this project was quoted).
CREATE TABLE IF NOT EXISTS project_selected_type_activities (
    id                     BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id             BIGINT UNSIGNED NOT NULL,
    type_activity_item_id  VARCHAR(20) NOT NULL,
    activity_name          VARCHAR(150) NOT NULL,
    cost                   DECIMAL(12,2) NOT NULL,
    is_covered_by_service  TINYINT(1) NOT NULL DEFAULT 0,
    CONSTRAINT fk_project_selected_type_activities_project FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_project_selected_type_activities_project (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS company_settings (
    id                                  INT PRIMARY KEY DEFAULT 1,
    company_name                       VARCHAR(150) NOT NULL DEFAULT 'Al Mailam Consulting',
    tagline                            VARCHAR(200) NOT NULL DEFAULT '',
    trade_license_number               VARCHAR(80)  NOT NULL DEFAULT '',
    email                              VARCHAR(150) NOT NULL DEFAULT '',
    phone                              VARCHAR(30)  NOT NULL DEFAULT '',
    website                            VARCHAR(150) NOT NULL DEFAULT '',
    address                            VARCHAR(250) NOT NULL DEFAULT '',
    city                               VARCHAR(80)  NOT NULL DEFAULT '',
    country                            VARCHAR(80)  NOT NULL DEFAULT '',
    brand_color                        VARCHAR(20)  NOT NULL DEFAULT '#1D4ED8',
    default_language                   VARCHAR(20)  NOT NULL DEFAULT 'English',
    timezone                           VARCHAR(60)  NOT NULL DEFAULT 'Asia/Dubai',
    date_format                        VARCHAR(20)  NOT NULL DEFAULT 'DD/MM/YYYY',
    currency                           VARCHAR(10)  NOT NULL DEFAULT 'AED',
    default_payment_terms_days         INT UNSIGNED NOT NULL DEFAULT 30,
    default_quotation_validity_days    INT UNSIGNED NOT NULL DEFAULT 14,
    stale_project_alert_days           INT UNSIGNED NOT NULL DEFAULT 45,
    stale_onboarding_alert_days        INT UNSIGNED NOT NULL DEFAULT 5,
    status_report_recipient_id         BIGINT UNSIGNED NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_company_settings_singleton CHECK (id = 1),
    CONSTRAINT fk_company_settings_status_report_recipient
        FOREIGN KEY (status_report_recipient_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS project_timeline_events (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id      BIGINT UNSIGNED NOT NULL,
    type            ENUM('stage','document','quotation','contract','submission','milestone','task','note','field_activity') NOT NULL,
    title           VARCHAR(200) NOT NULL,
    description     TEXT NULL,
    event_date      DATE NOT NULL,
    status          ENUM('completed','in-progress','upcoming') NOT NULL,
    created_by      BIGINT UNSIGNED NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_project_timeline_events_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_project_timeline_events_user FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_project_timeline_events_project (project_id, event_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- The execution-step checklist, the Project Approval Process (5
-- external sign-off gates), and the admin-configurable step-set system
-- that backed them were removed entirely in migration 0051, along with
-- the "Execution & Tracking" and "Completed" project stages they
-- existed to serve.

CREATE TABLE IF NOT EXISTS status_reports (
    id                          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    report_no                   VARCHAR(20)  NOT NULL UNIQUE,
    project_id                  BIGINT UNSIGNED NOT NULL,
    engineer_id                 BIGINT UNSIGNED NOT NULL,
    report_date                 DATE NOT NULL,
    receipt_type                VARCHAR(200) NULL,
    supervision_type            ENUM('Full-time','Part-time') NOT NULL DEFAULT 'Full-time',
    notes                       TEXT NOT NULL,
    status                      ENUM('Pending','Attached') NOT NULL DEFAULT 'Pending',
    attached_task_id            BIGINT UNSIGNED NULL,
    attached_timeline_event_id  BIGINT UNSIGNED NULL,
    attached_by                 BIGINT UNSIGNED NULL,
    attached_at                 DATETIME NULL,
    created_at                  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at                  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_status_reports_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_status_reports_engineer FOREIGN KEY (engineer_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_status_reports_task FOREIGN KEY (attached_task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    CONSTRAINT fk_status_reports_timeline_event FOREIGN KEY (attached_timeline_event_id) REFERENCES project_timeline_events(id) ON DELETE SET NULL,
    CONSTRAINT fk_status_reports_attached_by FOREIGN KEY (attached_by) REFERENCES users(id) ON DELETE SET NULL,
    -- One report per engineer *per project* per day -- an engineer on
    -- several projects files a separate report for each; "file today's
    -- report" is scoped to (engineer, project, day), not just (engineer, day).
    CONSTRAINT uq_status_reports_engineer_project_date UNIQUE (engineer_id, project_id, report_date),
    INDEX idx_status_reports_project (project_id),
    INDEX idx_status_reports_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ai_configuration (
    id                          INT PRIMARY KEY DEFAULT 1,
    is_enabled                  TINYINT(1) NOT NULL DEFAULT 0,
    default_provider            VARCHAR(20) NOT NULL DEFAULT 'claude',
    provider_priority           JSON NOT NULL,
    timeout_seconds             INT UNSIGNED NOT NULL DEFAULT 30,
    max_tokens                  INT UNSIGNED NOT NULL DEFAULT 2000,
    temperature                 DECIMAL(3,2) NOT NULL DEFAULT 0.30,
    -- Also the knowledgebase Q&A answer-cache TTL (see knowledge_qa_cache).
    cache_duration_minutes      INT UNSIGNED NOT NULL DEFAULT 15,
    retry_limit                 INT UNSIGNED NOT NULL DEFAULT 2,
    kb_system_prompt            TEXT NULL,
    kb_max_upload_size_mb       INT UNSIGNED NOT NULL DEFAULT 20,
    kb_max_document_chars       INT UNSIGNED NOT NULL DEFAULT 60000,
    kb_max_context_chars        INT UNSIGNED NOT NULL DEFAULT 150000,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_ai_configuration_singleton CHECK (id = 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ai_provider_configs (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    provider_id         VARCHAR(20) NOT NULL UNIQUE,
    label               VARCHAR(80) NOT NULL,
    model               VARCHAR(120) NOT NULL DEFAULT '',
    api_key_encrypted   TEXT NULL,
    has_api_key         TINYINT(1) NOT NULL DEFAULT 0,
    api_key_hint        VARCHAR(4) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;
