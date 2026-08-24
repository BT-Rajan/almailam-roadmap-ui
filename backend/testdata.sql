-- ============================================================================
-- ServiceOS / Al Mailam Roadmap -- Test Data
-- ============================================================================
-- Populates a fresh database (after schema.sql has been applied) with a
-- small, internally-consistent set of demo data so the application has
-- something real to show end to end: clients, projects at different
-- workflow stages, quotations, contracts, payments, government
-- submissions, documents, tasks, and notifications.
--
-- This is NOT the same thing as the frontend mock data that used to live
-- in src/mock/ (removed) -- this seeds the real backend database, so
-- everything you see when browsing the app after loading this file is
-- coming from real GET requests against real rows, exactly like data a
-- real user entered would.
--
-- Usage:
--   mysql -u root -p almailam < schema.sql
--   mysql -u root -p almailam < testdata.sql
--
-- All seeded users share the password: Demo#2026
-- (the app's own admin bootstrap script, scripts/create_admin.py, is a
-- separate, simpler way to get just one working login -- use this file
-- when you want the app to feel populated, not empty)
--
-- Safe to run only against a fresh database: table PKs are left to
-- auto-increment starting from 1, and the number_series counters at the
-- end of this file assume nothing else has been inserted into projects,
-- documents, tasks, quotations, contracts, submissions, or notifications
-- yet. Re-running against a database that already has this data (or any
-- other rows in those tables) will fail on unique constraints.
-- ============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------------------------------------------------------
-- Users
-- ----------------------------------------------------------------------------
-- Password hash below is bcrypt('Demo#2026'), generated with this repo's
-- own app.core.security.hash_password -- not a placeholder.
INSERT INTO users (username, email, password_hash, full_name, designation, mobile, role, is_active) VALUES
('admin',     'admin@almailam.example',    '$2b$12$A.fpsSUrwUczc6W6XeOmO.k06k0Km2GJ9zMkGnFQFBYdic4PGLa0O', 'System Administrator', 'System Administrator',     '+971501000001', 'Administrator',       1),
('s.alfarsi', 's.alfarsi@almailam.example','$2b$12$A.fpsSUrwUczc6W6XeOmO.k06k0Km2GJ9zMkGnFQFBYdic4PGLa0O', 'Sarah Al-Farsi',       'Project Manager',           '+971501000002', 'Project Manager',      1),
('l.haddad',  'l.haddad@almailam.example', '$2b$12$A.fpsSUrwUczc6W6XeOmO.k06k0Km2GJ9zMkGnFQFBYdic4PGLa0O', 'Layla Haddad',         'Structural Engineer',      '+971501000003', 'Engineer',             1),
('a.rashid',  'a.rashid@almailam.example', '$2b$12$A.fpsSUrwUczc6W6XeOmO.k06k0Km2GJ9zMkGnFQFBYdic4PGLa0O', 'Ahmed Rashid',         'MEP Engineer',              '+971501000004', 'Engineer',             1),
('m.iqbal',   'm.iqbal@almailam.example',  '$2b$12$A.fpsSUrwUczc6W6XeOmO.k06k0Km2GJ9zMkGnFQFBYdic4PGLa0O', 'Mohammed Iqbal',       'Fire & Safety Engineer',   '+971501000005', 'Engineer',             1),
('f.noor',    'f.noor@almailam.example',   '$2b$12$A.fpsSUrwUczc6W6XeOmO.k06k0Km2GJ9zMkGnFQFBYdic4PGLa0O', 'Fatima Noor',          'Document Controller',      '+971501000006', 'Document Controller',  1),
('o.khalid',  'o.khalid@almailam.example', '$2b$12$A.fpsSUrwUczc6W6XeOmO.k06k0Km2GJ9zMkGnFQFBYdic4PGLa0O', 'Omar Khalid',          'Stakeholder',               '+971501000007', 'Viewer',               1);

-- Site Engineer Portal demo logins -- same accounts/password as above,
-- just also resolvable by employee_id (see auth_service.login).
UPDATE users SET employee_id = 'EMP-1003' WHERE username = 'l.haddad';
UPDATE users SET employee_id = 'EMP-1004' WHERE username = 'a.rashid';
UPDATE users SET employee_id = 'EMP-1005' WHERE username = 'm.iqbal';

SET @u_admin    = (SELECT id FROM users WHERE username = 'admin');
SET @u_pm       = (SELECT id FROM users WHERE username = 's.alfarsi');
SET @u_layla    = (SELECT id FROM users WHERE username = 'l.haddad');
SET @u_ahmed    = (SELECT id FROM users WHERE username = 'a.rashid');
SET @u_mohammed = (SELECT id FROM users WHERE username = 'm.iqbal');
SET @u_fatima   = (SELECT id FROM users WHERE username = 'f.noor');
SET @u_omar     = (SELECT id FROM users WHERE username = 'o.khalid');

