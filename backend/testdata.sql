-- ============================================================================
-- ServiceOS / Al Mailam Roadmap -- Test Data
-- ============================================================================
-- Populates a fresh database (after schema.sql has been applied) with a
-- small, internally-consistent set of demo data so the application has
-- something real to show end to end: clients, projects at different
-- workflow stages, quotations, contracts, payments, government
-- submissions, documents, tasks, and notifications.
--
-- 5 clients, 5 staff users, 20 projects -- deliberately spread across every
-- WorkflowStage and every parallel-track combination (Design / Government
-- Submission / Supervision, alone and combined), plus a handful of
-- specific conditions worth exercising by hand: an On Hold project, a
-- Cancelled project, a Cancelled track item sitting next to still-open
-- ones, an overdue task, both Handover sub-states (payment confirmed vs.
-- not), a fully Completed project, and one project with none of the three
-- parallel tracks at all -- parked at Contract with a signed contract and
-- no open tasks, so the very first GET /api/projects/{id} against it
-- self-heals current_stage straight to Handover (see
-- project_service.try_auto_advance_stage / _auto_advance_target's
-- zero-track fallback). Every other seeded project deliberately leaves its
-- own stage's exit criteria unmet, so that same self-heal on read leaves
-- it parked exactly where seeded instead of silently advancing.
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
-- Users (5 staff)
-- ----------------------------------------------------------------------------
-- Password hash below is bcrypt('Demo#2026'), generated with this repo's
-- own app.core.security.hash_password -- not a placeholder.
--
-- Username mirrors the login email for every user except 'admin' (see
-- migration 0058 / user_service.create_user) -- 'admin' is the sole
-- exemption and keeps its own short username.
INSERT INTO users (username, email, password_hash, full_name, designation, mobile, role, is_active) VALUES
('admin',                            'admin@almailam.example',           '$2b$12$A.fpsSUrwUczc6W6XeOmO.k06k0Km2GJ9zMkGnFQFBYdic4PGLa0O', 'System Administrator', 'System Administrator',   '+971501000001', 'Administrator',      1),
('projectmanager@almailam.ai',       'projectmanager@almailam.ai',       '$2b$12$A.fpsSUrwUczc6W6XeOmO.k06k0Km2GJ9zMkGnFQFBYdic4PGLa0O', 'Sarah Al-Farsi',       'Project Manager',         '+971501000002', 'Project Manager',    1),
('engineer1@almailam.ai',            'engineer1@almailam.ai',            '$2b$12$A.fpsSUrwUczc6W6XeOmO.k06k0Km2GJ9zMkGnFQFBYdic4PGLa0O', 'Layla Haddad',         'Structural Engineer',    '+971501000003', 'Engineer',            1),
('engineer2@almailam.ai',            'engineer2@almailam.ai',            '$2b$12$A.fpsSUrwUczc6W6XeOmO.k06k0Km2GJ9zMkGnFQFBYdic4PGLa0O', 'Ahmed Rashid',         'MEP Engineer',            '+971501000004', 'Engineer',            1),
('documentcontroller@almailam.ai',   'documentcontroller@almailam.ai',   '$2b$12$A.fpsSUrwUczc6W6XeOmO.k06k0Km2GJ9zMkGnFQFBYdic4PGLa0O', 'Fatima Noor',          'Document Controller',    '+971501000006', 'Document Controller', 1);

-- Site Engineer Portal demo logins -- same accounts/password as above,
-- just also resolvable by employee_id (see auth_service.login).
UPDATE users SET employee_id = 'EMP-1003' WHERE email = 'engineer1@almailam.ai';
UPDATE users SET employee_id = 'EMP-1004' WHERE email = 'engineer2@almailam.ai';

SET @u_admin  = (SELECT id FROM users WHERE username = 'admin');
SET @u_pm     = (SELECT id FROM users WHERE email = 'projectmanager@almailam.ai');
SET @u_layla  = (SELECT id FROM users WHERE email = 'engineer1@almailam.ai');
SET @u_ahmed  = (SELECT id FROM users WHERE email = 'engineer2@almailam.ai');
SET @u_fatima = (SELECT id FROM users WHERE email = 'documentcontroller@almailam.ai');

-- ----------------------------------------------------------------------------
-- Clients (5)
-- ----------------------------------------------------------------------------
INSERT INTO clients (client_type, company_name, contact_person, mobile, email, city, status, onboarding_state, org_legal_name, org_organisation_type, org_registration_number, org_trade_licence_number, org_country_of_registration, org_date_of_incorporation, preferred_language, preferred_channel, email_consent, whatsapp_consent, sms_consent) VALUES
('Organisation', 'Al Reem Development LLC',        'Khalid Al Reem',   '+96550200001', 'khalid@alreemdev.example',       'Kuwait City', 'Active', 'Ready',               'Al Reem Development LLC',         'LLC', 'REG-10023', 'TL-88213', 'Kuwait', '2015-03-11', 'English', 'Email',    1, 1, 0),
('Organisation', 'Falcon Heights Logistics',        'Yousef Al Amiri',  '+96550200002', 'yousef@falconheights.example',   'Shuwaikh',    'Active', 'Ready',               'Falcon Heights Logistics WLL',    'WLL', 'REG-10456', 'TL-90144', 'Kuwait', '2018-07-02', 'English', 'WhatsApp', 1, 1, 0),
('Organisation', 'Marina Bay Hospitality Group',    'Noura Al Sabah',   '+96550200003', 'noura@marinabayhg.example',      'Salmiya',     'Active', 'Ready',               'Marina Bay Hospitality Group WLL','WLL', 'REG-10789', 'TL-91230', 'Kuwait', '2012-11-20', 'Arabic',  'Email',    1, 0, 0),
('Organisation', 'Ahmadi Industrial Holdings',      'Rashid Al Nuaimi', '+96550200004', 'rashid@aihholdings.example',     'Ahmadi',      'Active', 'Pending Verification','Ahmadi Industrial Holdings WLL',  'WLL', 'REG-11002', 'TL-92877', 'Kuwait', '2009-01-15', 'English', 'Email',    1, 1, 1),
('Individual',   'Khalid Al Mansoori',              'Khalid Al Mansoori','+96550200005','khalid.mansoori@example.com',   'Hawalli',    'Active', 'Ready',               NULL, NULL, NULL, NULL, NULL, NULL, 'English', 'SMS', 1, 0, 1);

UPDATE clients SET ind_full_legal_name = 'Khalid Al Mansoori', ind_nationality = 'Kuwaiti', ind_date_of_birth = '1978-04-02', ind_country_of_residence = 'Kuwait'
WHERE company_name = 'Khalid Al Mansoori';

SET @c_alreem = (SELECT id FROM clients WHERE company_name = 'Al Reem Development LLC');
SET @c_falcon = (SELECT id FROM clients WHERE company_name = 'Falcon Heights Logistics');
SET @c_marina = (SELECT id FROM clients WHERE company_name = 'Marina Bay Hospitality Group');
SET @c_ahmadi = (SELECT id FROM clients WHERE company_name = 'Ahmadi Industrial Holdings');
SET @c_khalid = (SELECT id FROM clients WHERE company_name = 'Khalid Al Mansoori');

-- Customer Portal demo logins -- same password hash as every other demo
-- account, resolved via customer_id (see auth_service.login) and scoped
-- to their own client's projects via client_id.
INSERT INTO users (username, customer_id, client_id, email, password_hash, full_name, mobile, role, is_active) VALUES
('customer1@almailam.ai', 'CUST-1001', @c_alreem, 'customer1@almailam.ai', '$2b$12$A.fpsSUrwUczc6W6XeOmO.k06k0Km2GJ9zMkGnFQFBYdic4PGLa0O', 'Khalid Al Reem',  '+96550200001', 'Customer', 1),
('customer2@almailam.ai', 'CUST-1002', @c_falcon, 'customer2@almailam.ai', '$2b$12$A.fpsSUrwUczc6W6XeOmO.k06k0Km2GJ9zMkGnFQFBYdic4PGLa0O', 'Yousef Al Amiri', '+96550200002', 'Customer', 1);

INSERT INTO client_contacts (client_id, name, contact_type, mobile, email, is_authorised_representative) VALUES
(@c_alreem, 'Khalid Al Reem',   'Primary Contact', '+96550200001', 'khalid@alreemdev.example', 1),
(@c_falcon, 'Yousef Al Amiri',  'Primary Contact', '+96550200002', 'yousef@falconheights.example', 1),
(@c_falcon, 'Mona Saeed',       'Billing Contact',  '+96550200012', 'mona@falconheights.example', 0),
(@c_marina, 'Noura Al Sabah',   'Primary Contact', '+96550200003', 'noura@marinabayhg.example', 1),
(@c_ahmadi, 'Rashid Al Nuaimi', 'Primary Contact', '+96550200004', 'rashid@aihholdings.example', 1);

INSERT INTO client_addresses (client_id, address_type, country, state, city, area, street, building) VALUES
(@c_alreem, 'Registered', 'Kuwait', 'Al Asimah', 'Kuwait City', 'Sharq',            'Arabian Gulf Street',    'Al Reem Tower'),
(@c_falcon, 'Operating',  'Kuwait', 'Al Asimah', 'Shuwaikh',    'Shuwaikh Port',    'Port Road',              'Warehouse 14'),
(@c_marina, 'Registered', 'Kuwait', 'Hawalli',   'Salmiya',     'Salmiya Seafront', 'Arabian Gulf Road',      'Marina Bay Plaza'),
(@c_ahmadi, 'Operating',  'Kuwait', 'Ahmadi',    'Ahmadi',      'Industrial Area',  'Ahmadi Industrial Road', 'Plot 44');

INSERT INTO client_identifications (client_id, document_type, document_number, issue_date, expiry_date, issuing_country) VALUES
(@c_alreem, 'Trade Licence', 'TL-88213', '2023-01-10', '2027-01-09', 'Kuwait'),
(@c_falcon, 'Trade Licence', 'TL-90144', '2023-06-01', '2027-05-31', 'Kuwait'),
(@c_marina, 'Trade Licence', 'TL-91230', '2022-11-15', '2026-11-14', 'Kuwait'),
(@c_ahmadi, 'Trade Licence', 'TL-92877', '2023-02-20', '2027-02-19', 'Kuwait'),
(@c_khalid, 'Civil ID',      '278040112345', '2021-04-02', '2031-04-01', 'Kuwait');

INSERT INTO client_consents (client_id, consent_type, version, granted, recorded_at, method, recorded_by) VALUES
(@c_alreem, 'Process Personal Information', 'v1.0', 1, '2026-01-05 09:15:00', 'Onboarding wizard', @u_pm),
(@c_falcon, 'Process Personal Information', 'v1.0', 1, '2026-02-10 11:00:00', 'Onboarding wizard', @u_pm),
(@c_marina, 'Process Personal Information', 'v1.0', 1, '2026-01-20 14:30:00', 'Onboarding wizard', @u_pm),
(@c_ahmadi, 'Process Personal Information', 'v1.0', 1, '2026-03-01 10:00:00', 'Onboarding wizard', @u_pm);

INSERT INTO client_documents (client_id, category, title, issue_date, expiry_date, issuing_authority, version, verification_status, uploaded_by, upload_date, storage_key, original_filename, file_size_bytes) VALUES
(@c_alreem, 'Trade Licence',      'Al Reem Development Trade Licence',   '2023-01-10', '2027-01-09', 'Ministry of Commerce and Industry',      1, 'Verified', @u_fatima, '2026-01-05 09:20:00', '', 'seed-data-no-file.pdf', 0),
(@c_falcon, 'Trade Licence',      'Falcon Heights Trade Licence',        '2023-06-01', '2027-05-31', 'Ministry of Commerce and Industry',      1, 'Verified', @u_fatima, '2026-02-10 11:05:00', '', 'seed-data-no-file.pdf', 0),
(@c_khalid, 'Identity Document',  'Khalid Al Mansoori Civil ID',         '2021-04-02', '2031-04-01', 'Public Authority for Civil Information', 1, 'Verified', @u_fatima, '2026-01-15 08:40:00', '', 'seed-data-no-file.pdf', 0);

INSERT INTO client_verifications (client_id, item, result, verified_by, verified_date, notes) VALUES
(@c_alreem, 'Trade Licence Verification', 'Verified', @u_fatima, '2026-01-06 10:00:00', 'Verified against Ministry of Commerce and Industry public register.'),
(@c_falcon, 'Trade Licence Verification', 'Verified', @u_fatima, '2026-02-11 09:30:00', 'Verified against Ministry of Commerce and Industry public register.'),
(@c_ahmadi, 'Trade Licence Verification', 'Pending',  @u_fatima, '2026-03-02 09:00:00', 'Awaiting Ministry of Commerce and Industry confirmation.');

