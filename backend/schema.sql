SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS users (
    id                      BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username                VARCHAR(50)  NOT NULL UNIQUE,
    email                   VARCHAR(120) NOT NULL UNIQUE,
    password_hash           VARCHAR(255) NOT NULL,
    full_name               VARCHAR(120) NOT NULL,
    designation             VARCHAR(120) NULL,
    mobile                  VARCHAR(30)  NULL,
    role                    ENUM('Administrator','Project Manager','Engineer','Document Controller','Viewer')
                                NOT NULL DEFAULT 'Viewer',
    is_active               TINYINT(1) NOT NULL DEFAULT 1,
    failed_login_attempts   SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    locked_until            DATETIME NULL,
    created_at              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at              DATETIME NULL,
    INDEX idx_users_role (role),
    INDEX idx_users_deleted_at (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    jti             CHAR(36)     NOT NULL UNIQUE,
    user_id         BIGINT UNSIGNED NOT NULL,
    revoked         TINYINT(1)   NOT NULL DEFAULT 0,
    expires_at      DATETIME     NOT NULL,
    created_at      DATETIME     NOT NULL,
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
    onboarding_state                ENUM('Information Required','Documents Required','Verification Required','Under Review','Ready','Rejected','Suspended')
                                        NOT NULL DEFAULT 'Information Required',
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
    created_at                      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at                      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at                      DATETIME NULL,
    INDEX idx_clients_status (status),
    INDEX idx_clients_onboarding_state (onboarding_state),
    INDEX idx_clients_deleted_at (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS client_contacts (
    id                          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    client_id                   BIGINT UNSIGNED NOT NULL,
    name                        VARCHAR(120) NOT NULL,
    contact_type                ENUM('Primary Contact','Billing Contact','Legal Contact','Authorised Representative','Technical Contact','Other') NOT NULL,
    mobile                      VARCHAR(30)  NOT NULL,
    email                       VARCHAR(120) NOT NULL,
    is_authorised_representative TINYINT(1) NOT NULL DEFAULT 0,
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
    CONSTRAINT fk_client_addresses_client FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    INDEX idx_client_addresses_client (client_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS client_identifications (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    client_id           BIGINT UNSIGNED NOT NULL,
    document_type       ENUM('Emirates ID','Passport','Trade Licence','Other') NOT NULL,
    document_number     VARCHAR(60) NOT NULL,
    issue_date          DATE NOT NULL,
    expiry_date         DATE NOT NULL,
    issuing_country     VARCHAR(80) NOT NULL,
    CONSTRAINT fk_client_identifications_client FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    INDEX idx_client_identifications_client (client_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS client_consents (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    client_id       BIGINT UNSIGNED NOT NULL,
    consent_type    ENUM('Process Personal Information','Electronic Communication','Receive Notifications','Process Documents') NOT NULL,
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
    CONSTRAINT fk_client_documents_client FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    CONSTRAINT fk_client_documents_user FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_client_documents_client (client_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS client_verifications (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    client_id       BIGINT UNSIGNED NOT NULL,
    item            VARCHAR(150) NOT NULL,
    result          ENUM('Pending','Verified','Rejected') NOT NULL,
    verified_by     BIGINT UNSIGNED NOT NULL,
    verified_date   DATETIME NOT NULL,
    notes           VARCHAR(1000) NULL,
    CONSTRAINT fk_client_verifications_client FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    CONSTRAINT fk_client_verifications_user FOREIGN KEY (verified_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_client_verifications_client (client_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS projects (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_no      VARCHAR(20)  NOT NULL UNIQUE,
    project_name    VARCHAR(200) NOT NULL,
    client_id       BIGINT UNSIGNED NOT NULL,
    service         VARCHAR(100) NOT NULL,
    engineer_id     BIGINT UNSIGNED NOT NULL,
    current_stage   ENUM('Enquiry','Quotation','Contract','Design','Government Submission','Review','Correction','Approval','Completed')
                        NOT NULL DEFAULT 'Enquiry',
    progress        SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    priority        ENUM('High','Medium','Low') NOT NULL DEFAULT 'Medium',
    start_date      DATE NOT NULL,
    target_date     DATE NOT NULL,
    status          ENUM('Active','On Hold','Completed','Cancelled') NOT NULL DEFAULT 'Active',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at      DATETIME NULL,
    CONSTRAINT fk_projects_client FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE RESTRICT,
    CONSTRAINT fk_projects_engineer FOREIGN KEY (engineer_id) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_projects_client (client_id),
    INDEX idx_projects_status (status),
    INDEX idx_projects_deleted_at (deleted_at)
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
    category            ENUM('Building Permit','Occupancy Certificate','Fire Safety Approval','Utility Connection','Environmental Clearance','Business License') NOT NULL,
    description         TEXT NOT NULL,
    required_documents  JSON NOT NULL,
    preview_url         VARCHAR(300) NULL,
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
    status                      ENUM('Draft','Submitted','Under Review','Comments Received','Approved','Rejected') NOT NULL DEFAULT 'Draft',
    submitted_date               DATE NULL,
    expected_decision_date       DATE NULL,
    decision_date                DATE NULL,
    notes                        TEXT NULL,
    created_at                   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at                   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at                   DATETIME NULL,
    CONSTRAINT fk_government_submissions_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_government_submissions_authority FOREIGN KEY (authority_id) REFERENCES government_authorities(id) ON DELETE RESTRICT,
    CONSTRAINT fk_government_submissions_form FOREIGN KEY (form_id) REFERENCES government_forms(id) ON DELETE RESTRICT,
    INDEX idx_government_submissions_project (project_id),
    INDEX idx_government_submissions_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS submission_documents (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    submission_id   BIGINT UNSIGNED NOT NULL,
    name            VARCHAR(150) NOT NULL,
    status          ENUM('Pending','Uploaded','Verified') NOT NULL DEFAULT 'Pending',
    CONSTRAINT fk_submission_documents_submission FOREIGN KEY (submission_id) REFERENCES government_submissions(id) ON DELETE CASCADE,
    INDEX idx_submission_documents_submission (submission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS quotations (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    quotation_no        VARCHAR(20) NOT NULL UNIQUE,
    project_id          BIGINT UNSIGNED NOT NULL,
    revision            VARCHAR(10) NOT NULL DEFAULT 'R0',
    issue_date          DATE NOT NULL,
    validity            DATE NOT NULL,
    status              ENUM('Draft','Sent','Approved','Rejected','Expired') NOT NULL DEFAULT 'Draft',
    currency            VARCHAR(10) NOT NULL DEFAULT 'KWD',
    prepared_by         BIGINT UNSIGNED NOT NULL,
    tax_rate_percent    DECIMAL(5,2) NOT NULL DEFAULT 0,
    discount_amount     DECIMAL(12,2) NOT NULL DEFAULT 0,
    notes               TEXT NULL,
    terms_and_conditions JSON NOT NULL,
    amount              DECIMAL(12,2) NOT NULL DEFAULT 0,
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

CREATE TABLE IF NOT EXISTS contracts (
    id                      BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    contract_no             VARCHAR(20) NOT NULL UNIQUE,
    project_id              BIGINT UNSIGNED NOT NULL,
    template_name           VARCHAR(150) NOT NULL,
    revision                VARCHAR(10) NOT NULL DEFAULT 'R0',
    currency                VARCHAR(10) NOT NULL DEFAULT 'KWD',
    contract_value          DECIMAL(12,2) NOT NULL,
    issue_date              DATE NOT NULL,
    signed_date             DATE NULL,
    expiry_date             DATE NOT NULL,
    status                  ENUM('Draft','Sent','Signed','Active','Expired','Terminated') NOT NULL DEFAULT 'Draft',
    prepared_by             BIGINT UNSIGNED NOT NULL,
    client_representative   VARCHAR(150) NOT NULL,
    scope_summary           TEXT NOT NULL,
    created_at              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at              DATETIME NULL,
    CONSTRAINT fk_contracts_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_contracts_prepared_by FOREIGN KEY (prepared_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_contracts_project (project_id),
    INDEX idx_contracts_status (status)
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
    INDEX idx_financial_agreements_project (project_id)
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
    type                ENUM('Drawing','Report','Contract','Quotation','Municipality Form','Calculation Sheet') NOT NULL,
    revision            VARCHAR(10) NOT NULL DEFAULT 'Rev A',
    uploaded_by         BIGINT UNSIGNED NOT NULL,
    upload_date         DATE NOT NULL,
    status              ENUM('Draft','Under Review','Approved','Rejected') NOT NULL DEFAULT 'Draft',
    storage_key         VARCHAR(300) NOT NULL,
    original_filename   VARCHAR(255) NOT NULL,
    file_size_bytes     BIGINT UNSIGNED NOT NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at          DATETIME NULL,
    CONSTRAINT fk_project_documents_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_project_documents_user FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_project_documents_project (project_id),
    INDEX idx_project_documents_status (status)
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

CREATE TABLE IF NOT EXISTS document_ai_reviews (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    document_id         BIGINT UNSIGNED NOT NULL,
    summary             TEXT NOT NULL,
    details             TEXT NOT NULL,
    confidence          ENUM('high','medium','low') NOT NULL,
    extracted_fields    JSON NOT NULL,
    suggestions         JSON NOT NULL,
    created_at          DATETIME NOT NULL,
    CONSTRAINT fk_document_ai_reviews_document FOREIGN KEY (document_id) REFERENCES project_documents(id) ON DELETE CASCADE,
    INDEX idx_document_ai_reviews_document (document_id)
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
    category            ENUM('Project','Task','Government','AI','System') NOT NULL,
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

CREATE TABLE IF NOT EXISTS workflow_templates (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(120) NOT NULL,
    is_default      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at      DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS workflow_stages (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    template_id     BIGINT UNSIGNED NOT NULL,
    name            VARCHAR(120) NOT NULL,
    description     TEXT NULL,
    sequence_number INT NOT NULL,
    CONSTRAINT fk_workflow_stages_template
        FOREIGN KEY (template_id) REFERENCES workflow_templates(id) ON DELETE CASCADE,
    INDEX idx_workflow_stages_template (template_id, sequence_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;