-- ----------------------------------------------------------------------------
-- Clients
-- ----------------------------------------------------------------------------
INSERT INTO clients (client_type, company_name, contact_person, mobile, email, city, status, onboarding_state, org_legal_name, org_organisation_type, org_registration_number, org_trade_licence_number, org_country_of_registration, org_date_of_incorporation, preferred_language, preferred_channel, email_consent, whatsapp_consent, sms_consent) VALUES
('Organisation', 'Al Reem Development LLC',        'Khalid Al Reem',   '+96550200001', 'khalid@alreemdev.example',       'Kuwait City', 'Active', 'Ready', 'Al Reem Development LLC',        'LLC', 'REG-10023', 'TL-88213', 'Kuwait', '2015-03-11', 'English', 'Email',    1, 1, 0),
('Organisation', 'Falcon Heights Logistics',        'Yousef Al Amiri',  '+96550200002', 'yousef@falconheights.example',   'Shuwaikh',    'Active', 'Ready', 'Falcon Heights Logistics WLL',   'WLL', 'REG-10456', 'TL-90144', 'Kuwait', '2018-07-02', 'English', 'WhatsApp', 1, 1, 0),
('Organisation', 'Marina Bay Hospitality Group',    'Noura Al Sabah',   '+96550200003', 'noura@marinabayhg.example',      'Salmiya',     'Active', 'Ready', 'Marina Bay Hospitality Group WLL','WLL', 'REG-10789', 'TL-91230', 'Kuwait', '2012-11-20', 'Arabic',  'Email',    1, 0, 0),
('Organisation', 'Ahmadi Industrial Holdings',      'Rashid Al Nuaimi', '+96550200004', 'rashid@aihholdings.example',     'Ahmadi',      'Active', 'Under Review', 'Ahmadi Industrial Holdings WLL','WLL', 'REG-11002', 'TL-92877', 'Kuwait', '2009-01-15', 'English', 'Email',    1, 1, 1),
('Individual',   'Khalid Al Mansoori',              'Khalid Al Mansoori','+96550200005','khalid.mansoori@example.com',   'Hawalli',    'Active', 'Ready', NULL, NULL, NULL, NULL, NULL, NULL, 'English', 'SMS', 1, 0, 1);

UPDATE clients SET ind_full_legal_name = 'Khalid Al Mansoori', ind_nationality = 'Kuwaiti', ind_date_of_birth = '1978-04-02', ind_country_of_residence = 'Kuwait'
WHERE company_name = 'Khalid Al Mansoori';

SET @c_alreem  = (SELECT id FROM clients WHERE company_name = 'Al Reem Development LLC');
SET @c_falcon  = (SELECT id FROM clients WHERE company_name = 'Falcon Heights Logistics');
SET @c_marina  = (SELECT id FROM clients WHERE company_name = 'Marina Bay Hospitality Group');
SET @c_ahmadi = (SELECT id FROM clients WHERE company_name = 'Ahmadi Industrial Holdings');
SET @c_khalid  = (SELECT id FROM clients WHERE company_name = 'Khalid Al Mansoori');

-- Customer Portal demo logins -- same password hash as every other demo
-- account, resolved via customer_id (see auth_service.login) and scoped
-- to their own client's projects via client_id.
INSERT INTO users (username, customer_id, client_id, email, password_hash, full_name, mobile, role, is_active) VALUES
('cust.alreem', 'CUST-1001', @c_alreem, 'khalid@alreemdev.example',     '$2b$12$A.fpsSUrwUczc6W6XeOmO.k06k0Km2GJ9zMkGnFQFBYdic4PGLa0O', 'Khalid Al Reem',  '+96550200001', 'Customer', 1),
('cust.falcon', 'CUST-1002', @c_falcon, 'yousef@falconheights.example', '$2b$12$A.fpsSUrwUczc6W6XeOmO.k06k0Km2GJ9zMkGnFQFBYdic4PGLa0O', 'Yousef Al Amiri', '+96550200002', 'Customer', 1);

INSERT INTO client_contacts (client_id, name, contact_type, mobile, email, is_authorised_representative) VALUES
(@c_alreem,  'Khalid Al Reem',  'Primary Contact', '+96550200001', 'khalid@alreemdev.example', 1),
(@c_falcon,  'Yousef Al Amiri', 'Primary Contact', '+96550200002', 'yousef@falconheights.example', 1),
(@c_falcon,  'Mona Saeed',      'Billing Contact',  '+96550200012', 'mona@falconheights.example', 0),
(@c_marina,  'Noura Al Sabah',  'Primary Contact', '+96550200003', 'noura@marinabayhg.example', 1),
(@c_ahmadi, 'Rashid Al Nuaimi','Primary Contact', '+96550200004', 'rashid@aihholdings.example', 1);