-- ----------------------------------------------------------------------------
-- Government authorities, forms
-- ----------------------------------------------------------------------------
INSERT INTO government_authorities (name, category, website, description) VALUES
('Kuwait Municipality',              'Municipality',    'https://www.baladia.gov.kw', 'Regulates building permits, occupancy, and municipal compliance across Kuwait.'),
('Kuwait Fire Service Directorate',  'Fire Department', 'https://www.kff.gov.kw',     'Approves fire and life safety systems for buildings and facilities in Kuwait.'),
('Ministry of Electricity, Water and Renewable Energy', 'Electricity', 'https://www.mew.gov.kw', 'Handles electricity and water connection approvals across Kuwait.');

SET @a_km   = (SELECT id FROM government_authorities WHERE name = 'Kuwait Municipality');
SET @a_kfsd = (SELECT id FROM government_authorities WHERE name = 'Kuwait Fire Service Directorate');
SET @a_mew  = (SELECT id FROM government_authorities WHERE name = 'Ministry of Electricity, Water and Renewable Energy');

INSERT INTO government_forms (authority_id, form_code, title, version, language, category, description, required_documents, status) VALUES
(@a_km,   'KM-101',   'Building Permit Application',      '2.1', 'English / Arabic', 'Building Permit',      'Application for a new building permit or major renovation.',   JSON_ARRAY('Trade Licence','Site Plan','Structural Drawings','Ownership Proof'), 'Active'),
(@a_kfsd, 'KFSD-204', 'Fire Safety Approval',             '1.4', 'English',          'Fire Safety Approval', 'Approval of fire and life safety systems prior to occupancy.', JSON_ARRAY('Fire System Drawings','Material Safety Data Sheets','Structural Drawings'), 'Active'),
(@a_mew,  'MEW-310',  'Utility Connection Request',       '3.0', 'English / Arabic', 'Utility Connection',   'Request for electricity and water connection to a new or renovated facility.', JSON_ARRAY('Building Completion Certificate','Ownership Proof'), 'Active');

SET @f_km101   = (SELECT id FROM government_forms WHERE form_code = 'KM-101');
SET @f_kfsd204 = (SELECT id FROM government_forms WHERE form_code = 'KFSD-204');

SET @permit_baladia = (SELECT id FROM permit_catalog_items WHERE name = 'Baladia Permits');
SET @permit_kfd     = (SELECT id FROM permit_catalog_items WHERE name = 'KFD Permits');

-- ----------------------------------------------------------------------------
-- Projects (20 -- 4 per client)
-- ----------------------------------------------------------------------------
-- Al Reem Development LLC: Requirement (ready to confirm) -> Quotation ->
-- Payment Plan -> Contract (unsigned, parked), one project per stage of
-- the straight-line front half of the workflow.
INSERT INTO projects (project_no, project_name, client_id, service, engineer_id, current_stage, description, scope_client_confirmed_at, progress, priority, start_date, target_date, status) VALUES
('2600001', 'Al Reem Residential Tower - Structural Design', @c_alreem, 'Structural Engineering', @u_layla, 'Requirement', 'Structural design and analysis for a 12-storey residential tower, covering foundation, superstructure, and seismic assessment.', NULL, 0, 'Medium', '2026-08-01', '2027-02-15', 'Active'),
('2600002', 'Al Reem Tower - MEP Coordination',              @c_alreem, 'MEP Design',             @u_ahmed, 'Quotation',   'MEP coordination and shop-drawing review for the residential tower.', '2026-07-12 10:00:00', 0, 'Medium', '2026-07-10', '2026-12-20', 'Active'),
('2600003', 'Al Reem Annex Building',                        @c_alreem, 'Structural Engineering', @u_layla, 'Payment Plan','Structural design for a new annex building adjoining the main tower.', '2026-06-16 09:30:00', 0, 'Medium', '2026-06-15', '2027-01-10', 'Active'),
('2600004', 'Al Reem Parking Structure',                     @c_alreem, 'Structural Engineering', @u_layla, 'Contract',    'Structural design of a multi-level parking structure for the development.', '2026-05-21 09:00:00', 0, 'Low',    '2026-05-20', '2026-12-01', 'Active');

-- Falcon Heights Logistics: one project per single track (Design /
-- Government Submission / Supervision alone), plus a Design+Permits combo
-- with a Cancelled item sitting next to a still-open one.
INSERT INTO projects (project_no, project_name, client_id, service, engineer_id, current_stage, description, scope_client_confirmed_at, progress, priority, start_date, target_date, status) VALUES
('2600005', 'Falcon Heights Warehouse Expansion',       @c_falcon, 'MEP Design',                       @u_ahmed, 'Design',                'MEP design for the warehouse expansion, covering concept through construction-issue drawings.', '2026-05-15 09:00:00', 19, 'High',   '2026-05-14', '2026-11-30', 'Active'),
('2600006', 'Falcon Heights Cold Storage Unit - Permits', @c_falcon, 'Government Submission Services',  @u_ahmed, 'Government Submission', 'Municipality and fire authority permitting for a new cold storage unit.',                         '2026-04-02 09:00:00', 10, 'High',   '2026-04-01', '2026-10-15', 'Active'),
('2600007', 'Falcon Heights Rooftop Solar Retrofit',     @c_falcon, 'Supervision Services',             @u_ahmed, 'Supervision',            'Ongoing site supervision for a rooftop solar retrofit.',                                          '2026-03-02 09:00:00', 15, 'Medium', '2026-03-01', '2026-09-30', 'Active'),
('2600008', 'Falcon Heights Loading Dock Upgrade',       @c_falcon, 'MEP Design',                       @u_ahmed, 'Design',                'MEP design and permitting for a loading dock capacity upgrade -- electrical layout scope was later descoped.', '2026-02-16 09:00:00', 25, 'Medium', '2026-02-15', '2026-08-30', 'Active');

-- Marina Bay Hospitality Group: the existing Design+Supervision hotel
-- renovation, a Design+Permits+Supervision triple-track spa wing, and two
-- Handover-stage projects showing the two different sub-states (payment
-- not yet confirmed / payment confirmed but not yet acknowledged).
INSERT INTO projects (project_no, project_name, client_id, service, engineer_id, current_stage, description, scope_client_confirmed_at, progress, priority, start_date, target_date, status, supervision_start_date, supervision_end_date, supervision_monthly_total, handover_sent_at, handover_payment_confirmed_at, handover_payment_confirmed_by) VALUES
('2600009', 'Marina Bay Hotel Renovation',   @c_marina, 'Architectural Design', @u_layla, 'Design',      'Full architectural renovation design and site supervision for Marina Bay Hotel, including interior scope.', '2026-03-11 09:00:00', 34, 'High',   '2026-03-10', '2026-10-05', 'Active', '2026-04-11', '2026-10-05', 350.00, NULL, NULL, NULL),
('2600010', 'Marina Bay Spa Wing Extension', @c_marina, 'Architectural Design', @u_layla, 'Supervision', 'New spa wing extension: design, building permit, and ongoing site supervision.',                             '2026-04-02 09:00:00', 39, 'High',   '2026-04-01', '2026-11-15', 'Active', '2026-06-01', '2027-02-01', 190.00, NULL, NULL, NULL),
('2600011', 'Marina Bay Banquet Hall Refurb',@c_marina, 'Architectural Design', @u_layla, 'Handover',    'Renovation design for the banquet hall -- design complete, awaiting payment confirmation before final hand-over.', '2026-01-16 09:00:00', 90, 'Medium', '2026-01-15', '2026-07-30', 'Active', NULL, NULL, NULL, '2026-08-01 09:00:00', NULL, NULL),
('2600012', 'Marina Bay Rooftop Lounge',     @c_marina, 'Architectural Design', @u_layla, 'Handover',    'Design and building permit for a new rooftop lounge -- payment confirmed, awaiting the client''s signed hand-over acknowledgment.', '2025-12-02 09:00:00', 90, 'Medium', '2025-12-01', '2026-06-15', 'Active', NULL, NULL, NULL, '2026-05-10 09:00:00', '2026-05-15 14:00:00', @u_admin);

-- Ahmadi Industrial Holdings: the existing Government Submission project,
-- the zero-track Contract -> Handover auto-advance demonstration project,
-- an On Hold project, and a project carrying one deliberately overdue task.
INSERT INTO projects (project_no, project_name, client_id, service, engineer_id, current_stage, description, scope_client_confirmed_at, progress, priority, start_date, target_date, status) VALUES
('2600013', 'Ahmadi Industrial Facility - Fire Safety Approval', @c_ahmadi, 'Fire & Safety Engineering', @u_ahmed, 'Government Submission', 'Fire suppression system design and Kuwait Fire Service Directorate permitting for the industrial facility.', '2026-01-21 09:00:00', 20, 'High',   '2026-01-20', '2026-08-15', 'Active'),
('2600014', 'Ahmadi Warehouse Fire Suppression Retrofit',        @c_ahmadi, 'Fire & Safety Engineering', @u_ahmed, 'Contract',              'Fixed-scope fire suppression retrofit -- design and oversight only, no permits or supervision selected.',    '2026-07-02 09:00:00', 0,  'Medium', '2026-07-01', '2026-10-01', 'Active'),
('2600015', 'Ahmadi Plant Expansion',                            @c_ahmadi, 'Fire & Safety Engineering', @u_ahmed, 'Design',                'Plant expansion layout and fire safety systems design -- on hold pending client budget approval.',           '2026-02-02 09:00:00', 40, 'Medium', '2026-02-01', '2026-09-01', 'On Hold'),
('2600016', 'Ahmadi Admin Building Refurbishment',               @c_ahmadi, 'Fire & Safety Engineering', @u_ahmed, 'Design',                'Fire exit redesign for the administration building.',                                                          '2026-01-06 09:00:00', 10, 'Medium', '2026-01-05', '2026-07-01', 'Active');

-- Khalid Al Mansoori: the existing Completed handover, a Requirement-stage
-- project not yet ready to confirm (no scope written up), a Quotation-
-- stage project, and a project cancelled early.
INSERT INTO projects (project_no, project_name, client_id, service, engineer_id, current_stage, description, scope_client_confirmed_at, progress, priority, start_date, target_date, status, handover_sent_at, handover_payment_confirmed_at, handover_payment_confirmed_by, handover_acknowledged_at) VALUES
('2600017', 'Desert Rose Retail Plaza - Final Handover',   @c_khalid, 'Civil Engineering', @u_ahmed, 'Handover',    'Civil engineering design and final hand-over for the Desert Rose retail plaza.', '2025-09-03 09:00:00', 100, 'Low', '2025-09-01', '2026-03-20', 'Completed', '2026-03-18 09:00:00', '2026-03-16 10:00:00', @u_admin, '2026-03-20 11:00:00'),
('2600018', 'Khalid Villa Renovation',                      @c_khalid, 'Architectural Design', @u_layla, 'Requirement', NULL, NULL, 0, 'Low', '2026-08-20', '2027-03-01', 'Active', NULL, NULL, NULL, NULL),
('2600019', 'Khalid Al Mansoori Residence - Landscape Design', @c_khalid, 'Landscape Design', @u_ahmed, 'Quotation', 'Landscape design for the residence''s front and rear garden.', '2026-07-03 09:00:00', 0, 'Low', '2026-07-01', '2026-12-15', 'Active', NULL, NULL, NULL, NULL),
('2600020', 'Khalid Guest House Addition',                  @c_khalid, 'Civil Engineering', @u_layla, 'Requirement', 'Proposed guest house addition -- cancelled before a scope was finalised.', NULL, 0, 'Low', '2026-06-01', '2026-11-01', 'Cancelled', NULL, NULL, NULL, NULL);

SET @p_alreem_tower     = (SELECT id FROM projects WHERE project_no = '2600001');
SET @p_alreem_mep       = (SELECT id FROM projects WHERE project_no = '2600002');
SET @p_alreem_annex     = (SELECT id FROM projects WHERE project_no = '2600003');
SET @p_alreem_parking   = (SELECT id FROM projects WHERE project_no = '2600004');
SET @p_falcon_warehouse = (SELECT id FROM projects WHERE project_no = '2600005');
SET @p_falcon_coldstore = (SELECT id FROM projects WHERE project_no = '2600006');
SET @p_falcon_solar     = (SELECT id FROM projects WHERE project_no = '2600007');
SET @p_falcon_dock      = (SELECT id FROM projects WHERE project_no = '2600008');
SET @p_marina_hotel     = (SELECT id FROM projects WHERE project_no = '2600009');
SET @p_marina_spa       = (SELECT id FROM projects WHERE project_no = '2600010');
SET @p_marina_banquet   = (SELECT id FROM projects WHERE project_no = '2600011');
SET @p_marina_rooftop   = (SELECT id FROM projects WHERE project_no = '2600012');
SET @p_ahmadi_fire      = (SELECT id FROM projects WHERE project_no = '2600013');
SET @p_ahmadi_warehouse = (SELECT id FROM projects WHERE project_no = '2600014');
SET @p_ahmadi_plant     = (SELECT id FROM projects WHERE project_no = '2600015');
SET @p_ahmadi_admin     = (SELECT id FROM projects WHERE project_no = '2600016');
SET @p_desert           = (SELECT id FROM projects WHERE project_no = '2600017');
SET @p_khalid_villa     = (SELECT id FROM projects WHERE project_no = '2600018');
SET @p_khalid_landscape = (SELECT id FROM projects WHERE project_no = '2600019');
SET @p_khalid_guesthouse= (SELECT id FROM projects WHERE project_no = '2600020');

