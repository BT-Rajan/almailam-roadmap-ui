PASS B01
Backend Foundation
FastAPI project scaffold, SQLAlchemy models, migrations, config/env, CORS, error-handling middleware, request/response envelope shape. Mirrors backend/app/core structure from jdk_clean (config.py, database.py, exceptions.py, validators.py). Establishes the {"error": "message"} response contract that the frontend's future apiError.ts helper will read directly.

PASS B02
Auth & Sessions
JWT access/refresh tokens, bcrypt password hashing, refresh-token rotation and revocation, account lockout after repeated failures. Ported from jdk_clean's auth_service.py + core/security.py. Replaces the current authStore.ts localStorage boolean flag with real session state.

PASS B03
RBAC & Permissions
Role and department write guards (canWrite, canWriteDepartment, isAdmin equivalents) as reusable dependency checks, mirroring jdk_clean's lib/roles.ts / api/deps.py:require_department_write. Backs PermissionMatrix.vue, RoleCard.vue and roleDefinitions.ts with real enforcement instead of mock data.

PASS B04
Shared Workflow Engine
One assert_transition_allowed + assert_reason_given implementation (ported from jdk_clean's core/workflow.py), with a per-entity ALLOWED_TRANSITIONS table for government submissions, quotations, contracts, tasks and payment obligations. The frontend's statusTransitions.ts equivalents are generated to mirror these tables exactly, same pairing jdk_clean uses.

PASS B05
Number Series Service
Atomic sequential document numbering (SELECT ... FOR UPDATE claim pattern) for quotation numbers, contract numbers, government submission references and payment receipt numbers. Direct port of number_series_service.py.

PASS B06
Audit Trail Service
Generic log_create / log_update / log_delete / log_restore + get_history, one implementation shared by every module rather than one per entity. Powers ClientAuditTrail.vue and the financialAuditEvents feed with real history instead of static mock arrays.

PASS B07
Client & Project APIs
CRUD for clients, contacts, addresses, identification, consent, and projects. Response shapes matched field-for-field to the existing mock/clients.ts and mock/projects.ts so clientStore.ts and projectStore.ts need a service-layer swap only, no page changes.

PASS B08
Government Forms & Submissions API
Forms catalogue, authority grouping, submission workflow wired to the Pass B04 workflow engine, plus the admin-review escalation pattern from jdk_clean's feasibility_service.py (override-with-reason, SLA-based flag) for SubmissionApprovalStepper.vue.

PASS B09
Quotation & Contract API
Line items, pricing, versioning, and PDF generation via one shared _render_document() renderer with thin per-document adapters (ported from pdf_generator.py) serving both the Quotation printable layout and the Contract preview.

PASS B10
Payments API
Obligations, allocations, refunds, and payment status transitions on the Pass B04 engine. Backs PaymentSummaryCards.vue, PaymentTimeline.vue and paymentStore.ts.

PASS B11
Document Repository & AI Review API
Upload, storage, versioning, metadata, and hooks for the AI review pipeline (summary, extracted fields, confidence score) that AIReviewPanel.vue and OCRResultPanel.vue currently mock.

PASS B12
Task Management API
Task board/list CRUD, assignment, priority and severity, status transitions on the Pass B04 engine.

PASS B13
Notifications Service
Computed-fresh (not stored) notifications, gated by role/department visibility exactly as jdk_clean's notification_service.py does, each item deep-linked back to its source record. Backs NotificationDrawer.vue and the dashboard's PendingTasksWidget / UpcomingDeadlinesWidget.

PASS B14
Reports API
Aggregation queries for executive, project, and workload reports powering BarChart.vue, LineChart.vue and ProgressChart.vue with real data.

PASS B15
Email & Messaging Service
Send-document-as-attachment (ported from email_service.py), message templates, message log. Backs MessageCentrePage.vue and the send-email dialog flow.

PASS B16
Cutover
Swap each src/services/*.ts mock implementation for real Axios calls against the new API, add the client.ts interceptor pattern (token attach, single-flight refresh-on-401, retry), remove the mock/ dependency page-by-page, and re-run Pass 35/36-style QA against the live backend.