INSERT INTO client_addresses (client_id, address_type, country, state, city, area, street, building) VALUES
(@c_alreem,  'Registered', 'Kuwait', 'Al Asimah', 'Kuwait City', 'Sharq',           'Arabian Gulf Street', 'Al Reem Tower'),
(@c_falcon,  'Operating',  'Kuwait', 'Al Asimah', 'Shuwaikh',    'Shuwaikh Port',   'Port Road',           'Warehouse 14'),
(@c_marina,  'Registered', 'Kuwait', 'Hawalli',   'Salmiya',     'Salmiya Seafront','Arabian Gulf Road',   'Marina Bay Plaza'),
(@c_ahmadi, 'Operating',  'Kuwait', 'Ahmadi',    'Ahmadi',      'Industrial Area', 'Ahmadi Industrial Road', 'Plot 44');

INSERT INTO client_identifications (client_id, document_type, document_number, issue_date, expiry_date, issuing_country) VALUES
(@c_alreem,  'Trade Licence', 'TL-88213', '2023-01-10', '2027-01-09', 'Kuwait'),
(@c_falcon,  'Trade Licence', 'TL-90144', '2023-06-01', '2027-05-31', 'Kuwait'),
(@c_marina,  'Trade Licence', 'TL-91230', '2022-11-15', '2026-11-14', 'Kuwait'),
(@c_ahmadi, 'Trade Licence', 'TL-92877', '2023-02-20', '2027-02-19', 'Kuwait'),
(@c_khalid,  'Civil ID',      '278040112345', '2021-04-02', '2031-04-01', 'Kuwait');

INSERT INTO client_consents (client_id, consent_type, version, granted, recorded_at, method, recorded_by) VALUES
(@c_alreem,  'Process Personal Information', 'v1.0', 1, '2026-01-05 09:15:00', 'Onboarding wizard', @u_pm),
(@c_falcon,  'Process Personal Information', 'v1.0', 1, '2026-02-10 11:00:00', 'Onboarding wizard', @u_pm),
(@c_marina,  'Process Personal Information', 'v1.0', 1, '2026-01-20 14:30:00', 'Onboarding wizard', @u_pm),
(@c_ahmadi, 'Process Personal Information', 'v1.0', 1, '2026-03-01 10:00:00', 'Onboarding wizard', @u_pm);

INSERT INTO client_documents (client_id, category, title, issue_date, expiry_date, issuing_authority, version, verification_status, uploaded_by, upload_date, storage_key, original_filename, file_size_bytes) VALUES
(@c_alreem,  'Trade Licence', 'Al Reem Development Trade Licence', '2023-01-10', '2027-01-09', 'Ministry of Commerce and Industry', 1, 'Verified', @u_fatima, '2026-01-05 09:20:00', '', 'seed-data-no-file.pdf', 0),
(@c_falcon,  'Trade Licence', 'Falcon Heights Trade Licence',      '2023-06-01', '2027-05-31', 'Ministry of Commerce and Industry', 1, 'Verified', @u_fatima, '2026-02-10 11:05:00', '', 'seed-data-no-file.pdf', 0),
(@c_khalid,  'Identity Document', 'Khalid Al Mansoori Civil ID', '2021-04-02', '2031-04-01', 'Public Authority for Civil Information', 1, 'Verified', @u_fatima, '2026-01-15 08:40:00', '', 'seed-data-no-file.pdf', 0);

INSERT INTO client_verifications (client_id, item, result, verified_by, verified_date, notes) VALUES
(@c_alreem,  'Trade Licence Verification', 'Verified', @u_fatima, '2026-01-06 10:00:00', 'Verified against Ministry of Commerce and Industry public register.'),
(@c_falcon,  'Trade Licence Verification', 'Verified', @u_fatima, '2026-02-11 09:30:00', 'Verified against Ministry of Commerce and Industry public register.'),
(@c_ahmadi, 'Trade Licence Verification', 'Pending',  @u_fatima, '2026-03-02 09:00:00', 'Awaiting Ministry of Commerce and Industry confirmation.');

-- ----------------------------------------------------------------------------
-- Projects
-- ----------------------------------------------------------------------------
INSERT INTO projects (project_no, project_name, client_id, service, engineer_id, current_stage, progress, priority, start_date, target_date, status) VALUES
('2600001', 'Al Reem Residential Tower - Structural Design',       @c_alreem,  'Structural Engineering',    @u_layla,    'Enquiry',               8,   'Medium', '2026-06-02', '2026-12-18', 'Active'),
('2600002', 'Falcon Heights Warehouse Expansion',                  @c_falcon,  'MEP Design',                @u_ahmed,    'Quotation',             18,  'High',   '2026-05-14', '2026-11-30', 'Active'),
('2600003', 'Marina Bay Hotel Renovation',                         @c_marina,  'Architectural Design',      @u_layla,    'Design',                42,  'High',   '2026-03-10', '2026-10-05', 'Active'),
('2600004', 'Ahmadi Industrial Facility - Fire Safety Approval',   @c_ahmadi, 'Fire & Safety Engineering', @u_mohammed, 'Government Submission', 68,  'High',   '2026-01-20', '2026-08-15', 'Active'),
('2600005', 'Desert Rose Retail Plaza - Final Handover',           @c_khalid,  'Civil Engineering',         @u_ahmed,    'Completed',             100, 'Low',    '2025-09-01', '2026-03-20', 'Completed');