-- ----------------------------------------------------------------------------
-- Selected Design activities / Permits / Supervision activities
-- ----------------------------------------------------------------------------
-- Al Reem Annex Building (Payment Plan stage) and Al Reem Parking
-- Structure (Contract stage, contract still unsigned) -- both need a
-- selected Design item on file so compute_stage_flags reads them as
-- includes_design=True; without one, the Payment Plan -> Contract and
-- Contract -> Design/Handover exit checks below silently skip the
-- Design-specific gate entirely (nothing to check) and the project
-- would auto-advance past its intended stage on the very first read,
-- exactly like the deliberate zero-track demo project further down.
-- No service tasks generated yet either way -- see
-- project_service._create_service_tasks, only fires once Contract is
-- actually left.
INSERT INTO project_selected_activities (project_id, service_id, service_name, activity_id, activity_name, fixed_cost, status) VALUES
(@p_alreem_annex,   'SVC-STR', 'Structural Engineering', 'ACT-101', 'Annex Building Design',    220000.00, 'Not Started'),
(@p_alreem_parking, 'SVC-STR', 'Structural Engineering', 'ACT-201', 'Parking Structure Design', 165000.00, 'Not Started');

-- Falcon Heights Warehouse Expansion -- single Design track, mixed status.
INSERT INTO project_selected_activities (project_id, service_id, service_name, activity_id, activity_name, fixed_cost, status, closed_at, closed_by) VALUES
(@p_falcon_warehouse, 'SVC-MEP', 'MEP Design', 'ACT-301', 'MEP Concept Design',        82000.00, 'Complete',    '2026-06-01 16:00:00', @u_ahmed),
(@p_falcon_warehouse, 'SVC-MEP', 'MEP Design', 'ACT-302', 'MEP Detailed Design',       82000.00, 'In Progress', NULL, NULL),
(@p_falcon_warehouse, 'SVC-MEP', 'MEP Design', 'ACT-303', 'MEP Coordination Drawings', 82000.00, 'Not Started', NULL, NULL);

-- Falcon Heights Cold Storage Unit -- single Permits track.
INSERT INTO project_selected_permits (project_id, permit_catalog_item_id, permit_name, status, permit_price) VALUES
(@p_falcon_coldstore, @permit_baladia, 'Cold Storage Building Permit',      'In Progress', 8000.00),
(@p_falcon_coldstore, @permit_kfd,     'Cold Storage Fire Safety Permit',   'Planned',     6000.00);

-- Falcon Heights Rooftop Solar Retrofit -- single Supervision track.
INSERT INTO project_selected_supervision_activities (project_id, activity_id, activity_name, monthly_rate, start_date, end_date, status) VALUES
(@p_falcon_solar, 'ACT-401', 'Weekly Site Visits',  150.00, '2026-03-01', '2026-09-30', 'In Progress'),
(@p_falcon_solar, 'ACT-402', 'Progress Reporting',   80.00, '2026-03-01', '2026-09-30', 'Planned');

-- Falcon Heights Loading Dock Upgrade -- Design+Permits combo, one Design
-- activity Cancelled (descoped) sitting next to one still In Progress.
INSERT INTO project_selected_activities (project_id, service_id, service_name, activity_id, activity_name, fixed_cost, status, closed_at, closed_by) VALUES
(@p_falcon_dock, 'SVC-MEP', 'MEP Design', 'ACT-501', 'Loading Dock MEP Design',        90000.00, 'In Progress', NULL, NULL),
(@p_falcon_dock, 'SVC-MEP', 'MEP Design', 'ACT-502', 'Loading Dock Electrical Layout',  40000.00, 'Cancelled',   '2026-04-01 12:00:00', @u_ahmed);
INSERT INTO project_selected_permits (project_id, permit_catalog_item_id, permit_name, status, permit_price) VALUES
(@p_falcon_dock, @permit_baladia, 'Loading Dock Access Permit', 'In Progress', 5000.00);

-- Marina Bay Hotel Renovation -- Design track (previously missing from
-- seed data entirely) alongside the existing Supervision track.
INSERT INTO project_selected_activities (project_id, service_id, service_name, activity_id, activity_name, fixed_cost, status, closed_at, closed_by) VALUES
(@p_marina_hotel, 'SVC-ARCH', 'Architectural Design', 'ACT-601', 'Architectural Concept Design',   150000.00, 'Complete',    '2026-05-01 15:00:00', @u_layla),
(@p_marina_hotel, 'SVC-ARCH', 'Architectural Design', 'ACT-602', 'Detailed Architectural Drawings', 180000.00, 'In Progress', NULL, NULL),
(@p_marina_hotel, 'SVC-ARCH', 'Architectural Design', 'ACT-603', 'Interior Renovation Design',       82000.00, 'Not Started', NULL, NULL);
INSERT INTO project_selected_supervision_activities (project_id, activity_id, activity_name, monthly_rate, start_date, end_date, status) VALUES
(@p_marina_hotel, 'ACT-101', 'Weekly Site Visits', 250.00, '2026-04-11', '2026-10-05', 'In Progress'),
(@p_marina_hotel, 'ACT-102', 'Progress Reporting', 100.00, '2026-04-01', '2026-10-05', 'In Progress');

-- Marina Bay Spa Wing Extension -- all three tracks at once.
INSERT INTO project_selected_activities (project_id, service_id, service_name, activity_id, activity_name, fixed_cost, status, closed_at, closed_by) VALUES
(@p_marina_spa, 'SVC-ARCH', 'Architectural Design', 'ACT-701', 'Spa Wing Concept Design',  120000.00, 'Complete',    '2026-05-15 15:00:00', @u_layla),
(@p_marina_spa, 'SVC-ARCH', 'Architectural Design', 'ACT-702', 'Spa Wing Detailed Design', 130000.00, 'In Progress', NULL, NULL);
INSERT INTO project_selected_permits (project_id, permit_catalog_item_id, permit_name, status, eligibility_met_at, permit_price) VALUES
(@p_marina_spa, @permit_baladia, 'Spa Wing Building Permit', 'Eligible', '2026-05-16 09:00:00', 10000.00);
INSERT INTO project_selected_supervision_activities (project_id, activity_id, activity_name, monthly_rate, start_date, end_date, status) VALUES
(@p_marina_spa, 'ACT-703', 'Weekly Site Visits - Spa Wing',  120.00, '2026-06-01', '2027-02-01', 'In Progress'),
(@p_marina_spa, 'ACT-704', 'Progress Reporting - Spa Wing',   70.00, '2026-06-01', '2027-02-01', 'Planned');

-- Marina Bay Banquet Hall Refurb -- single Design track, fully Complete
-- (Handover sub-state A: sent, payment not yet confirmed).
INSERT INTO project_selected_activities (project_id, service_id, service_name, activity_id, activity_name, fixed_cost, status, closed_at, closed_by) VALUES
(@p_marina_banquet, 'SVC-ARCH', 'Architectural Design', 'ACT-801', 'Banquet Hall Renovation Design', 160000.00, 'Complete', '2026-06-20 15:00:00', @u_layla);

-- Marina Bay Rooftop Lounge -- Design+Permits, both fully Complete
-- (Handover sub-state B: payment confirmed, acknowledgment still pending).
INSERT INTO project_selected_activities (project_id, service_id, service_name, activity_id, activity_name, fixed_cost, status, closed_at, closed_by) VALUES
(@p_marina_rooftop, 'SVC-ARCH', 'Architectural Design', 'ACT-901', 'Rooftop Lounge Design', 140000.00, 'Complete', '2026-04-10 15:00:00', @u_layla);
INSERT INTO project_selected_permits (project_id, permit_catalog_item_id, permit_name, status, closed_at, closed_by, permit_price) VALUES
(@p_marina_rooftop, @permit_baladia, 'Rooftop Lounge Building Permit', 'Complete', '2026-05-01 12:00:00', @u_ahmed, 12000.00);

-- Ahmadi Industrial Facility -- single Permits track.
INSERT INTO project_selected_permits (project_id, permit_catalog_item_id, permit_name, status, permit_price) VALUES
(@p_ahmadi_fire, @permit_kfd, 'Fire Suppression System Permit', 'In Progress', 15000.00);

-- Ahmadi Warehouse Fire Suppression Retrofit -- deliberately ZERO selected
-- Design/Permit/Supervision items, and zero tasks (see below) -- the
-- self-heal auto-advance demo project (see header comment).

-- Ahmadi Plant Expansion -- single Design track, On Hold status.
INSERT INTO project_selected_activities (project_id, service_id, service_name, activity_id, activity_name, fixed_cost, status, closed_at, closed_by) VALUES
(@p_ahmadi_plant, 'SVC-FIRE', 'Fire & Safety Engineering', 'ACT-1001', 'Plant Layout Design',          95000.00, 'Complete',    '2026-05-01 15:00:00', @u_ahmed),
(@p_ahmadi_plant, 'SVC-FIRE', 'Fire & Safety Engineering', 'ACT-1002', 'Plant Safety Systems Design',  90000.00, 'In Progress', NULL, NULL);

-- Ahmadi Admin Building Refurbishment -- single Design track, carries the
-- deliberately overdue task below.
INSERT INTO project_selected_activities (project_id, service_id, service_name, activity_id, activity_name, fixed_cost, status) VALUES
(@p_ahmadi_admin, 'SVC-FIRE', 'Fire & Safety Engineering', 'ACT-1101', 'Admin Building Fire Exit Design', 68000.00, 'In Progress');

