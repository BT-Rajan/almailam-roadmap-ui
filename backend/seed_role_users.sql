-- ============================================================================
-- ServiceOS -- Five Role Users
-- ============================================================================
-- One user per internal app role (see app/core/permissions.py ROLES),
-- for exercising the role/permission matrix end to end. "Customer" is
-- deliberately excluded -- it's an external-only role scoped to a
-- specific client_id (see app/services/customer_portal_service.py) and
-- has no access to the internal app these five roles cover.
--
-- Usage (against a database schema.sql has already been applied to):
--   mysql -u <user> -p <database> < seed_role_users.sql
--
-- All five share the password: Demo#2026
-- (the hash below is a genuine bcrypt hash of that password, generated
-- with this repo's own app.core.security.hash_password -- same hash
-- already used in testdata.sql, not a placeholder)
--
-- Usernames/emails here are distinct from testdata.sql's, so this file
-- can be loaded on its own or alongside testdata.sql without a unique-
-- constraint collision.
-- ============================================================================

INSERT INTO users (username, email, password_hash, full_name, designation, mobile, role, is_active) VALUES
('r.admin',   'r.admin@almailam.example',   '$2b$12$A.fpsSUrwUczc6W6XeOmO.k06k0Km2GJ9zMkGnFQFBYdic4PGLa0O', 'Rana Admin',        'System Administrator', '+971502000001', 'Administrator',      1),
('r.manager', 'r.manager@almailam.example', '$2b$12$A.fpsSUrwUczc6W6XeOmO.k06k0Km2GJ9zMkGnFQFBYdic4PGLa0O', 'Rami Manager',      'Project Manager',      '+971502000002', 'Project Manager',    1),
('r.engineer','r.engineer@almailam.example','$2b$12$A.fpsSUrwUczc6W6XeOmO.k06k0Km2GJ9zMkGnFQFBYdic4PGLa0O', 'Reem Engineer',     'Structural Engineer',  '+971502000003', 'Engineer',           1),
('r.docs',    'r.docs@almailam.example',    '$2b$12$A.fpsSUrwUczc6W6XeOmO.k06k0Km2GJ9zMkGnFQFBYdic4PGLa0O', 'Rasha Documents',   'Document Controller',  '+971502000004', 'Document Controller',1),
('r.viewer',  'r.viewer@almailam.example',  '$2b$12$A.fpsSUrwUczc6W6XeOmO.k06k0Km2GJ9zMkGnFQFBYdic4PGLa0O', 'Rayan Viewer',      'Stakeholder',          '+971502000005', 'Viewer',             1);