SET @p_alreem  = (SELECT id FROM projects WHERE project_no = '2600001');
SET @p_falcon  = (SELECT id FROM projects WHERE project_no = '2600002');
SET @p_marina  = (SELECT id FROM projects WHERE project_no = '2600003');
SET @p_ahmadi  = (SELECT id FROM projects WHERE project_no = '2600004');
SET @p_desert  = (SELECT id FROM projects WHERE project_no = '2600005');

-- ----------------------------------------------------------------------------
-- Government authorities, forms, submissions
-- ----------------------------------------------------------------------------
INSERT INTO government_authorities (name, category, website, description) VALUES
('Kuwait Municipality',              'Municipality',    'https://www.baladia.gov.kw', 'Regulates building permits, occupancy, and municipal compliance across Kuwait.'),
('Kuwait Fire Service Directorate',  'Fire Department', 'https://www.kff.gov.kw',     'Approves fire and life safety systems for buildings and facilities in Kuwait.'),
('Ministry of Electricity, Water and Renewable Energy', 'Electricity', 'https://www.mew.gov.kw', 'Handles electricity and water connection approvals across Kuwait.');

SET @a_km   = (SELECT id FROM government_authorities WHERE name = 'Kuwait Municipality');
SET @a_kfsd = (SELECT id FROM government_authorities WHERE name = 'Kuwait Fire Service Directorate');
SET @a_mew  = (SELECT id FROM government_authorities WHERE name = 'Ministry of Electricity, Water and Renewable Energy');

INSERT INTO government_forms (authority_id, form_code, title, version, language, category, description, required_documents, status) VALUES
(@a_km,   'KM-101',   'Building Permit Application',      '2.1', 'English / Arabic', 'Building Permit',          'Application for a new building permit or major renovation.', JSON_ARRAY('Trade Licence','Site Plan','Structural Drawings','Ownership Proof'), 'Active'),
(@a_kfsd, 'KFSD-204', 'Fire Safety Approval',             '1.4', 'English',          'Fire Safety Approval',     'Approval of fire and life safety systems prior to occupancy.', JSON_ARRAY('Fire System Drawings','Material Safety Data Sheets','Structural Drawings'), 'Active'),
(@a_mew,  'MEW-310',  'Utility Connection Request',       '3.0', 'English / Arabic', 'Utility Connection',       'Request for electricity and water connection to a new or renovated facility.', JSON_ARRAY('Building Completion Certificate','Ownership Proof'), 'Active');

SET @f_km101   = (SELECT id FROM government_forms WHERE form_code = 'KM-101');
SET @f_kfsd204 = (SELECT id FROM government_forms WHERE form_code = 'KFSD-204');

INSERT INTO government_submissions (submission_no, project_id, authority_id, form_id, status, submitted_date, expected_decision_date, decision_date, notes) VALUES
('SUB-2026-001', @p_ahmadi, @a_kfsd, @f_kfsd204, 'Under Review', '2026-06-15', '2026-08-01', NULL, 'Submitted fire suppression drawings for the warehouse extension.'),
('SUB-2026-002', @p_alreem, @a_km,   @f_km101,   'Draft',        NULL,         NULL,         NULL, 'Preparing building permit application; awaiting finalised structural drawings.');

SET @sub_ahmadi = (SELECT id FROM government_submissions WHERE submission_no = 'SUB-2026-001');
SET @sub_alreem = (SELECT id FROM government_submissions WHERE submission_no = 'SUB-2026-002');

INSERT INTO submission_documents (submission_id, name, status) VALUES
(@sub_ahmadi, 'Fire System Drawings',       'Uploaded'),
(@sub_ahmadi, 'Material Safety Data Sheets','Uploaded'),
(@sub_ahmadi, 'Structural Drawings',        'Verified'),
(@sub_alreem,  'Trade Licence',              'Uploaded'),
(@sub_alreem,  'Site Plan',                  'Pending'),
(@sub_alreem,  'Structural Drawings',        'Pending'),
(@sub_alreem,  'Ownership Proof',            'Pending');

-- ----------------------------------------------------------------------------
-- Quotations
-- ----------------------------------------------------------------------------
INSERT INTO quotations (quotation_no, project_id, revision, issue_date, validity, status, currency, prepared_by, tax_rate_percent, discount_amount, notes, terms_and_conditions, amount) VALUES
('QUO-2026-001', @p_alreem,  'R0', '2026-06-05', '2026-07-05', 'Draft',    'AED', @u_pm, 5.00, 0,    'Initial structural design quotation for the residential tower.', JSON_ARRAY('Valid for 30 days from issue date.','50% advance payment required to commence design.','Excludes government submission fees.'), 185000.00),
('QUO-2026-002', @p_falcon,  'R1', '2026-05-20', '2026-06-19', 'Approved', 'AED', @u_pm, 5.00, 5000, 'MEP design for the warehouse expansion, revised after client feedback.', JSON_ARRAY('Valid for 30 days from issue date.','Payment terms per signed agreement.'), 246000.00),
('QUO-2026-003', @p_marina,  'R0', '2026-03-15', '2026-04-14', 'Approved', 'AED', @u_pm, 5.00, 0,    'Architectural renovation design for Marina Bay Hotel.', JSON_ARRAY('Valid for 30 days from issue date.','Site survey included in scope.'), 412000.00);