-- Desert Rose Retail Plaza -- single Design track, Complete (matches the
-- project's Completed status/100% progress).
INSERT INTO project_selected_activities (project_id, service_id, service_name, activity_id, activity_name, fixed_cost, status, closed_at, closed_by) VALUES
(@p_desert, 'SVC-CIVIL', 'Civil Engineering', 'ACT-1201', 'Final Civil Handover Package', 98000.00, 'Complete', '2026-03-15 14:00:00', @u_ahmed);

SET @act_falcon_wh_concept    = (SELECT id FROM project_selected_activities WHERE project_id = @p_falcon_warehouse AND activity_id = 'ACT-301');
SET @act_falcon_wh_detail     = (SELECT id FROM project_selected_activities WHERE project_id = @p_falcon_warehouse AND activity_id = 'ACT-302');
SET @act_falcon_wh_coord      = (SELECT id FROM project_selected_activities WHERE project_id = @p_falcon_warehouse AND activity_id = 'ACT-303');
SET @perm_falcon_cs_building  = (SELECT id FROM project_selected_permits WHERE project_id = @p_falcon_coldstore AND permit_name = 'Cold Storage Building Permit');
SET @perm_falcon_cs_fire      = (SELECT id FROM project_selected_permits WHERE project_id = @p_falcon_coldstore AND permit_name = 'Cold Storage Fire Safety Permit');
SET @sup_falcon_solar_visits  = (SELECT id FROM project_selected_supervision_activities WHERE project_id = @p_falcon_solar AND activity_id = 'ACT-401');
SET @sup_falcon_solar_reports = (SELECT id FROM project_selected_supervision_activities WHERE project_id = @p_falcon_solar AND activity_id = 'ACT-402');
SET @act_falcon_dock_mep      = (SELECT id FROM project_selected_activities WHERE project_id = @p_falcon_dock AND activity_id = 'ACT-501');
SET @perm_falcon_dock_access  = (SELECT id FROM project_selected_permits WHERE project_id = @p_falcon_dock AND permit_name = 'Loading Dock Access Permit');
SET @act_marina_hotel_concept = (SELECT id FROM project_selected_activities WHERE project_id = @p_marina_hotel AND activity_id = 'ACT-601');
SET @act_marina_hotel_detail  = (SELECT id FROM project_selected_activities WHERE project_id = @p_marina_hotel AND activity_id = 'ACT-602');
SET @sup_marina_hotel_visits  = (SELECT id FROM project_selected_supervision_activities WHERE project_id = @p_marina_hotel AND activity_id = 'ACT-101');
SET @sup_marina_hotel_reports = (SELECT id FROM project_selected_supervision_activities WHERE project_id = @p_marina_hotel AND activity_id = 'ACT-102');
SET @act_marina_spa_concept   = (SELECT id FROM project_selected_activities WHERE project_id = @p_marina_spa AND activity_id = 'ACT-701');
SET @act_marina_spa_detail    = (SELECT id FROM project_selected_activities WHERE project_id = @p_marina_spa AND activity_id = 'ACT-702');
SET @perm_marina_spa_building = (SELECT id FROM project_selected_permits WHERE project_id = @p_marina_spa AND permit_name = 'Spa Wing Building Permit');
SET @sup_marina_spa_visits    = (SELECT id FROM project_selected_supervision_activities WHERE project_id = @p_marina_spa AND activity_id = 'ACT-703');
SET @sup_marina_spa_reports   = (SELECT id FROM project_selected_supervision_activities WHERE project_id = @p_marina_spa AND activity_id = 'ACT-704');
SET @act_marina_banquet       = (SELECT id FROM project_selected_activities WHERE project_id = @p_marina_banquet AND activity_id = 'ACT-801');
SET @act_marina_rooftop       = (SELECT id FROM project_selected_activities WHERE project_id = @p_marina_rooftop AND activity_id = 'ACT-901');
SET @perm_marina_rooftop      = (SELECT id FROM project_selected_permits WHERE project_id = @p_marina_rooftop AND permit_name = 'Rooftop Lounge Building Permit');
SET @perm_ahmadi_fire         = (SELECT id FROM project_selected_permits WHERE project_id = @p_ahmadi_fire AND permit_name = 'Fire Suppression System Permit');
SET @act_ahmadi_plant_layout  = (SELECT id FROM project_selected_activities WHERE project_id = @p_ahmadi_plant AND activity_id = 'ACT-1001');
SET @act_ahmadi_plant_safety  = (SELECT id FROM project_selected_activities WHERE project_id = @p_ahmadi_plant AND activity_id = 'ACT-1002');
SET @act_ahmadi_admin_exit    = (SELECT id FROM project_selected_activities WHERE project_id = @p_ahmadi_admin AND activity_id = 'ACT-1101');
SET @act_desert_handover      = (SELECT id FROM project_selected_activities WHERE project_id = @p_desert AND activity_id = 'ACT-1201');

-- ----------------------------------------------------------------------------
-- Government submissions
-- ----------------------------------------------------------------------------
INSERT INTO government_submissions (submission_no, project_id, authority_id, form_id, project_selected_permit_id, status, submitted_date, expected_decision_date, decision_date, response_outcome, notes) VALUES
('SUB-2026-001', @p_falcon_coldstore, @a_km,   @f_km101,   @perm_falcon_cs_building, 'Draft',        NULL,         NULL,         NULL,         NULL,       'Preparing building permit application for the cold storage unit.'),
('SUB-2026-002', @p_falcon_coldstore, @a_kfsd, @f_kfsd204, @perm_falcon_cs_fire,     'Under Review', '2026-06-20', '2026-08-10', NULL,         NULL,       'Fire safety drawings submitted for the cold storage unit.'),
('SUB-2026-003', @p_ahmadi_fire,      @a_kfsd, @f_kfsd204, @perm_ahmadi_fire,        'Under Review', '2026-06-15', '2026-08-01', NULL,         NULL,       'Submitted fire suppression drawings for the industrial facility.'),
('SUB-2026-004', @p_marina_rooftop,   @a_km,   @f_km101,   @perm_marina_rooftop,     'Approved',     '2026-04-05', '2026-04-25', '2026-04-25', 'Approved', 'Rooftop lounge building permit approved without conditions.');

SET @sub_falcon_cs_building = (SELECT id FROM government_submissions WHERE submission_no = 'SUB-2026-001');
SET @sub_falcon_cs_fire     = (SELECT id FROM government_submissions WHERE submission_no = 'SUB-2026-002');
SET @sub_ahmadi_fire        = (SELECT id FROM government_submissions WHERE submission_no = 'SUB-2026-003');

INSERT INTO submission_documents (submission_id, name, status) VALUES
(@sub_falcon_cs_building, 'Trade Licence',              'Uploaded'),
(@sub_falcon_cs_building, 'Site Plan',                  'Pending'),
(@sub_falcon_cs_fire,     'Fire System Drawings',       'Uploaded'),
(@sub_ahmadi_fire,        'Fire System Drawings',       'Uploaded'),
(@sub_ahmadi_fire,        'Material Safety Data Sheets','Uploaded'),
(@sub_ahmadi_fire,        'Structural Drawings',        'Verified');

-- ----------------------------------------------------------------------------
-- Quotations
-- ----------------------------------------------------------------------------
INSERT INTO quotations (quotation_no, project_id, revision, issue_date, validity, status, currency, prepared_by, discount_amount, notes, terms_and_conditions, amount) VALUES
('QUO-2026-001', @p_alreem_mep,       'R0', '2026-07-12', '2026-08-11', 'Draft',    'AED', @u_pm, 0,    'MEP coordination quotation for the residential tower.',   JSON_ARRAY('Valid for 30 days from issue date.'), 95000.00),
('QUO-2026-002', @p_alreem_annex,     'R0', '2026-06-16', '2026-07-16', 'Approved', 'AED', @u_pm, 0,    'Structural design quotation for the annex building.',     JSON_ARRAY('Valid for 30 days from issue date.'), 220000.00),
('QUO-2026-003', @p_alreem_parking,   'R0', '2026-05-21', '2026-06-20', 'Approved', 'AED', @u_pm, 0,    'Structural design quotation for the parking structure.',  JSON_ARRAY('Valid for 30 days from issue date.'), 165000.00),
('QUO-2026-004', @p_falcon_warehouse, 'R1', '2026-05-20', '2026-06-19', 'Approved', 'AED', @u_pm, 5000, 'MEP design for the warehouse expansion, revised after client feedback.', JSON_ARRAY('Valid for 30 days from issue date.','Payment terms per signed agreement.'), 246000.00),
('QUO-2026-005', @p_falcon_coldstore, 'R0', '2026-04-02', '2026-05-02', 'Approved', 'AED', @u_pm, 0,    'Government submission preparation and filing for the cold storage unit.', JSON_ARRAY('Valid for 30 days from issue date.'), 58000.00),
('QUO-2026-006', @p_falcon_solar,     'R0', '2026-03-02', '2026-04-01', 'Approved', 'AED', @u_pm, 0,    'Site supervision services for the rooftop solar retrofit.',              JSON_ARRAY('Valid for 30 days from issue date.'), 42000.00),
('QUO-2026-007', @p_falcon_dock,      'R0', '2026-02-16', '2026-03-18', 'Approved', 'AED', @u_pm, 0,    'MEP design and permitting for the loading dock upgrade.',                JSON_ARRAY('Valid for 30 days from issue date.'), 130000.00),
('QUO-2026-008', @p_marina_hotel,     'R0', '2026-03-15', '2026-04-14', 'Approved', 'AED', @u_pm, 0,    'Architectural renovation design for Marina Bay Hotel.',   JSON_ARRAY('Valid for 30 days from issue date.','Site survey included in scope.'), 412000.00),
('QUO-2026-009', @p_marina_spa,       'R0', '2026-04-02', '2026-05-02', 'Approved', 'AED', @u_pm, 0,    'Spa wing extension design and supervision setup.',        JSON_ARRAY('Valid for 30 days from issue date.'), 250000.00),
('QUO-2026-010', @p_marina_banquet,   'R0', '2026-01-16', '2026-02-15', 'Approved', 'AED', @u_pm, 0,    'Banquet hall renovation design.',                          JSON_ARRAY('Valid for 30 days from issue date.'), 160000.00),
('QUO-2026-011', @p_marina_rooftop,   'R0', '2025-12-02', '2026-01-01', 'Approved', 'AED', @u_pm, 0,    'Rooftop lounge design.',                                   JSON_ARRAY('Valid for 30 days from issue date.'), 140000.00),
('QUO-2026-012', @p_ahmadi_fire,      'R0', '2026-01-21', '2026-02-20', 'Approved', 'AED', @u_pm, 0,    'Fire safety system design and submission for the industrial facility.', JSON_ARRAY('Valid for 30 days from issue date.'), 95000.00),
('QUO-2026-013', @p_ahmadi_warehouse, 'R0', '2026-07-02', '2026-08-01', 'Approved', 'AED', @u_pm, 0,    'Fire suppression retrofit design and installation oversight, fixed scope.', JSON_ARRAY('Valid for 30 days from issue date.'), 75000.00),
('QUO-2026-014', @p_ahmadi_plant,     'R0', '2026-02-02', '2026-03-04', 'Approved', 'AED', @u_pm, 0,    'Plant expansion layout and safety systems design.',       JSON_ARRAY('Valid for 30 days from issue date.'), 185000.00),
('QUO-2026-015', @p_ahmadi_admin,     'R0', '2026-01-06', '2026-02-05', 'Approved', 'AED', @u_pm, 0,    'Fire exit redesign for the administration building.',     JSON_ARRAY('Valid for 30 days from issue date.'), 68000.00),
('QUO-2026-016', @p_desert,           'R0', '2025-09-03', '2025-10-03', 'Approved', 'AED', @u_pm, 0,    'Civil engineering design and final hand-over package.',   JSON_ARRAY('Valid for 30 days from issue date.'), 98000.00),
('QUO-2026-017', @p_khalid_landscape, 'R0', '2026-07-03', '2026-08-02', 'Draft',    'AED', @u_pm, 0,    'Landscape design for the residence front and rear garden.', JSON_ARRAY('Valid for 30 days from issue date.'), 38000.00);

SET @q_alreem_mep       = (SELECT id FROM quotations WHERE quotation_no = 'QUO-2026-001');
SET @q_alreem_annex     = (SELECT id FROM quotations WHERE quotation_no = 'QUO-2026-002');
SET @q_alreem_parking   = (SELECT id FROM quotations WHERE quotation_no = 'QUO-2026-003');
SET @q_falcon_warehouse = (SELECT id FROM quotations WHERE quotation_no = 'QUO-2026-004');
SET @q_falcon_coldstore = (SELECT id FROM quotations WHERE quotation_no = 'QUO-2026-005');
SET @q_falcon_solar     = (SELECT id FROM quotations WHERE quotation_no = 'QUO-2026-006');
SET @q_falcon_dock      = (SELECT id FROM quotations WHERE quotation_no = 'QUO-2026-007');
SET @q_marina_hotel     = (SELECT id FROM quotations WHERE quotation_no = 'QUO-2026-008');
SET @q_marina_spa       = (SELECT id FROM quotations WHERE quotation_no = 'QUO-2026-009');
SET @q_marina_banquet   = (SELECT id FROM quotations WHERE quotation_no = 'QUO-2026-010');
SET @q_marina_rooftop   = (SELECT id FROM quotations WHERE quotation_no = 'QUO-2026-011');
SET @q_ahmadi_fire      = (SELECT id FROM quotations WHERE quotation_no = 'QUO-2026-012');
SET @q_ahmadi_warehouse = (SELECT id FROM quotations WHERE quotation_no = 'QUO-2026-013');
SET @q_ahmadi_plant     = (SELECT id FROM quotations WHERE quotation_no = 'QUO-2026-014');
SET @q_ahmadi_admin     = (SELECT id FROM quotations WHERE quotation_no = 'QUO-2026-015');
SET @q_desert           = (SELECT id FROM quotations WHERE quotation_no = 'QUO-2026-016');

INSERT INTO quotation_line_items (quotation_id, description, quantity, unit_price) VALUES
(@q_alreem_mep,       'MEP concept design',                    1, 60000.00),
(@q_alreem_mep,       'MEP detailed design',                   1, 35000.00),
(@q_alreem_annex,     'Structural design and analysis',        1, 140000.00),
(@q_alreem_annex,     'Structural drawings and specifications',1, 80000.00),
(@q_alreem_parking,   'Structural design and analysis',        1, 100000.00),
(@q_alreem_parking,   'Structural drawings and specifications',1, 65000.00),
(@q_falcon_warehouse, 'MEP concept and detailed design',       1, 180000.00),
(@q_falcon_warehouse, 'MEP coordination and site supervision', 1, 71000.00),
(@q_falcon_coldstore, 'Government submission preparation and filing', 1, 58000.00),
(@q_falcon_solar,     'Site supervision services',              1, 42000.00),
(@q_falcon_dock,      'Loading dock MEP design',                1, 90000.00),
(@q_falcon_dock,      'Loading dock electrical layout',         1, 40000.00),
(@q_marina_hotel,     'Architectural concept design',           1, 150000.00),
(@q_marina_hotel,     'Detailed architectural drawings',        1, 180000.00),
(@q_marina_hotel,     'Interior renovation design',              1, 82000.00),
(@q_marina_spa,       'Spa wing concept design',                 1, 120000.00),
(@q_marina_spa,       'Spa wing detailed design',                1, 130000.00),
(@q_marina_banquet,   'Banquet hall renovation design',          1, 160000.00),
(@q_marina_rooftop,   'Rooftop lounge design',                   1, 140000.00),
(@q_ahmadi_fire,      'Fire safety system design and submission',1, 95000.00),
(@q_ahmadi_warehouse, 'Fire suppression retrofit design and installation oversight', 1, 75000.00),
(@q_ahmadi_plant,     'Plant layout design',                     1, 95000.00),
(@q_ahmadi_plant,     'Plant safety systems design',             1, 90000.00),
(@q_ahmadi_admin,     'Admin building fire exit design',         1, 68000.00),
(@q_desert,           'Civil engineering design and final hand-over package', 1, 98000.00);

-- ----------------------------------------------------------------------------
-- Contracts
-- ----------------------------------------------------------------------------
INSERT INTO contracts (contract_no, project_id, revision, currency, contract_value, issue_date, signed_date, expiry_date, status, prepared_by, client_representative, scope_summary) VALUES
('CON-2026-001', @p_alreem_parking,   'R0', 'AED', 165000.00, '2026-05-25', NULL,         '2026-12-01', 'Draft',  @u_pm, 'Khalid Al Reem',   'Structural design services for the parking structure -- awaiting client signature.'),
('CON-2026-002', @p_falcon_warehouse, 'R0', 'AED', 246000.00, '2026-05-25', '2026-05-28', '2026-11-30', 'Signed', @u_pm, 'Yousef Al Amiri',  'MEP design services for the Falcon Heights warehouse expansion, covering concept through construction-issue drawings.'),
('CON-2026-003', @p_falcon_coldstore, 'R0', 'AED', 58000.00,  '2026-04-05', '2026-04-08', '2026-10-15', 'Signed', @u_pm, 'Yousef Al Amiri',  'Government submission preparation and filing for the cold storage unit permits.'),
('CON-2026-004', @p_falcon_solar,     'R0', 'AED', 42000.00,  '2026-03-05', '2026-03-08', '2026-09-30', 'Signed', @u_pm, 'Yousef Al Amiri',  'Site supervision services for the rooftop solar retrofit.'),
('CON-2026-005', @p_falcon_dock,      'R0', 'AED', 130000.00, '2026-02-19', '2026-02-22', '2026-08-30', 'Signed', @u_pm, 'Yousef Al Amiri',  'MEP design and permitting for the loading dock capacity upgrade.'),
('CON-2026-006', @p_marina_hotel,     'R0', 'AED', 412000.00, '2026-03-20', '2026-03-25', '2026-10-05', 'Active', @u_pm, 'Noura Al Sabah',   'Full architectural renovation design and site supervision for Marina Bay Hotel, including interior scope.'),
('CON-2026-007', @p_marina_spa,       'R0', 'AED', 250000.00, '2026-04-05', '2026-04-08', '2027-02-01', 'Signed', @u_pm, 'Noura Al Sabah',   'Design, permitting, and ongoing site supervision for the new spa wing extension.'),
('CON-2026-008', @p_marina_banquet,   'R0', 'AED', 160000.00, '2026-01-19', '2026-01-22', '2026-07-30', 'Active', @u_pm, 'Noura Al Sabah',   'Renovation design services for the banquet hall.'),
('CON-2026-009', @p_marina_rooftop,   'R0', 'AED', 140000.00, '2025-12-05', '2025-12-08', '2026-06-15', 'Active', @u_pm, 'Noura Al Sabah',   'Design and permitting services for the new rooftop lounge.'),
('CON-2026-010', @p_ahmadi_fire,      'R0', 'AED', 95000.00,  '2026-01-24', '2026-01-27', '2026-08-15', 'Signed', @u_pm, 'Rashid Al Nuaimi', 'Fire safety system design and permitting for the industrial facility.'),
('CON-2026-011', @p_ahmadi_warehouse, 'R0', 'AED', 75000.00,  '2026-07-05', '2026-07-08', '2026-10-01', 'Signed', @u_pm, 'Rashid Al Nuaimi', 'Fixed-scope fire suppression retrofit design and installation oversight -- no permits or supervision included.'),
('CON-2026-012', @p_ahmadi_plant,     'R0', 'AED', 185000.00, '2026-02-05', '2026-02-08', '2026-09-01', 'Signed', @u_pm, 'Rashid Al Nuaimi', 'Plant expansion layout and fire safety systems design.'),
('CON-2026-013', @p_ahmadi_admin,     'R0', 'AED', 68000.00,  '2026-01-09', '2026-01-12', '2026-07-01', 'Signed', @u_pm, 'Rashid Al Nuaimi', 'Fire exit redesign for the administration building.'),
('CON-2026-014', @p_desert,           'R0', 'AED', 98000.00,  '2025-09-05', '2025-09-08', '2026-03-20', 'Active', @u_pm, 'Khalid Al Mansoori','Civil engineering design and final hand-over services for the Desert Rose retail plaza.');

SET @con_falcon_warehouse = (SELECT id FROM contracts WHERE contract_no = 'CON-2026-002');
SET @con_marina_hotel     = (SELECT id FROM contracts WHERE contract_no = 'CON-2026-006');

INSERT INTO contract_clauses (contract_id, title, content, sort_order) VALUES
(@con_falcon_warehouse, 'Scope of Work',   'The Consultant shall provide MEP design services as detailed in the attached quotation QUO-2026-004.', 1),
(@con_falcon_warehouse, 'Payment Terms',   'Payment shall be made in three instalments per the payment schedule in the financial agreement.', 2),
(@con_falcon_warehouse, 'Termination',     'Either party may terminate this agreement with 30 days written notice.', 3),
(@con_marina_hotel,     'Scope of Work',   'The Consultant shall provide architectural design and site supervision services as detailed in QUO-2026-008.', 1),
(@con_marina_hotel,     'Payment Terms',   'Payment shall be made monthly against progress milestones.', 2),
(@con_marina_hotel,     'Confidentiality', 'Both parties agree to keep project details confidential during and after the engagement.', 3);

INSERT INTO contract_revisions (contract_id, revision, revised_at, changed_by, summary) VALUES
(@con_falcon_warehouse, 'R0', '2026-05-25', @u_pm, 'Initial contract issued to client for signature.'),
(@con_marina_hotel,     'R0', '2026-03-20', @u_pm, 'Initial contract issued to client for signature.');

-- ----------------------------------------------------------------------------
-- Financial agreements, obligations, payments
-- ----------------------------------------------------------------------------
-- Design-stream agreements. Al Reem Annex's stays Draft (parks the project
-- at Payment Plan); every other Design agreement below is Approved.
INSERT INTO financial_agreements (project_id, stream, status, contract_amount, currency, contract_start_date, contract_end_date, agreement_date, quotation_reference, contract_reference, payment_mode, payment_frequency) VALUES
(@p_alreem_annex,     'Design', 'Draft',    220000.00, 'AED', '2026-07-16', '2027-01-10', '2026-06-20', 'QUO-2026-002', NULL,            'Bank Transfer', 'Quarterly'),
(@p_alreem_parking,   'Design', 'Approved', 165000.00, 'AED', '2026-06-20', '2026-12-01', '2026-05-25', 'QUO-2026-003', 'CON-2026-001', 'Bank Transfer', 'Monthly'),
(@p_falcon_warehouse, 'Design', 'Approved', 246000.00, 'AED', '2026-05-28', '2026-11-30', '2026-05-28', 'QUO-2026-004', 'CON-2026-002', 'Bank Transfer', 'Monthly'),
(@p_falcon_dock,      'Design', 'Approved', 130000.00, 'AED', '2026-02-22', '2026-08-30', '2026-02-19', 'QUO-2026-007', 'CON-2026-005', 'Bank Transfer', 'Monthly'),
(@p_marina_hotel,     'Design', 'Approved', 412000.00, 'AED', '2026-03-25', '2026-10-05', '2026-03-25', 'QUO-2026-008', 'CON-2026-006', 'Bank Transfer', 'Monthly'),
(@p_marina_spa,       'Design', 'Approved', 250000.00, 'AED', '2026-04-08', '2027-02-01', '2026-04-05', 'QUO-2026-009', 'CON-2026-007', 'Bank Transfer', 'Monthly'),
(@p_marina_banquet,   'Design', 'Approved', 160000.00, 'AED', '2026-01-22', '2026-07-30', '2026-01-19', 'QUO-2026-010', 'CON-2026-008', 'Bank Transfer', 'Monthly'),
(@p_marina_rooftop,   'Design', 'Approved', 140000.00, 'AED', '2025-12-08', '2026-06-15', '2025-12-05', 'QUO-2026-011', 'CON-2026-009', 'Bank Transfer', 'Monthly'),
(@p_ahmadi_plant,     'Design', 'Approved', 185000.00, 'AED', '2026-02-08', '2026-09-01', '2026-02-05', 'QUO-2026-014', 'CON-2026-012', 'Bank Transfer', 'Monthly'),
(@p_ahmadi_admin,     'Design', 'Approved', 68000.00,  'AED', '2026-01-12', '2026-07-01', '2026-01-09', 'QUO-2026-015', 'CON-2026-013', 'Bank Transfer', 'Monthly'),
(@p_desert,           'Design', 'Approved', 98000.00,  'AED', '2025-09-05', '2026-03-20', '2025-09-05', NULL,           NULL,           'Bank Transfer', 'One-time');