SET @q_alreem = (SELECT id FROM quotations WHERE quotation_no = 'QUO-2026-001');
SET @q_falcon = (SELECT id FROM quotations WHERE quotation_no = 'QUO-2026-002');
SET @q_marina = (SELECT id FROM quotations WHERE quotation_no = 'QUO-2026-003');

INSERT INTO quotation_line_items (quotation_id, description, quantity, unit_price) VALUES
(@q_alreem, 'Structural design and analysis',        1, 140000.00),
(@q_alreem, 'Structural drawings and specifications', 1, 45000.00),
(@q_falcon, 'MEP concept and detailed design',        1, 180000.00),
(@q_falcon, 'MEP coordination and site supervision',  1, 71000.00),
(@q_marina, 'Architectural concept design',           1, 150000.00),
(@q_marina, 'Detailed architectural drawings',        1, 180000.00),
(@q_marina, 'Interior renovation design',             1, 82000.00);

-- ----------------------------------------------------------------------------
-- Contracts
-- ----------------------------------------------------------------------------
INSERT INTO contracts (contract_no, project_id, template_name, revision, currency, contract_value, issue_date, signed_date, expiry_date, status, prepared_by, client_representative, scope_summary) VALUES
('CON-2026-001', @p_falcon, 'Standard MEP Design Agreement',   'R0', 'AED', 246000.00, '2026-05-25', '2026-05-28', '2026-11-30', 'Signed', @u_pm, 'Yousef Al Amiri', 'MEP design services for the Falcon Heights warehouse expansion, covering concept through construction-issue drawings.'),
('CON-2026-002', @p_marina, 'Standard Architectural Design Agreement', 'R0', 'AED', 412000.00, '2026-03-20', '2026-03-25', '2026-10-05', 'Active', @u_pm, 'Noura Al Sabah', 'Full architectural renovation design and site supervision for Marina Bay Hotel, including interior scope.');

SET @con_falcon = (SELECT id FROM contracts WHERE contract_no = 'CON-2026-001');
SET @con_marina = (SELECT id FROM contracts WHERE contract_no = 'CON-2026-002');

INSERT INTO contract_clauses (contract_id, title, content, sort_order) VALUES
(@con_falcon, 'Scope of Work',  'The Consultant shall provide MEP design services as detailed in the attached quotation QUO-2026-002.', 1),
(@con_falcon, 'Payment Terms',  'Payment shall be made in three instalments per the payment schedule in the financial agreement.', 2),
(@con_falcon, 'Termination',    'Either party may terminate this agreement with 30 days written notice.', 3),
(@con_marina, 'Scope of Work',  'The Consultant shall provide architectural design and site supervision services as detailed in QUO-2026-003.', 1),
(@con_marina, 'Payment Terms',  'Payment shall be made monthly against progress milestones.', 2),
(@con_marina, 'Confidentiality','Both parties agree to keep project details confidential during and after the engagement.', 3);

INSERT INTO contract_revisions (contract_id, revision, revised_at, changed_by, summary) VALUES
(@con_falcon, 'R0', '2026-05-25', @u_pm, 'Initial contract issued to client for signature.'),
(@con_marina, 'R0', '2026-03-20', @u_pm, 'Initial contract issued to client for signature.');

-- ----------------------------------------------------------------------------
-- Financial agreements, obligations, payments
-- ----------------------------------------------------------------------------
INSERT INTO financial_agreements (project_id, contract_amount, currency, contract_start_date, contract_end_date, agreement_date, quotation_reference, contract_reference, payment_mode, payment_frequency) VALUES
(@p_falcon, 246000.00, 'AED', '2026-05-28', '2026-11-30', '2026-05-28', 'QUO-2026-002', 'CON-2026-001', 'Bank Transfer', 'Monthly'),
(@p_marina, 412000.00, 'AED', '2026-03-25', '2026-10-05', '2026-03-25', 'QUO-2026-003', 'CON-2026-002', 'Bank Transfer', 'Monthly'),
(@p_desert,  98000.00, 'AED', '2025-09-05', '2026-03-20', '2025-09-05', NULL,           NULL,           'Bank Transfer', 'One-time');

SET @fa_falcon = (SELECT id FROM financial_agreements WHERE project_id = @p_falcon);
SET @fa_marina = (SELECT id FROM financial_agreements WHERE project_id = @p_marina);
SET @fa_desert = (SELECT id FROM financial_agreements WHERE project_id = @p_desert);

INSERT INTO payment_obligations (agreement_id, sequence_number, description, amount_due, due_date, amount_received, date_paid, payment_method, reference_number) VALUES
(@fa_falcon, 1, 'Instalment 1 - Design Kickoff',    82000.00,  '2026-06-01', 82000.00,  '2026-06-01', 'Bank Transfer', 'TRF-20260601-1'),
(@fa_falcon, 2, 'Instalment 2 - Design Development', 82000.00,  '2026-08-01', 0,         NULL,         NULL,             NULL),
(@fa_falcon, 3, 'Instalment 3 - Final Delivery',     82000.00,  '2026-11-15', 0,         NULL,         NULL,             NULL),
(@fa_marina, 1, 'Instalment 1 - Concept Design',    137333.33, '2026-04-01', 137333.33, '2026-04-02', 'Bank Transfer', 'TRF-20260402-1'),
(@fa_marina, 2, 'Instalment 2 - Detailed Design',   137333.33, '2026-07-01', 137333.33, '2026-07-03', 'Bank Transfer', 'TRF-20260703-1'),
(@fa_marina, 3, 'Instalment 3 - Site Supervision',  137333.34, '2026-10-01', 0,         NULL,         NULL,             NULL),
(@fa_desert, 1, 'Final Handover Payment',            98000.00,  '2026-03-15', 98000.00,  '2026-03-10', 'Bank Transfer', 'TRF-20260310-1');

INSERT INTO payments (agreement_id, project_id, amount_received, payment_date, payment_mode, reference_number, payer, receiving_account, created_by, created_at) VALUES
(@fa_falcon, @p_falcon,  82000.00,  '2026-06-01', 'Bank Transfer', 'TRF-20260601-1', 'Falcon Heights Logistics',     'Al Mailam Operating Account', @u_pm, '2026-06-01 10:00:00'),
(@fa_marina, @p_marina, 137333.33, '2026-04-02', 'Bank Transfer', 'TRF-20260402-1', 'Marina Bay Hospitality Group', 'Al Mailam Operating Account', @u_pm, '2026-04-02 09:30:00'),
(@fa_marina, @p_marina, 137333.33, '2026-07-03', 'Bank Transfer', 'TRF-20260703-1', 'Marina Bay Hospitality Group', 'Al Mailam Operating Account', @u_pm, '2026-07-03 09:45:00'),
(@fa_desert, @p_desert,  98000.00,  '2026-03-10', 'Bank Transfer', 'TRF-20260310-1', 'Khalid Al Mansoori',          'Al Mailam Operating Account', @u_pm, '2026-03-10 14:20:00');

SET @pay_falcon1 = (SELECT id FROM payments WHERE reference_number = 'TRF-20260601-1');
SET @pay_marina1 = (SELECT id FROM payments WHERE reference_number = 'TRF-20260402-1');
SET @pay_marina2 = (SELECT id FROM payments WHERE reference_number = 'TRF-20260703-1');
SET @pay_desert1 = (SELECT id FROM payments WHERE reference_number = 'TRF-20260310-1');

SET @ob_falcon1 = (SELECT id FROM payment_obligations WHERE agreement_id = @fa_falcon AND sequence_number = 1);
SET @ob_marina1 = (SELECT id FROM payment_obligations WHERE agreement_id = @fa_marina AND sequence_number = 1);
SET @ob_marina2 = (SELECT id FROM payment_obligations WHERE agreement_id = @fa_marina AND sequence_number = 2);
SET @ob_desert1 = (SELECT id FROM payment_obligations WHERE agreement_id = @fa_desert AND sequence_number = 1);

INSERT INTO payment_allocations (payment_id, obligation_id, amount_allocated) VALUES
(@pay_falcon1, @ob_falcon1, 82000.00),
(@pay_marina1, @ob_marina1, 137333.33),
(@pay_marina2, @ob_marina2, 137333.33),
(@pay_desert1, @ob_desert1, 98000.00);

-- ----------------------------------------------------------------------------
-- Project documents (+ one version history example)
-- ----------------------------------------------------------------------------
-- storage_key values are placeholders -- there is no matching file on disk
-- for seed data, so these rows are for listing/metadata purposes only; do
-- not expect a real download to succeed for a seeded document.
INSERT INTO project_documents (document_no, project_id, title, type, revision, uploaded_by, upload_date, status, storage_key, original_filename, file_size_bytes) VALUES
('DOC-2026-001', @p_alreem,  'Al Reem Tower Site Survey',              'Report',           'Rev A', @u_layla,    '2026-06-10', 'Approved',     'seed/doc-001', 'al-reem-site-survey.pdf',        1258000),
('DOC-2026-002', @p_falcon,  'Falcon Heights MEP Concept Drawing',     'Drawing',          'Rev B', @u_ahmed,    '2026-05-22', 'Approved',     'seed/doc-002', 'falcon-mep-concept-revB.pdf',    3421000),
('DOC-2026-003', @p_falcon,  'Falcon Heights Load Calculation Sheet',  'Calculation Sheet','Rev A', @u_ahmed,    '2026-06-01', 'Under Review', 'seed/doc-003', 'falcon-load-calcs.xlsx',          842000),
('DOC-2026-004', @p_marina,  'Marina Bay Hotel Renovation Drawings',   'Drawing',          'Rev C', @u_layla,    '2026-07-15', 'Approved',     'seed/doc-004', 'marina-bay-renovation-revC.pdf', 5210000),
('DOC-2026-005', @p_marina,  'Marina Bay Interior Fit-out Report',     'Report',           'Rev A', @u_layla,    '2026-07-20', 'Draft',        'seed/doc-005', 'marina-bay-interior-report.pdf',  987000),
('DOC-2026-006', @p_ahmadi, 'Ahmadi Facility Fire System Drawings',  'Drawing',          'Rev A', @u_mohammed, '2026-06-12', 'Approved',     'seed/doc-006', 'ahmadi-fire-system.pdf',        2870000),
('DOC-2026-007', @p_ahmadi, 'Ahmadi Facility Submission Form',   'Municipality Form','Rev A', @u_fatima,   '2026-06-14', 'Approved',     'seed/doc-007', 'ahmadi-kfsd-204-form.pdf',         410000),
('DOC-2026-008', @p_desert,  'Desert Rose Plaza Handover Certificate', 'Report',           'Rev A', @u_ahmed,    '2026-03-18', 'Approved',     'seed/doc-008', 'desert-rose-handover.pdf',        650000);