-- Supervision-stream agreements (contract_amount = sum of the monthly
-- schedule below, same convention as the Marina Bay Hotel example).
INSERT INTO financial_agreements (project_id, stream, status, contract_amount, currency, contract_start_date, contract_end_date, agreement_date, quotation_reference, contract_reference, payment_mode, payment_frequency) VALUES
(@p_falcon_solar, 'Supervision', 'Approved', 1610.00, 'AED', '2026-03-01', '2026-09-30', '2026-03-05', 'QUO-2026-006', 'CON-2026-004', 'Bank Transfer', 'Monthly'),
(@p_marina_hotel, 'Supervision', 'Approved', 2073.12, 'AED', '2026-04-11', '2026-10-05', '2026-04-05', 'QUO-2026-008', 'CON-2026-006', 'Bank Transfer', 'Monthly'),
(@p_marina_spa,   'Supervision', 'Approved', 1520.00, 'AED', '2026-06-01', '2027-02-01', '2026-04-08', 'QUO-2026-009', 'CON-2026-007', 'Bank Transfer', 'Monthly');

SET @fa_alreem_annex     = (SELECT id FROM financial_agreements WHERE project_id = @p_alreem_annex     AND stream = 'Design');
SET @fa_alreem_parking   = (SELECT id FROM financial_agreements WHERE project_id = @p_alreem_parking   AND stream = 'Design');
SET @fa_falcon_warehouse = (SELECT id FROM financial_agreements WHERE project_id = @p_falcon_warehouse AND stream = 'Design');
SET @fa_falcon_dock      = (SELECT id FROM financial_agreements WHERE project_id = @p_falcon_dock      AND stream = 'Design');
SET @fa_falcon_solar_sup = (SELECT id FROM financial_agreements WHERE project_id = @p_falcon_solar     AND stream = 'Supervision');
SET @fa_marina_hotel     = (SELECT id FROM financial_agreements WHERE project_id = @p_marina_hotel     AND stream = 'Design');
SET @fa_marina_hotel_sup = (SELECT id FROM financial_agreements WHERE project_id = @p_marina_hotel     AND stream = 'Supervision');
SET @fa_marina_spa       = (SELECT id FROM financial_agreements WHERE project_id = @p_marina_spa       AND stream = 'Design');
SET @fa_marina_spa_sup   = (SELECT id FROM financial_agreements WHERE project_id = @p_marina_spa       AND stream = 'Supervision');
SET @fa_marina_banquet   = (SELECT id FROM financial_agreements WHERE project_id = @p_marina_banquet   AND stream = 'Design');
SET @fa_marina_rooftop   = (SELECT id FROM financial_agreements WHERE project_id = @p_marina_rooftop   AND stream = 'Design');
SET @fa_ahmadi_plant     = (SELECT id FROM financial_agreements WHERE project_id = @p_ahmadi_plant     AND stream = 'Design');
SET @fa_ahmadi_admin     = (SELECT id FROM financial_agreements WHERE project_id = @p_ahmadi_admin     AND stream = 'Design');
SET @fa_desert           = (SELECT id FROM financial_agreements WHERE project_id = @p_desert           AND stream = 'Design');