SET @doc_falcon_mep = (SELECT id FROM project_documents WHERE document_no = 'DOC-2026-002');

INSERT INTO document_versions (document_id, revision, uploaded_by, upload_date, notes, storage_key, original_filename, file_size_bytes) VALUES
(@doc_falcon_mep, 'Rev A', @u_ahmed, '2026-05-15', 'Initial concept drawing.',          'seed/doc-002-revA', 'falcon-mep-concept-revA.pdf', 3180000),
(@doc_falcon_mep, 'Rev B', @u_ahmed, '2026-05-22', 'Revised after client walkthrough.', 'seed/doc-002-revB', 'falcon-mep-concept-revB.pdf', 3421000);

-- ----------------------------------------------------------------------------
-- Tasks
-- ----------------------------------------------------------------------------
INSERT INTO tasks (task_no, project_id, title, assigned_to, priority, severity, due_date, due_time, status) VALUES
('TSK-2026-001', @p_alreem,  'Complete structural site survey report',       @u_layla,    'High',   'Major',    '2026-06-20', '17:00:00', 'Completed'),
('TSK-2026-002', @p_alreem,  'Draft preliminary structural calculations',    @u_layla,    'Medium', 'Minor',    '2026-07-05', '17:00:00', 'In Progress'),
('TSK-2026-003', @p_falcon,  'Finalise MEP concept drawing Rev B',           @u_ahmed,    'High',   'Major',    '2026-05-22', '17:00:00', 'Completed'),
('TSK-2026-004', @p_falcon,  'Review load calculation sheet',                @u_ahmed,    'Medium', 'Major',    '2026-06-10', '17:00:00', 'In Progress'),
('TSK-2026-005', @p_marina,  'Coordinate interior fit-out with client',      @u_layla,    'High',   'Minor',    '2026-07-25', '15:00:00', 'Pending'),
('TSK-2026-006', @p_ahmadi, 'Prepare fire safety submission package',       @u_mohammed, 'High',   'Critical', '2026-06-14', '12:00:00', 'Completed'),
('TSK-2026-007', @p_ahmadi, 'Follow up with Kuwait Fire Service Directorate on review status',@u_mohammed, 'Medium', 'Major',    '2026-07-20', '12:00:00', 'Pending'),
('TSK-2026-008', @p_desert,  'Archive final handover documentation',         @u_fatima,   'Low',    'Minor',    '2026-03-19', '17:00:00', 'Completed');

-- ----------------------------------------------------------------------------
-- Notifications
-- ----------------------------------------------------------------------------
INSERT INTO notifications (notification_no, user_id, title, message, category, created_at, `read`, link_route_name, link_params) VALUES
('NTF-2026-001', @u_pm,    'New task assigned',            'You have been kept informed on "Prepare fire safety submission package" for Ahmadi Industrial Facility.', 'Task', '2026-06-14 09:00:00', 1, 'project-workspace', JSON_OBJECT('projectId', '2600004')),
('NTF-2026-002', @u_pm,    'Payment received',             'AED 82,000 received for Falcon Heights Warehouse Expansion (Instalment 1).', 'Project', '2026-06-01 10:05:00', 1, 'project-workspace', JSON_OBJECT('projectId', '2600002')),
('NTF-2026-003', @u_pm,    'Government submission update', 'Fire Safety Approval for Ahmadi Industrial Facility is now Under Review.', 'Government', '2026-06-15 11:30:00', 0, 'government-submissions', NULL),
('NTF-2026-004', @u_admin, 'New client onboarded',         'Ahmadi Industrial Holdings has completed onboarding and is under review.', 'Project', '2026-03-01 10:05:00', 0, 'client-workspace', JSON_OBJECT('clientId', 'CLT-004')),
('NTF-2026-005', @u_layla, 'Task due soon',                'Draft preliminary structural calculations is due on 2026-07-05.', 'Task', '2026-06-28 08:00:00', 0, 'tasks', NULL);

-- ----------------------------------------------------------------------------
-- Message templates and log
-- ----------------------------------------------------------------------------
INSERT INTO message_templates (name, channel, body) VALUES
('Project Kickoff Notice', 'Email', 'Dear {{contact_name}}, we are pleased to confirm the kickoff of {{project_name}}. Our team will be in touch shortly with next steps.'),
('Payment Reminder',       'Email', 'Dear {{contact_name}}, this is a reminder that a payment of {{amount}} for {{project_name}} is due on {{due_date}}.');

SET @tmpl_kickoff  = (SELECT id FROM message_templates WHERE name = 'Project Kickoff Notice');
SET @tmpl_reminder = (SELECT id FROM message_templates WHERE name = 'Payment Reminder');

INSERT INTO message_log (client_id, channel, template_id, body, project_id, status, sent_at) VALUES
(@c_falcon, 'Email', @tmpl_kickoff,  'Dear Yousef Al Amiri, we are pleased to confirm the kickoff of Falcon Heights Warehouse Expansion. Our team will be in touch shortly with next steps.', @p_falcon, 'Sent', '2026-05-14 09:00:00'),
(@c_marina, 'Email', @tmpl_reminder, 'Dear Noura Al Sabah, this is a reminder that a payment of AED 137,333.34 for Marina Bay Hotel Renovation is due on 2026-10-01.', @p_marina, 'Sent', '2026-09-15 09:00:00');

-- ----------------------------------------------------------------------------
-- Project timeline events
-- ----------------------------------------------------------------------------
INSERT INTO project_timeline_events (project_id, type, title, description, event_date, status, created_by) VALUES
(@p_marina,  'stage',      'Design stage started',           'Project moved into the Design stage after contract signature.', '2026-03-25', 'completed', @u_pm),
(@p_marina,  'milestone',  'Concept design approved',        'Client approved the architectural concept design.',              '2026-05-01', 'completed', @u_pm),
(@p_marina,  'note',       'Interior fit-out scope added',   'Client requested interior fit-out design be added to scope.',    '2026-07-10', 'completed', @u_layla),
(@p_desert,  'stage',      'Project completed',              'Final handover documentation delivered and accepted.',           '2026-03-20', 'completed', @u_ahmed),
(@p_ahmadi, 'submission', 'Fire safety approval submitted', 'Submitted KFSD-204 Fire Safety Approval to Kuwait Fire Service Directorate.',  '2026-06-15', 'completed', @u_mohammed);

-- ----------------------------------------------------------------------------
-- Number series continuation
-- ----------------------------------------------------------------------------
-- So the next real project/document/task/quotation/contract/submission/
-- notification created through the app continues after the seeded ones
-- instead of colliding with them.
INSERT INTO number_series (doc_type, year, prefix, next_number, padding) VALUES
('PROJECT',              2026, 'PRJ', 6, 5),
('DOCUMENT',              2026, 'DOC', 9, 3),
('TASK',                 2026, 'TSK', 9, 3),
('QUOTATION',             2026, 'QUO', 4, 3),
('CONTRACT',              2026, 'CON', 3, 3),
('GOVERNMENT_SUBMISSION', 2026, 'SUB', 3, 3),
('NOTIFICATION',          2026, 'NTF', 6, 3)
ON DUPLICATE KEY UPDATE next_number = VALUES(next_number);

-- Seeded projects above are inserted as raw rows, not through
-- project_service.create_project() -- so they never went through its
-- execution-step snapshot step. Same backfill migration 0016 applies
-- to an existing database; needed here too so a fresh install (schema.sql
-- then this file, no migration in between) doesn't leave every demo
-- project stuck with an empty checklist. Guarded the same way: only
-- projects with zero existing steps get backfilled.
INSERT INTO project_execution_steps (project_id, name, sequence_number, weight_percentage, stage_key, is_optional)
SELECT p.id, t.name, t.sequence_number, t.weight_percentage, t.stage_key, t.is_optional
FROM projects p
CROSS JOIN execution_step_templates t
WHERE t.deleted_at IS NULL
  AND NOT EXISTS (
    SELECT 1 FROM project_execution_steps pes WHERE pes.project_id = p.id
  );

-- Same reasoning, same backfill pattern, for the separate approval
-- process trial -- see approval_process.py's own docstring. No status
-- to seed here either -- a stage counts as complete once a document
-- is uploaded for it (storage_key set), not via a status column.
INSERT INTO project_approval_steps (project_id, name, sequence_number, stage_key)
SELECT p.id, t.name, t.sequence_number, t.stage_key
FROM projects p
CROSS JOIN approval_process_templates t
WHERE t.deleted_at IS NULL
  AND NOT EXISTS (
    SELECT 1 FROM project_approval_steps pas WHERE pas.project_id = p.id
  );

SET FOREIGN_KEY_CHECKS = 1;