INSERT INTO payment_obligations (agreement_id, sequence_number, description, amount_due, due_date, amount_received, date_paid, payment_method, reference_number) VALUES
(@fa_alreem_annex,     1, 'Instalment 1 - Design Kickoff',     110000.00, '2026-08-01', 0,         NULL,         NULL,             NULL),
(@fa_alreem_annex,     2, 'Instalment 2 - Final Delivery',     110000.00, '2026-12-15', 0,         NULL,         NULL,             NULL),
(@fa_alreem_parking,   1, 'Instalment 1 - Design Kickoff',      82500.00, '2026-07-01', 82500.00,  '2026-07-01', 'Bank Transfer', 'TRF-20260701-1'),
(@fa_alreem_parking,   2, 'Instalment 2 - Final Delivery',      82500.00, '2026-11-01', 0,         NULL,         NULL,             NULL),
(@fa_falcon_warehouse, 1, 'Instalment 1 - Design Kickoff',      82000.00, '2026-06-01', 82000.00,  '2026-06-01', 'Bank Transfer', 'TRF-20260601-1'),
(@fa_falcon_warehouse, 2, 'Instalment 2 - Design Development',  82000.00, '2026-08-01', 0,         NULL,         NULL,             NULL),
(@fa_falcon_warehouse, 3, 'Instalment 3 - Final Delivery',      82000.00, '2026-11-15', 0,         NULL,         NULL,             NULL),
(@fa_falcon_dock,      1, 'Instalment 1 - Design Kickoff',      65000.00, '2026-03-01', 65000.00,  '2026-03-01', 'Bank Transfer', 'TRF-20260301-1'),
(@fa_falcon_dock,      2, 'Instalment 2 - Final Delivery',      65000.00, '2026-08-01', 0,         NULL,         NULL,             NULL),
(@fa_marina_hotel,     1, 'Instalment 1 - Concept Design',     137333.33, '2026-04-01', 137333.33, '2026-04-02', 'Bank Transfer', 'TRF-20260402-1'),
(@fa_marina_hotel,     2, 'Instalment 2 - Detailed Design',    137333.33, '2026-07-01', 137333.33, '2026-07-03', 'Bank Transfer', 'TRF-20260703-1'),
(@fa_marina_hotel,     3, 'Instalment 3 - Site Supervision',   137333.34, '2026-10-01', 0,         NULL,         NULL,             NULL),
(@fa_marina_spa,       1, 'Instalment 1 - Concept Design',     125000.00, '2026-05-01', 125000.00, '2026-05-02', 'Bank Transfer', 'TRF-20260502-1'),
(@fa_marina_spa,       2, 'Instalment 2 - Final Delivery',     125000.00, '2026-12-01', 0,         NULL,         NULL,             NULL),
(@fa_marina_banquet,   1, 'Instalment 1 - Design Kickoff',      80000.00, '2026-02-01', 80000.00,  '2026-02-01', 'Bank Transfer', 'TRF-20260201-1'),
(@fa_marina_banquet,   2, 'Instalment 2 - Final Delivery',      80000.00, '2026-06-01', 80000.00,  '2026-06-01', 'Bank Transfer', 'TRF-20260601-2'),
(@fa_marina_rooftop,   1, 'Instalment 1 - Design Kickoff',      70000.00, '2025-12-15', 70000.00,  '2025-12-15', 'Bank Transfer', 'TRF-20251215-1'),
(@fa_marina_rooftop,   2, 'Instalment 2 - Final Delivery',      70000.00, '2026-04-01', 70000.00,  '2026-04-01', 'Bank Transfer', 'TRF-20260401-1'),
(@fa_ahmadi_plant,     1, 'Instalment 1 - Design Kickoff',      92500.00, '2026-03-01', 92500.00,  '2026-03-01', 'Bank Transfer', 'TRF-20260301-2'),
(@fa_ahmadi_plant,     2, 'Instalment 2 - Final Delivery',      92500.00, '2026-08-01', 0,         NULL,         NULL,             NULL),
(@fa_ahmadi_admin,     1, 'Instalment 1 - Design Kickoff',      34000.00, '2026-02-01', 0,         NULL,         NULL,             NULL),
(@fa_ahmadi_admin,     2, 'Instalment 2 - Final Delivery',      34000.00, '2026-06-15', 0,         NULL,         NULL,             NULL),
(@fa_desert,           1, 'Final Handover Payment',             98000.00, '2026-03-15', 98000.00,  '2026-03-10', 'Bank Transfer', 'TRF-20260310-1');

-- Supervision obligations -- flat monthly (Falcon Solar, Marina Spa) or
-- day-prorated (Marina Hotel, kept exactly as originally modelled).
INSERT INTO payment_obligations (agreement_id, sequence_number, description, amount_due, due_date, amount_received, date_paid, payment_method, reference_number) VALUES
(@fa_falcon_solar_sup, 1, 'Supervision - March 2026',     230.00, '2026-03-01', 230.00, '2026-03-03', 'Bank Transfer', 'TRF-20260303-1'),
(@fa_falcon_solar_sup, 2, 'Supervision - April 2026',     230.00, '2026-04-01', 230.00, '2026-04-02', 'Bank Transfer', 'TRF-20260402-2'),
(@fa_falcon_solar_sup, 3, 'Supervision - May 2026',       230.00, '2026-05-01', 230.00, '2026-05-02', 'Bank Transfer', 'TRF-20260502-2'),
(@fa_falcon_solar_sup, 4, 'Supervision - June 2026',      230.00, '2026-06-01', 0,      NULL,         NULL,             NULL),
(@fa_falcon_solar_sup, 5, 'Supervision - July 2026',      230.00, '2026-07-01', 0,      NULL,         NULL,             NULL),
(@fa_falcon_solar_sup, 6, 'Supervision - August 2026',    230.00, '2026-08-01', 0,      NULL,         NULL,             NULL),
(@fa_falcon_solar_sup, 7, 'Supervision - September 2026', 230.00, '2026-09-01', 0,      NULL,         NULL,             NULL);

-- One row per calendar month covered by the Marina Hotel Supervision
-- agreement, day-prorated exactly as generate_prorated_monthly_schedule
-- computes it: April = Weekly Site Visits (250 x 20/30 = 166.67, starts
-- the 11th) + Progress Reporting (100.00, full month) = 266.67; May-Sep
-- are full months for both (250 + 100 = 350.00); October is prorated
-- again for the 2026-10-05 end date (5 of 31 days: 250 x 5/31 = 40.32,
-- 100 x 5/31 = 16.13, total 56.45).
INSERT INTO payment_obligations (agreement_id, sequence_number, description, amount_due, due_date, amount_received, date_paid, payment_method, reference_number) VALUES
(@fa_marina_hotel_sup, 1, 'Supervision - April 2026',     266.67, '2026-04-01', 0, NULL, NULL, NULL),
(@fa_marina_hotel_sup, 2, 'Supervision - May 2026',       350.00, '2026-05-01', 0, NULL, NULL, NULL),
(@fa_marina_hotel_sup, 3, 'Supervision - June 2026',      350.00, '2026-06-01', 0, NULL, NULL, NULL),
(@fa_marina_hotel_sup, 4, 'Supervision - July 2026',      350.00, '2026-07-01', 0, NULL, NULL, NULL),
(@fa_marina_hotel_sup, 5, 'Supervision - August 2026',    350.00, '2026-08-01', 0, NULL, NULL, NULL),
(@fa_marina_hotel_sup, 6, 'Supervision - September 2026', 350.00, '2026-09-01', 0, NULL, NULL, NULL),
(@fa_marina_hotel_sup, 7, 'Supervision - October 2026',    56.45, '2026-10-01', 0, NULL, NULL, NULL);

INSERT INTO payment_obligations (agreement_id, sequence_number, description, amount_due, due_date, amount_received, date_paid, payment_method, reference_number) VALUES
(@fa_marina_spa_sup, 1, 'Supervision - June 2026',      190.00, '2026-06-01', 190.00, '2026-06-02', 'Bank Transfer', 'TRF-20260602-1'),
(@fa_marina_spa_sup, 2, 'Supervision - July 2026',      190.00, '2026-07-01', 190.00, '2026-07-02', 'Bank Transfer', 'TRF-20260702-1'),
(@fa_marina_spa_sup, 3, 'Supervision - August 2026',    190.00, '2026-08-01', 0,      NULL,         NULL,             NULL),
(@fa_marina_spa_sup, 4, 'Supervision - September 2026', 190.00, '2026-09-01', 0,      NULL,         NULL,             NULL),
(@fa_marina_spa_sup, 5, 'Supervision - October 2026',   190.00, '2026-10-01', 0,      NULL,         NULL,             NULL),
(@fa_marina_spa_sup, 6, 'Supervision - November 2026',  190.00, '2026-11-01', 0,      NULL,         NULL,             NULL),
(@fa_marina_spa_sup, 7, 'Supervision - December 2026',  190.00, '2026-12-01', 0,      NULL,         NULL,             NULL),
(@fa_marina_spa_sup, 8, 'Supervision - January 2027',   190.00, '2027-01-01', 0,      NULL,         NULL,             NULL);

INSERT INTO payments (agreement_id, project_id, amount_received, payment_date, payment_mode, reference_number, payer, receiving_account, created_by, created_at) VALUES
(@fa_alreem_parking,   @p_alreem_parking,    82500.00,  '2026-07-01', 'Bank Transfer', 'TRF-20260701-1', 'Al Reem Development LLC',       'Al Mailam Operating Account', @u_pm, '2026-07-01 10:00:00'),
(@fa_falcon_warehouse, @p_falcon_warehouse,  82000.00,  '2026-06-01', 'Bank Transfer', 'TRF-20260601-1', 'Falcon Heights Logistics',      'Al Mailam Operating Account', @u_pm, '2026-06-01 10:00:00'),
(@fa_falcon_dock,      @p_falcon_dock,       65000.00,  '2026-03-01', 'Bank Transfer', 'TRF-20260301-1', 'Falcon Heights Logistics',      'Al Mailam Operating Account', @u_pm, '2026-03-01 10:00:00'),
(@fa_falcon_solar_sup, @p_falcon_solar,      230.00,    '2026-03-03', 'Bank Transfer', 'TRF-20260303-1', 'Falcon Heights Logistics',      'Al Mailam Operating Account', @u_pm, '2026-03-03 09:15:00'),
(@fa_falcon_solar_sup, @p_falcon_solar,      230.00,    '2026-04-02', 'Bank Transfer', 'TRF-20260402-2', 'Falcon Heights Logistics',      'Al Mailam Operating Account', @u_pm, '2026-04-02 09:15:00'),
(@fa_falcon_solar_sup, @p_falcon_solar,      230.00,    '2026-05-02', 'Bank Transfer', 'TRF-20260502-2', 'Falcon Heights Logistics',      'Al Mailam Operating Account', @u_pm, '2026-05-02 09:15:00'),
(@fa_marina_hotel,     @p_marina_hotel,     137333.33,  '2026-04-02', 'Bank Transfer', 'TRF-20260402-1', 'Marina Bay Hospitality Group',  'Al Mailam Operating Account', @u_pm, '2026-04-02 09:30:00'),
(@fa_marina_hotel,     @p_marina_hotel,     137333.33,  '2026-07-03', 'Bank Transfer', 'TRF-20260703-1', 'Marina Bay Hospitality Group',  'Al Mailam Operating Account', @u_pm, '2026-07-03 09:45:00'),
(@fa_marina_spa,       @p_marina_spa,       125000.00,  '2026-05-02', 'Bank Transfer', 'TRF-20260502-1', 'Marina Bay Hospitality Group',  'Al Mailam Operating Account', @u_pm, '2026-05-02 09:30:00'),
(@fa_marina_spa_sup,   @p_marina_spa,       190.00,     '2026-06-02', 'Bank Transfer', 'TRF-20260602-1', 'Marina Bay Hospitality Group',  'Al Mailam Operating Account', @u_pm, '2026-06-02 09:15:00'),
(@fa_marina_spa_sup,   @p_marina_spa,       190.00,     '2026-07-02', 'Bank Transfer', 'TRF-20260702-1', 'Marina Bay Hospitality Group',  'Al Mailam Operating Account', @u_pm, '2026-07-02 09:15:00'),
(@fa_marina_banquet,   @p_marina_banquet,    80000.00,  '2026-02-01', 'Bank Transfer', 'TRF-20260201-1', 'Marina Bay Hospitality Group',  'Al Mailam Operating Account', @u_pm, '2026-02-01 09:30:00'),
(@fa_marina_banquet,   @p_marina_banquet,    80000.00,  '2026-06-01', 'Bank Transfer', 'TRF-20260601-2', 'Marina Bay Hospitality Group',  'Al Mailam Operating Account', @u_pm, '2026-06-01 09:30:00'),
(@fa_marina_rooftop,   @p_marina_rooftop,    70000.00,  '2025-12-15', 'Bank Transfer', 'TRF-20251215-1', 'Marina Bay Hospitality Group',  'Al Mailam Operating Account', @u_pm, '2025-12-15 09:30:00'),
(@fa_marina_rooftop,   @p_marina_rooftop,    70000.00,  '2026-04-01', 'Bank Transfer', 'TRF-20260401-1', 'Marina Bay Hospitality Group',  'Al Mailam Operating Account', @u_pm, '2026-04-01 09:30:00'),
(@fa_ahmadi_plant,     @p_ahmadi_plant,      92500.00,  '2026-03-01', 'Bank Transfer', 'TRF-20260301-2', 'Ahmadi Industrial Holdings',    'Al Mailam Operating Account', @u_pm, '2026-03-01 10:00:00'),
(@fa_desert,           @p_desert,            98000.00,  '2026-03-10', 'Bank Transfer', 'TRF-20260310-1', 'Khalid Al Mansoori',            'Al Mailam Operating Account', @u_pm, '2026-03-10 14:20:00');

INSERT INTO payment_allocations (payment_id, obligation_id, amount_allocated) VALUES
((SELECT id FROM payments WHERE reference_number = 'TRF-20260701-1'), (SELECT id FROM payment_obligations WHERE agreement_id = @fa_alreem_parking   AND sequence_number = 1), 82500.00),
((SELECT id FROM payments WHERE reference_number = 'TRF-20260601-1'), (SELECT id FROM payment_obligations WHERE agreement_id = @fa_falcon_warehouse AND sequence_number = 1), 82000.00),
((SELECT id FROM payments WHERE reference_number = 'TRF-20260301-1'), (SELECT id FROM payment_obligations WHERE agreement_id = @fa_falcon_dock      AND sequence_number = 1), 65000.00),
((SELECT id FROM payments WHERE reference_number = 'TRF-20260303-1'), (SELECT id FROM payment_obligations WHERE agreement_id = @fa_falcon_solar_sup AND sequence_number = 1), 230.00),
((SELECT id FROM payments WHERE reference_number = 'TRF-20260402-2'), (SELECT id FROM payment_obligations WHERE agreement_id = @fa_falcon_solar_sup AND sequence_number = 2), 230.00),
((SELECT id FROM payments WHERE reference_number = 'TRF-20260502-2'), (SELECT id FROM payment_obligations WHERE agreement_id = @fa_falcon_solar_sup AND sequence_number = 3), 230.00),
((SELECT id FROM payments WHERE reference_number = 'TRF-20260402-1'), (SELECT id FROM payment_obligations WHERE agreement_id = @fa_marina_hotel     AND sequence_number = 1), 137333.33),
((SELECT id FROM payments WHERE reference_number = 'TRF-20260703-1'), (SELECT id FROM payment_obligations WHERE agreement_id = @fa_marina_hotel     AND sequence_number = 2), 137333.33),
((SELECT id FROM payments WHERE reference_number = 'TRF-20260502-1'), (SELECT id FROM payment_obligations WHERE agreement_id = @fa_marina_spa       AND sequence_number = 1), 125000.00),
((SELECT id FROM payments WHERE reference_number = 'TRF-20260602-1'), (SELECT id FROM payment_obligations WHERE agreement_id = @fa_marina_spa_sup   AND sequence_number = 1), 190.00),
((SELECT id FROM payments WHERE reference_number = 'TRF-20260702-1'), (SELECT id FROM payment_obligations WHERE agreement_id = @fa_marina_spa_sup   AND sequence_number = 2), 190.00),
((SELECT id FROM payments WHERE reference_number = 'TRF-20260201-1'), (SELECT id FROM payment_obligations WHERE agreement_id = @fa_marina_banquet   AND sequence_number = 1), 80000.00),
((SELECT id FROM payments WHERE reference_number = 'TRF-20260601-2'), (SELECT id FROM payment_obligations WHERE agreement_id = @fa_marina_banquet   AND sequence_number = 2), 80000.00),
((SELECT id FROM payments WHERE reference_number = 'TRF-20251215-1'), (SELECT id FROM payment_obligations WHERE agreement_id = @fa_marina_rooftop   AND sequence_number = 1), 70000.00),
((SELECT id FROM payments WHERE reference_number = 'TRF-20260401-1'), (SELECT id FROM payment_obligations WHERE agreement_id = @fa_marina_rooftop   AND sequence_number = 2), 70000.00),
((SELECT id FROM payments WHERE reference_number = 'TRF-20260301-2'), (SELECT id FROM payment_obligations WHERE agreement_id = @fa_ahmadi_plant     AND sequence_number = 1), 92500.00),
((SELECT id FROM payments WHERE reference_number = 'TRF-20260310-1'), (SELECT id FROM payment_obligations WHERE agreement_id = @fa_desert           AND sequence_number = 1), 98000.00);

-- ----------------------------------------------------------------------------
-- Project documents (+ one version history example)
-- ----------------------------------------------------------------------------
-- storage_key values are placeholders -- there is no matching file on disk
-- for seed data, so these rows are for listing/metadata purposes only; do
-- not expect a real download to succeed for a seeded document.
INSERT INTO project_documents (document_no, project_id, title, type, revision, uploaded_by, upload_date, status, storage_key, original_filename, file_size_bytes) VALUES
('DOC-2026-001', @p_alreem_tower,     'Al Reem Tower Site Survey',              'Report',            'Rev A', @u_layla, '2026-08-05', 'Approved',     'seed/doc-001', 'al-reem-site-survey.pdf',        1258000),
('DOC-2026-002', @p_falcon_warehouse, 'Falcon Heights MEP Concept Drawing',     'Drawing',           'Rev B', @u_ahmed, '2026-05-22', 'Approved',     'seed/doc-002', 'falcon-mep-concept-revB.pdf',    3421000),
('DOC-2026-003', @p_falcon_warehouse, 'Falcon Heights Load Calculation Sheet',  'Calculation Sheet', 'Rev A', @u_ahmed, '2026-06-01', 'Under Review', 'seed/doc-003', 'falcon-load-calcs.xlsx',          842000),
('DOC-2026-004', @p_marina_hotel,     'Marina Bay Hotel Renovation Drawings',   'Drawing',           'Rev C', @u_layla, '2026-07-15', 'Approved',     'seed/doc-004', 'marina-bay-renovation-revC.pdf', 5210000),
('DOC-2026-005', @p_marina_hotel,     'Marina Bay Interior Fit-out Report',     'Report',            'Rev A', @u_layla, '2026-07-20', 'Draft',        'seed/doc-005', 'marina-bay-interior-report.pdf',  987000),
('DOC-2026-006', @p_ahmadi_fire,      'Ahmadi Facility Fire System Drawings',   'Drawing',           'Rev A', @u_ahmed, '2026-06-12', 'Approved',     'seed/doc-006', 'ahmadi-fire-system.pdf',        2870000),
('DOC-2026-007', @p_ahmadi_fire,      'Ahmadi Facility Submission Form',        'Municipality Form', 'Rev A', @u_fatima,'2026-06-14', 'Approved',     'seed/doc-007', 'ahmadi-kfsd-204-form.pdf',        410000),
('DOC-2026-008', @p_desert,           'Desert Rose Plaza Handover Certificate', 'Report',            'Rev A', @u_ahmed, '2026-03-18', 'Approved',     'seed/doc-008', 'desert-rose-handover.pdf',        650000),
('DOC-2026-009', @p_marina_banquet,   'Banquet Hall Renovation Drawings',       'Drawing',           'Rev A', @u_layla, '2026-06-15', 'Approved',     'seed/doc-009', 'banquet-hall-drawings.pdf',      1980000),
('DOC-2026-010', @p_marina_rooftop,   'Rooftop Lounge Building Permit Copy',    'Municipality Form', 'Rev A', @u_fatima,'2026-05-02', 'Approved',     'seed/doc-010', 'rooftop-lounge-permit.pdf',       310000);

SET @doc_falcon_mep = (SELECT id FROM project_documents WHERE document_no = 'DOC-2026-002');

INSERT INTO document_versions (document_id, revision, uploaded_by, upload_date, notes, storage_key, original_filename, file_size_bytes) VALUES
(@doc_falcon_mep, 'Rev A', @u_ahmed, '2026-05-15', 'Initial concept drawing.',          'seed/doc-002-revA', 'falcon-mep-concept-revA.pdf', 3180000),
(@doc_falcon_mep, 'Rev B', @u_ahmed, '2026-05-22', 'Revised after client walkthrough.', 'seed/doc-002-revB', 'falcon-mep-concept-revB.pdf', 3421000);

-- ----------------------------------------------------------------------------
-- Tasks
-- ----------------------------------------------------------------------------
-- Al Reem Residential Tower -- general (unlinked) tasks at Requirement.
INSERT INTO tasks (task_no, project_id, title, assigned_to, priority, severity, due_date, due_time, status) VALUES
('TSK-2026-001', @p_alreem_tower, 'Complete structural site survey report',    @u_layla, 'High',   'Major', '2026-08-25', '17:00:00', 'Completed'),
('TSK-2026-002', @p_alreem_tower, 'Draft preliminary structural calculations', @u_layla, 'Medium', 'Minor', '2026-09-20', '17:00:00', 'In Progress');

-- Falcon Heights Warehouse Expansion -- auto-style service tasks, one per
-- selected Design activity, mirroring each activity's own status.
INSERT INTO tasks (task_no, project_id, title, assigned_to, priority, severity, start_date, due_date, due_time, status, selected_activity_id) VALUES
('TSK-2026-003', @p_falcon_warehouse, 'MEP Concept Design',        @u_ahmed, 'High',   'Major', '2026-05-14', '2026-06-01', '17:00:00', 'Completed',    @act_falcon_wh_concept),
('TSK-2026-004', @p_falcon_warehouse, 'MEP Detailed Design',       @u_ahmed, 'Medium', 'Major', '2026-05-14', '2026-08-15', '17:00:00', 'In Progress',  @act_falcon_wh_detail),
('TSK-2026-005', @p_falcon_warehouse, 'MEP Coordination Drawings', @u_ahmed, 'Medium', 'Minor', '2026-05-14', '2026-11-15', '17:00:00', 'Preset',       @act_falcon_wh_coord);

-- Falcon Heights Cold Storage Unit -- one per selected Permit.
INSERT INTO tasks (task_no, project_id, title, assigned_to, priority, severity, start_date, due_date, due_time, status, selected_permit_id) VALUES
('TSK-2026-006', @p_falcon_coldstore, 'Cold Storage Building Permit',    @u_ahmed, 'High',   'Major', '2026-04-01', '2026-08-01', '17:00:00', 'In Progress', @perm_falcon_cs_building),
('TSK-2026-007', @p_falcon_coldstore, 'Cold Storage Fire Safety Permit', @u_ahmed, 'Medium', 'Major', '2026-04-01', '2026-09-01', '17:00:00', 'Preset',      @perm_falcon_cs_fire);

-- Falcon Heights Rooftop Solar Retrofit -- one per selected Supervision
-- activity.
INSERT INTO tasks (task_no, project_id, title, assigned_to, priority, severity, start_date, due_date, due_time, status, selected_supervision_activity_id) VALUES
('TSK-2026-008', @p_falcon_solar, 'Weekly Site Visits', @u_ahmed, 'Medium', 'Minor', '2026-03-01', '2026-09-30', '17:00:00', 'In Progress', @sup_falcon_solar_visits),
('TSK-2026-009', @p_falcon_solar, 'Progress Reporting',  @u_ahmed, 'Low',    'Minor', '2026-03-01', '2026-09-30', '17:00:00', 'Preset',      @sup_falcon_solar_reports);

-- Falcon Heights Loading Dock Upgrade -- one per still-open selected item
-- (the Cancelled Electrical Layout activity never gets one, same as the
-- app's own _create_service_tasks skips Complete/Cancelled items).
INSERT INTO tasks (task_no, project_id, title, assigned_to, priority, severity, start_date, due_date, due_time, status, selected_activity_id) VALUES
('TSK-2026-010', @p_falcon_dock, 'Loading Dock MEP Design', @u_ahmed, 'Medium', 'Major', '2026-02-15', '2026-07-01', '17:00:00', 'In Progress', @act_falcon_dock_mep);
INSERT INTO tasks (task_no, project_id, title, assigned_to, priority, severity, start_date, due_date, due_time, status, selected_permit_id) VALUES
('TSK-2026-011', @p_falcon_dock, 'Loading Dock Access Permit', @u_ahmed, 'Medium', 'Major', '2026-02-15', '2026-08-15', '17:00:00', 'Preset', @perm_falcon_dock_access);

-- Marina Bay Hotel Renovation -- one manual task plus one per selected
-- Design/Supervision item.
INSERT INTO tasks (task_no, project_id, title, assigned_to, priority, severity, due_date, due_time, status) VALUES
('TSK-2026-012', @p_marina_hotel, 'Coordinate interior fit-out with client', @u_layla, 'High', 'Minor', '2026-07-25', '15:00:00', 'Pending');
INSERT INTO tasks (task_no, project_id, title, assigned_to, priority, severity, start_date, due_date, due_time, status, selected_activity_id) VALUES
('TSK-2026-013', @p_marina_hotel, 'Architectural Concept Design',    @u_layla, 'High',   'Major', '2026-03-10', '2026-05-01', '17:00:00', 'Completed',   @act_marina_hotel_concept),
('TSK-2026-014', @p_marina_hotel, 'Detailed Architectural Drawings', @u_layla, 'Medium', 'Major', '2026-03-10', '2026-09-01', '17:00:00', 'In Progress', @act_marina_hotel_detail);
INSERT INTO tasks (task_no, project_id, title, assigned_to, priority, severity, start_date, due_date, due_time, status, selected_supervision_activity_id) VALUES
('TSK-2026-015', @p_marina_hotel, 'Weekly Site Visits (Supervision)', @u_layla, 'Medium', 'Minor', '2026-04-11', '2026-10-05', '17:00:00', 'In Progress', @sup_marina_hotel_visits),
('TSK-2026-016', @p_marina_hotel, 'Progress Reporting (Supervision)', @u_layla, 'Low',    'Minor', '2026-04-01', '2026-10-05', '17:00:00', 'In Progress', @sup_marina_hotel_reports);

-- Marina Bay Spa Wing Extension -- one per selected item across all three
-- tracks.
INSERT INTO tasks (task_no, project_id, title, assigned_to, priority, severity, start_date, due_date, due_time, status, selected_activity_id) VALUES
('TSK-2026-017', @p_marina_spa, 'Spa Wing Concept Design',  @u_layla, 'High',   'Major', '2026-04-01', '2026-05-15', '17:00:00', 'Completed',   @act_marina_spa_concept),
('TSK-2026-018', @p_marina_spa, 'Spa Wing Detailed Design', @u_layla, 'Medium', 'Major', '2026-04-01', '2026-10-01', '17:00:00', 'In Progress', @act_marina_spa_detail);
INSERT INTO tasks (task_no, project_id, title, assigned_to, priority, severity, start_date, due_date, due_time, status, selected_permit_id) VALUES
('TSK-2026-019', @p_marina_spa, 'Spa Wing Building Permit', @u_layla, 'Medium', 'Major', '2026-04-01', '2026-11-01', '17:00:00', 'Preset', @perm_marina_spa_building);
INSERT INTO tasks (task_no, project_id, title, assigned_to, priority, severity, start_date, due_date, due_time, status, selected_supervision_activity_id) VALUES
('TSK-2026-020', @p_marina_spa, 'Weekly Site Visits - Spa Wing',  @u_layla, 'Medium', 'Minor', '2026-06-01', '2027-02-01', '17:00:00', 'In Progress', @sup_marina_spa_visits),
('TSK-2026-021', @p_marina_spa, 'Progress Reporting - Spa Wing',  @u_layla, 'Low',    'Minor', '2026-06-01', '2027-02-01', '17:00:00', 'Preset',      @sup_marina_spa_reports);

-- Marina Bay Banquet Hall Refurb / Rooftop Lounge -- Handover-stage
-- projects, every task already Completed (required exit criterion).
INSERT INTO tasks (task_no, project_id, title, assigned_to, priority, severity, start_date, due_date, due_time, status, selected_activity_id) VALUES
('TSK-2026-022', @p_marina_banquet, 'Banquet Hall Renovation Design', @u_layla, 'High', 'Major', '2026-01-15', '2026-06-20', '17:00:00', 'Completed', @act_marina_banquet),
('TSK-2026-023', @p_marina_rooftop, 'Rooftop Lounge Design',          @u_layla, 'High', 'Major', '2025-12-01', '2026-04-10', '17:00:00', 'Completed', @act_marina_rooftop);
INSERT INTO tasks (task_no, project_id, title, assigned_to, priority, severity, start_date, due_date, due_time, status, selected_permit_id) VALUES
('TSK-2026-024', @p_marina_rooftop, 'Rooftop Lounge Building Permit', @u_layla, 'High', 'Major', '2025-12-01', '2026-05-01', '17:00:00', 'Completed', @perm_marina_rooftop);

-- Ahmadi Industrial Facility -- one manual prep task plus one linked to
-- the selected Permit.
INSERT INTO tasks (task_no, project_id, title, assigned_to, priority, severity, due_date, due_time, status) VALUES
('TSK-2026-025', @p_ahmadi_fire, 'Prepare fire safety submission package', @u_ahmed, 'High', 'Critical', '2026-06-14', '12:00:00', 'Completed');
INSERT INTO tasks (task_no, project_id, title, assigned_to, priority, severity, start_date, due_date, due_time, status, selected_permit_id) VALUES
('TSK-2026-026', @p_ahmadi_fire, 'Fire Suppression System Permit', @u_ahmed, 'Medium', 'Major', '2026-01-20', '2026-08-01', '17:00:00', 'In Progress', @perm_ahmadi_fire);

-- Ahmadi Warehouse Fire Suppression Retrofit -- deliberately zero tasks
-- (part of the zero-track auto-advance demo, see header comment).

-- Ahmadi Plant Expansion -- On Hold, one per selected Design activity.
INSERT INTO tasks (task_no, project_id, title, assigned_to, priority, severity, start_date, due_date, due_time, status, selected_activity_id) VALUES
('TSK-2026-027', @p_ahmadi_plant, 'Plant Layout Design',         @u_ahmed, 'High',   'Major', '2026-02-01', '2026-05-01', '17:00:00', 'Completed',   @act_ahmadi_plant_layout),
('TSK-2026-028', @p_ahmadi_plant, 'Plant Safety Systems Design', @u_ahmed, 'Medium', 'Major', '2026-02-01', '2026-09-01', '17:00:00', 'In Progress', @act_ahmadi_plant_safety);

-- Ahmadi Admin Building Refurbishment -- deliberately overdue: due_date is
-- before today (2026-09-10) and the task is still open.
INSERT INTO tasks (task_no, project_id, title, assigned_to, priority, severity, start_date, due_date, due_time, status, selected_activity_id) VALUES
('TSK-2026-029', @p_ahmadi_admin, 'Admin Building Fire Exit Design', @u_ahmed, 'High', 'Major', '2026-01-05', '2026-08-15', '17:00:00', 'Pending', @act_ahmadi_admin_exit);

-- Desert Rose Retail Plaza -- Completed, its one task Completed and
-- linked to the closed Design activity.
INSERT INTO tasks (task_no, project_id, title, assigned_to, priority, severity, start_date, due_date, due_time, status, selected_activity_id) VALUES
('TSK-2026-030', @p_desert, 'Archive final handover documentation', @u_fatima, 'Low', 'Minor', '2025-09-01', '2026-03-19', '17:00:00', 'Completed', @act_desert_handover);

-- ----------------------------------------------------------------------------
-- Handover checklist items
-- ----------------------------------------------------------------------------
-- Mirrors project_service._generate_handover_checklist's own shape: one
-- row per Complete Design/Permit/Supervision item on a project that has
-- reached (or, for Desert Rose, finished) Handover.
INSERT INTO handover_checklist_items (project_id, source_type, source_id, title, completed_at) VALUES
(@p_marina_banquet, 'Design',  @act_marina_banquet, 'Banquet Hall Renovation Design', '2026-06-20 15:00:00'),
(@p_marina_rooftop, 'Design',  @act_marina_rooftop, 'Rooftop Lounge Design',          '2026-04-10 15:00:00'),
(@p_marina_rooftop, 'Permit',  @perm_marina_rooftop,'Rooftop Lounge Building Permit', '2026-05-01 12:00:00'),
(@p_desert,         'Design',  @act_desert_handover,'Final Civil Handover Package',   '2026-03-15 14:00:00');

-- ----------------------------------------------------------------------------
-- Notifications
-- ----------------------------------------------------------------------------
INSERT INTO notifications (notification_no, user_id, title, message, category, created_at, `read`, link_route_name, link_params) VALUES
('NTF-2026-001', @u_ahmed, 'New task assigned',            'You have been assigned "Fire Suppression System Permit" on Ahmadi Industrial Facility.', 'Task', '2026-01-20 09:00:00', 1, 'project-workspace', JSON_OBJECT('projectId', '2600013')),
('NTF-2026-002', @u_pm,    'Payment received',             'AED 82,000 received for Falcon Heights Warehouse Expansion (Instalment 1).', 'Project', '2026-06-01 10:05:00', 1, 'project-workspace', JSON_OBJECT('projectId', '2600005')),
('NTF-2026-003', @u_pm,    'Government submission update', 'Fire Safety Approval for Ahmadi Industrial Facility is now Under Review.', 'Government', '2026-06-15 11:30:00', 0, 'government-submissions', NULL),
('NTF-2026-004', @u_admin, 'New client onboarded',         'Ahmadi Industrial Holdings has completed onboarding and is pending verification.', 'Project', '2026-03-01 10:05:00', 0, 'client-workspace', JSON_OBJECT('clientId', 'CLT-004')),
('NTF-2026-005', @u_layla, 'Task due soon',                'Draft preliminary structural calculations is due on 2026-09-20.', 'Task', '2026-09-08 08:00:00', 0, 'tasks', NULL),
('NTF-2026-006', @u_admin, 'Project ready for hand-over',   'Marina Bay Banquet Hall Refurb has every planned item closed and is awaiting payment confirmation.', 'Project', '2026-08-01 09:00:00', 0, 'project-workspace', JSON_OBJECT('projectId', '2600011')),
('NTF-2026-007', @u_admin, 'Project ready for hand-over',   'Marina Bay Rooftop Lounge has every planned item closed and payment confirmed -- collect the signed acknowledgment.', 'Project', '2026-05-10 09:00:00', 0, 'project-workspace', JSON_OBJECT('projectId', '2600012')),
('NTF-2026-008', @u_ahmed, 'Task overdue',                  'Admin Building Fire Exit Design was due on 2026-08-15 and is still open.', 'Task', '2026-08-16 08:00:00', 0, 'tasks', NULL);

-- ----------------------------------------------------------------------------
-- Message templates and log
-- ----------------------------------------------------------------------------
INSERT INTO message_templates (name, channel, body) VALUES
('Project Kickoff Notice', 'Email', 'Dear {{contact_name}}, we are pleased to confirm the kickoff of {{project_name}}. Our team will be in touch shortly with next steps.'),
('Payment Reminder',       'Email', 'Dear {{contact_name}}, this is a reminder that a payment of {{amount}} for {{project_name}} is due on {{due_date}}.');

SET @tmpl_kickoff  = (SELECT id FROM message_templates WHERE name = 'Project Kickoff Notice');
SET @tmpl_reminder = (SELECT id FROM message_templates WHERE name = 'Payment Reminder');

INSERT INTO message_log (client_id, channel, template_id, body, project_id, status, sent_at) VALUES
(@c_falcon, 'Email', @tmpl_kickoff,  'Dear Yousef Al Amiri, we are pleased to confirm the kickoff of Falcon Heights Warehouse Expansion. Our team will be in touch shortly with next steps.', @p_falcon_warehouse, 'Sent', '2026-05-14 09:00:00'),
(@c_marina, 'Email', @tmpl_reminder, 'Dear Noura Al Sabah, this is a reminder that a payment of AED 137,333.34 for Marina Bay Hotel Renovation is due on 2026-10-01.', @p_marina_hotel, 'Sent', '2026-09-01 09:00:00');

-- ----------------------------------------------------------------------------
-- Project timeline events
-- ----------------------------------------------------------------------------
INSERT INTO project_timeline_events (project_id, type, title, description, event_date, status, created_by) VALUES
(@p_marina_hotel,   'stage',      'Design stage started',            'Project moved into the Design stage after contract signature.',              '2026-03-25', 'completed', @u_pm),
(@p_marina_hotel,   'milestone',  'Concept design approved',         'Client approved the architectural concept design.',                           '2026-05-01', 'completed', @u_pm),
(@p_marina_hotel,   'note',       'Interior fit-out scope added',    'Client requested interior fit-out design be added to scope.',                 '2026-07-10', 'completed', @u_layla),
(@p_marina_banquet, 'milestone',  'Design complete, ready for hand-over', 'Banquet hall renovation design closed out; hand-over notice sent to staff.', '2026-08-01', 'completed', @u_pm),
(@p_marina_rooftop, 'milestone',  'Payment confirmed',               'Full payment confirmed; awaiting client signed hand-over acknowledgment.',     '2026-05-15', 'completed', @u_admin),
(@p_desert,         'stage',      'Project completed',               'Final handover documentation delivered and accepted.',                        '2026-03-20', 'completed', @u_ahmed),
(@p_ahmadi_fire,    'submission', 'Fire safety approval submitted',  'Submitted KFSD-204 Fire Safety Approval to Kuwait Fire Service Directorate.', '2026-06-15', 'completed', @u_ahmed);

-- ----------------------------------------------------------------------------
-- Number series continuation
-- ----------------------------------------------------------------------------
-- So the next real project/document/task/quotation/contract/submission/
-- notification created through the app continues after the seeded ones
-- instead of colliding with them.
INSERT INTO number_series (doc_type, year, prefix, next_number, padding) VALUES
('PROJECT',              2026, 'PRJ', 21, 5),
('DOCUMENT',              2026, 'DOC', 11, 3),
('TASK',                 2026, 'TSK', 31, 3),
('QUOTATION',             2026, 'QUO', 18, 3),
('CONTRACT',              2026, 'CON', 15, 3),
('GOVERNMENT_SUBMISSION', 2026, 'SUB', 5, 3),
('NOTIFICATION',          2026, 'NTF', 9, 3)
ON DUPLICATE KEY UPDATE next_number = VALUES(next_number);

SET FOREIGN_KEY_CHECKS = 1;
