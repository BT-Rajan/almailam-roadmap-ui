"""
Creates real, comprehensive test data that exercises EVERY stage of the
Project workflow -- Requirement, Quotation, Payment Plan, Contract,
Design, Government Submission (Approvals & Permits), Supervision, and
Completed. Goes through the real service layer throughout (the exact
functions the API itself calls), including the real Requirement/
Quotation/Contract/Hand-over signed-document-upload confirmation flows
(a fake in-memory PDF stands in for the client's physically signed
copy) -- SMTP is mocked out so the script can run headless, but every
state transition it produces is one a real user action would also
have produced, not a shortcut that skips validation.

One project is created per workflow stage, each deliberately left
sitting mid-flight AT that stage (e.g. the Quotation demo project has a
finalized quotation awaiting approval, not an approved one) so it's
immediately useful for browsing/testing that stage's UI without having
to manually drive a project there first:

  1. Requirement           -- scope of work drafted, not yet client-confirmed
  2. Quotation              -- finalized, awaiting client approval
  3. Payment Plan           -- agreement(s) created, awaiting approval
  4. Contract                -- finalized, awaiting client signature
  5. Design                  -- one activity closed via its tasks, one still open
  6. Government Submission   -- permit application filed and under review
  7. Supervision             -- permit closed, one supervision activity still open
  8. Completed                -- every track closed, fully paid, hand-over acknowledged

Every demo project shares the same realistic scope (two Design
activities, one Permit, one Supervision activity) -- scope is frozen at
project creation in this app, so this is also what "test all stages"
implicitly exercises: the same picked-at-setup activities followed all
the way through, not a different make-believe scope per stage.

Also provisions one Site Engineer Portal login (the engineer assigned
to every demo project) and one Customer Portal login (for the
Completed project's client, since a finished project is what portal
browsing is most interesting against).

Safe to run against a staging/test database. Creates new records only
(new clients, new projects, catalog rows, two new users) -- it does not
modify or delete anything that already exists. Do not run this against
production unless you're comfortable with these test records living
there permanently (there's no cleanup step).

Usage
-----
Run from the backend/ directory, with the same environment variables
you already use to run the app itself:

  cd backend
  DB_HOST=... DB_PORT=... DB_USER=... DB_PASSWORD=... DB_NAME=... \
  JWT_SECRET_KEY=... python create_test_data.py

At the end it prints every credential, project number, and which stage
each project demonstrates.
"""

import io
import sys
import time
from datetime import date
from datetime import time as time_of_day
from unittest.mock import patch

sys.path.insert(0, ".")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.security import hash_password
from fastapi import UploadFile
from app.models import user as user_models
from app.models.government import GovernmentAuthority, GovernmentForm
from app.models.permit_catalog import PermitCatalogItem
from app.models.service_catalog import ServiceCatalogItem
from app.schemas import client as cs
from app.schemas import contract as cons
from app.schemas import government as gs
from app.schemas import payment as pays
from app.schemas import project as ps
from app.schemas import quotation as qs
from app.schemas import task as ts
from app.services import (
    client_service,
    contract_service,
    document_requirement_service,
    government_service,
    payment_service,
    permit_catalog_service,
    project_service,
    quotation_service,
    service_catalog_service,
    submission_service,
    task_service,
    user_service,
)

settings = get_settings()
engine = create_engine(settings.database_url)
Session = sessionmaker(bind=engine)
db = Session()

# -- Headless email -------------------------------------------------
# Every email-OTP-gated confirmation step in this app (Requirement,
# Quotation, Contract, Hand-over, both Client onboarding flows) is now
# confirmed by uploading a scan of the client's physically signed copy
# instead (see confirm_requirement_scope/confirm_quotation_approval/
# confirm_contract_signing/confirm_project_handover/confirm_onboarding_
# verification/confirm_onboarding_request) -- see MINI_PDF_BYTES/
# _pdf_upload below for the fake upload this script uses. SMTP is still
# mocked out since some of those confirmations also email the client a
# courtesy copy, and there's no guarantee SMTP is configured in
# whatever environment this runs in.
_email_patch = patch("app.services.email_service.send_email")
_doc_email_patch = patch("app.services.email_service.send_document_email")
_email_patch.start()
_doc_email_patch.start()

# A minimal but genuinely valid single-page PDF -- passes the upload
# endpoint's magic-byte signature check (save_upload/_verify_signature
# in app/core/file_storage.py look for a real "%PDF" header, not just a
# ".pdf" filename), used for the government submission's required
# document upload below.
MINI_PDF_BYTES = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 44 >>
stream
BT /F1 18 Tf 20 100 Td (Site Plan) Tj ET
endstream
endobj
xref
0 6
trailer
<< /Size 6 /Root 1 0 R >>
startxref
0
%%EOF
"""


def _pdf_upload(filename: str) -> UploadFile:
    """A fresh UploadFile over MINI_PDF_BYTES -- the stream position on
    an UploadFile is consumed after one read, so every confirm_* call
    below needs its own instance rather than sharing one."""
    return UploadFile(io.BytesIO(MINI_PDF_BYTES), filename=filename)


# -- Setup: admin actor, engineer, catalog lookups -----------------------


def find_admin() -> user_models.User:
    admin = (
        db.query(user_models.User)
        .filter(user_models.User.role == "Administrator", user_models.User.deleted_at.is_(None))
        .first()
    )
    if admin is None:
        raise RuntimeError("No Administrator user exists yet -- create one first (see create_admin.py).")
    return admin


def find_or_create_user(*, username: str, employee_id: str | None, email: str, full_name: str, role: str) -> user_models.User:
    existing = (
        db.query(user_models.User)
        .filter(user_models.User.username == username, user_models.User.deleted_at.is_(None))
        .first()
    )
    if existing is not None:
        return existing
    user = user_models.User(
        username=username,
        employee_id=employee_id,
        email=email,
        password_hash=hash_password("StageDemo123!"),
        full_name=full_name,
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def find_design_service(actor: user_models.User) -> ServiceCatalogItem:
    """The seeded named Design services (Structural Engineering, MEP
    Design, ...) exist as bare service rows with NO activities at all --
    only the catalog's Permit/Supervision services get default child
    activities seeded (see service_catalog_service._ensure_seeded).
    Excludes "Permit" itself here since that's a distinct, separately-
    selected part of a project's scope (selectedPermits), not what
    selectedActivities should be built from. Picks whichever named
    Design service already has the most activities (an install that's
    had real catalog editing done on it), adding two realistic priced
    activities to one if none has any yet -- needed so one demo project
    can show one Complete activity alongside one still-open one."""
    design_services = [s for s in service_catalog_service.list_services(db) if s.branch == "Design" and s.name != "Permit"]
    if not design_services:
        raise RuntimeError("No named Design-branch service catalog items exist -- expected default seed data.")
    service = max(design_services, key=lambda s: len(s.activities))
    if len(service.activities) < 2:
        service_catalog_service.add_activity(db, f"SVC-{service.id:03d}", "Structural Drawings & Calculations", 6000.00, actor.id)
        service_catalog_service.add_activity(db, f"SVC-{service.id:03d}", "Site Inspection & Sign-off", 2500.00, actor.id)
        service = service_catalog_service.get_service(db, f"SVC-{service.id:03d}")
    return service


def find_supervision_service() -> ServiceCatalogItem:
    supervision_services = [s for s in service_catalog_service.list_services(db) if s.branch == "Supervision"]
    if not supervision_services:
        raise RuntimeError("No Supervision-branch service catalog item exists -- expected default seed data.")
    service = max(supervision_services, key=lambda s: len(s.activities))
    if not service.activities:
        raise RuntimeError(f"Service '{service.name}' has no activities -- expected default seed data.")
    return service


def find_permit() -> PermitCatalogItem:
    permits = permit_catalog_service.list_permits(db)
    if not permits:
        raise RuntimeError("No Permit catalog items exist -- expected default seed data.")
    return permits[0]


def get_kuwait_municipality() -> GovernmentAuthority:
    authority = (
        db.query(GovernmentAuthority)
        .filter(GovernmentAuthority.deleted_at.is_(None))
        .order_by(GovernmentAuthority.id.asc())
        .first()
    )
    if authority is None:
        raise RuntimeError("No Government Authority exists -- expected default seed data (migration 0046).")
    return authority


def get_or_create_demo_form(authority: GovernmentAuthority, actor: user_models.User) -> GovernmentForm:
    """A form of our own, distinct from the seeded GF-29, specifically
    because GF-29 is seeded with an empty required_documents list --
    all_documents_satisfied() treats an empty checklist as never
    satisfied, so a submission built against it can never reach
    Approved. This one has exactly one required document ("Site Plan"),
    so the Government Submission demo data can actually be driven all
    the way through."""
    existing = (
        db.query(GovernmentForm)
        .filter(GovernmentForm.form_code == "STAGE-DEMO-1", GovernmentForm.deleted_at.is_(None))
        .first()
    )
    if existing is not None:
        return existing
    return government_service.create_form(
        db,
        gs.FormIn(
            authorityId=f"AUTH-{authority.id:03d}",
            formCode="STAGE-DEMO-1",
            title="Stage Demo Building Permit Application",
            version="1.0",
            language="English",
            category="Building Permit",
            description="Test-data form with a real required-document checklist, used by create_test_data.py "
            "so a submission built against it can actually reach Approved.",
            requiredDocuments=["Site Plan"],
        ),
        actor.id,
    )


# -- Client / identification ----------------------------------------------

# A short per-run numeric tag, not just a per-client counter that
# restarts at 0 every process start -- otherwise a second run of this
# script hits the exact same client mobile/email as the first, which
# collides once something checks for global uniqueness (Customer Portal
# login provisioning does, even though Client rows themselves don't).
_run_tag = str(int(time.time()) % 100000)
_client_counter = 0


def create_ready_client(actor: user_models.User, label: str):
    global _client_counter
    _client_counter += 1
    payload = cs.ClientCreate(
        clientType="Individual",
        companyName=f"Stage Demo Client -- {label}",
        contactPerson=f"Stage Demo Client -- {label}",
        mobile=f"+965{_run_tag}{_client_counter:03d}",
        email=f"stage.demo.{_run_tag}.{_client_counter}@example.com",
        city="Kuwait City",
        individualProfile={
            "fullLegalName": f"Stage Demo Client {_client_counter}",
            "nationality": "Kuwaiti",
            "dateOfBirth": "1988-06-15",
            "countryOfResidence": "Kuwait",
        },
    )
    client = client_service.create_client(db, payload, actor.id)
    # The lightweight onboarding path -- goes straight from create_client's
    # actual starting state ("Pending Verification") to "Ready" in one
    # hop, rather than the full signed-document-upload confirmation (see
    # the Completed project's client near the end of main(), which does
    # get a real Customer Portal login provisioned via
    # user_service.create_client_portal_user directly).
    client_service.set_onboarding_state(db, client.id, "Ready", None, actor.id)
    return client


def add_identification(actor: user_models.User, client) -> None:
    client_service.create_identification(
        db,
        client.id,
        cs.ClientIdentificationCreate(
            documentType="Civil ID",
            documentNumber=f"280010199{client.id:05d}",
            issueDate=date(2023, 1, 1),
            expiryDate=date(2033, 1, 1),
            issuingCountry="Kuwait",
        ),
        actor.id,
    )


# -- Scope payload shared by every demo project ----------------------------


def design_activity_payload(service: ServiceCatalogItem, activity) -> dict:
    return {
        "serviceId": f"SVC-{service.id:03d}",
        "serviceName": service.name,
        "activityId": f"ACT-{activity.id:03d}",
        "activityName": activity.name,
        "fixedCost": float(activity.fixed_cost),
    }


def supervision_activity_payload(activity, start: date, end: date) -> dict:
    return {
        "activityId": f"ACT-{activity.id:03d}",
        "activityName": activity.name,
        "monthlyRate": float(activity.fixed_cost) or 500.0,
        "startDate": start,
        "endDate": end,
    }


def permit_payload(permit: PermitCatalogItem) -> dict:
    return {"permitId": f"PER-{permit.id:03d}", "permitName": permit.name}


SUPERVISION_WINDOW = (date(2026, 4, 1), date(2026, 6, 30))
SCOPE_TEXT = (
    "Full architectural and structural design for a 3-storey residential building, including MEP "
    "coordination, municipal permit filing, and construction-phase site supervision -- per the "
    "client's approved concept drawings."
)


def create_demo_project(
    actor: user_models.User,
    client,
    engineer: user_models.User,
    *,
    name: str,
    design_service: ServiceCatalogItem,
    design_activities: list,
    supervision_service: ServiceCatalogItem,
    supervision_activity,
    permit: PermitCatalogItem,
):
    payload = ps.ProjectCreate(
        projectName=name,
        description=SCOPE_TEXT,
        clientId=f"CLT-{client.id:03d}",
        service="Civil Engineering",
        engineerId=f"USR-{engineer.id:03d}",
        priority="Medium",
        startDate=date(2026, 1, 1),
        targetDate=date(2026, 12, 31),
        selectedActivities=[design_activity_payload(design_service, activity) for activity in design_activities],
        selectedSupervisionActivities=[supervision_activity_payload(supervision_activity, *SUPERVISION_WINDOW)],
        supervisionStartDate=SUPERVISION_WINDOW[0],
        supervisionEndDate=SUPERVISION_WINDOW[1],
        selectedPermits=[permit_payload(permit)],
        siteAddress="Plot 12, Block 4, Salmiya, Kuwait",
    )
    return project_service.create_project(db, payload, actor.id)


# -- Per-stage step helpers ------------------------------------------------
# Each function drives a project through exactly one stage transition,
# via the same real service calls the API/frontend uses. Every project
# below calls a prefix of these and stops -- whatever the last call is
# determines which stage that project is left sitting at.


def do_requirement(actor: user_models.User, project, client, *, add_id: bool, confirm: bool) -> None:
    """Enters the scope of work; optionally adds the client's
    identification document and confirms it with a signed-document
    upload, which is what actually lets the project leave Requirement
    (see project_service._assert_stage_exit_criteria)."""
    project_service.save_scope_of_work(db, project.project_no, SCOPE_TEXT, "Initial scope of work", actor.id)
    if add_id:
        add_identification(actor, client)
    if confirm:
        project_service.confirm_requirement_scope(db, project.project_no, _pdf_upload("scope-confirmation.pdf"), actor.id)


def do_quotation(actor: user_models.User, project, *, approve: bool):
    """Creates and finalizes a quotation; optionally approves it via the
    real client-confirmation OTP, which auto-advances the project
    straight to Payment Plan."""
    quotation = quotation_service.create_quotation(
        db,
        qs.QuotationCreate(
            projectId=project.project_no,
            validity=date(2026, 3, 1),
            currency="KWD",
            lineItems=[
                {"description": "Architectural & structural design", "quantity": 1, "unitPrice": 8000},
                {"description": "MEP coordination", "quantity": 1, "unitPrice": 3500},
                {"description": "Municipal permit filing", "quantity": 1, "unitPrice": 1200},
            ],
        ),
        actor.id,
    )
    quotation_service.finalize_quotation(db, quotation.quotation_no, actor.id)
    if approve:
        quotation_service.confirm_quotation_approval(db, quotation.quotation_no, _pdf_upload("signed-quotation.pdf"), actor.id)
        db.refresh(quotation)
    return quotation


def do_payment_plan(actor: user_models.User, project, quotation, *, approve: bool):
    """Creates a Design-stream agreement covering the quotation's line
    items, plus a Supervision-stream agreement derived from the
    project's own selected Supervision activity. Optionally approves
    both -- every included stream's agreement must be Approved before
    the project can advance to Contract."""
    design_amount = float(quotation.amount)
    design_agreement = payment_service.create_agreement(
        db,
        pays.FinancialAgreementCreate(
            projectId=project.project_no,
            stream="Design",
            contractAmount=design_amount,
            contractStartDate=date(2026, 3, 10),
            paymentFrequency="One-time",
            agreementDate=date(2026, 3, 5),
            quotationReference=quotation.quotation_no,
            paymentMode="Bank Transfer",
        ),
        actor.id,
    )
    supervision_agreement = payment_service.create_agreement(
        db,
        pays.FinancialAgreementCreate(
            projectId=project.project_no,
            stream="Supervision",
            agreementDate=date(2026, 3, 5),
            paymentMode="Bank Transfer",
        ),
        actor.id,
    )
    if approve:
        payment_service.approve_agreement(db, design_agreement.id, actor.id)
        payment_service.approve_agreement(db, supervision_agreement.id, actor.id)
    return design_agreement, supervision_agreement


def do_contract(actor: user_models.User, project, quotation, *, sign: bool):
    """Creates and finalizes a contract from the approved quotation;
    optionally signs it via the real signed-document-upload
    confirmation, which auto-advances the project into Design (this
    app always includes Design in the demo scope, so Contract never
    routes straight to Government Submission here)."""
    contract = contract_service.create_contract(
        db,
        cons.ContractCreate(
            projectId=project.project_no,
            quotationId=quotation.quotation_no,
            currency="KWD",
            contractValue=float(quotation.amount),
            expiryDate=date(2026, 12, 31),
            clientRepresentative="Stage Demo Client",
            scopeSummary="Design, municipal permit filing, and construction-phase supervision per the approved quotation.",
            clauses=[{"title": "Payment Terms", "content": "As per the agreed payment plan."}],
        ),
        actor.id,
    )
    contract_service.finalize_contract(db, contract.contract_no, actor.id)
    if sign:
        contract_service.confirm_contract_signing(db, contract.contract_no, _pdf_upload("signed-contract.pdf"), actor.id)
    return contract


def close_design_activity_via_tasks(actor: user_models.User, project, engineer: user_models.User, activity_row_id: int, title: str) -> None:
    """Closes a Design activity the real, task-driven way: creates a
    task linked to it, drives the task Pending -> In Progress ->
    Completed (the only allowed path), and lets project_service.
    maybe_auto_close_design_activity close the activity once every one
    of its linked tasks is Completed."""
    task = task_service.create_task(
        db,
        ts.TaskCreate(
            projectId=project.project_no,
            title=title,
            assignedTo=f"USR-{engineer.id:03d}",
            dueDate=date(2026, 4, 1),
            dueTime=time_of_day(17, 0),
            selectedActivityId=str(activity_row_id),
        ),
        actor.id,
    )
    task_service.set_status(db, task.task_no, "In Progress", None, actor.id)
    task_service.set_status(db, task.task_no, "Completed", None, actor.id)


def open_design_activity_via_task(actor: user_models.User, project, engineer: user_models.User, activity_row_id: int, title: str) -> None:
    """Leaves a Design activity visibly in progress -- a linked task
    that's been started but not finished, so the activity itself stays
    open (auto-close only fires once every linked task is Completed)."""
    task = task_service.create_task(
        db,
        ts.TaskCreate(
            projectId=project.project_no,
            title=title,
            assignedTo=f"USR-{engineer.id:03d}",
            dueDate=date(2026, 5, 15),
            dueTime=time_of_day(17, 0),
            selectedActivityId=str(activity_row_id),
        ),
        actor.id,
    )
    task_service.set_status(db, task.task_no, "In Progress", None, actor.id)


def do_government_submission(
    actor: user_models.User, project, authority: GovernmentAuthority, form: GovernmentForm, selected_permit_row_id: int, *, approve: bool
):
    """Files a permit application against the project's own planned
    permit, progresses it to Under Review with its one required
    document uploaded, and optionally approves it -- which auto-
    advances the project to Supervision, but does NOT itself close the
    linked ProjectSelectedPermit (that's always a separate, direct
    user action, see close_permit below)."""
    submission = submission_service.create_submission(
        db,
        gs.SubmissionCreate(
            projectId=project.project_no,
            authorityId=f"AUTH-{authority.id:03d}",
            formId=f"FORM-{form.id:03d}",
            expectedDecisionDate=date(2026, 6, 1),
            notes="Filed as part of the stage-coverage test data.",
            selectedPermitId=str(selected_permit_row_id),
        ),
        actor.id,
    )
    # Required documents can only be attached while still Draft.
    documents = submission_service.get_documents(db, submission.id)
    upload = UploadFile(io.BytesIO(MINI_PDF_BYTES), filename="site-plan.pdf")
    submission_service.upload_document(db, submission.submission_no, documents[0].id, upload, actor.id)

    submission_service.set_status(db, submission.submission_no, "Submitted", None, actor.id)
    submission_service.set_status(db, submission.submission_no, "Under Review", None, actor.id)

    if approve:
        submission_service.set_status(db, submission.submission_no, "Approved", None, actor.id)
    return submission


def advance_past_design(actor: user_models.User, project) -> None:
    """Closing every Design activity satisfies the Design -> Government
    Submission exit criterion, but nothing in the close path itself
    calls try_auto_advance_stage (unlike every other stage transition
    in this app, which is triggered from whichever action just made its
    own criteria true) -- the real app only picks this up incidentally,
    the next time some unrelated action (a document upload, a new
    submission being approved, ...) happens to call it. Calling it here
    directly is the same public, side-effect-free-if-not-eligible check
    every other trigger point already uses, just invoked explicitly
    since nothing else in this script's sequence would happen to."""
    project_service.try_auto_advance_stage(db, project, actor.id)
    db.commit()


def close_permit(actor: user_models.User, project, permit_row_id: int) -> None:
    project_service.set_permit_status(db, project.project_no, permit_row_id, "Complete", actor.id)


def set_supervision_in_progress(actor: user_models.User, project, activity_row_id: int) -> None:
    project_service.set_supervision_status(db, project.project_no, activity_row_id, "In Progress", actor.id)


def close_supervision_activity(actor: user_models.User, project, activity_row_id: int) -> None:
    project_service.set_supervision_status(db, project.project_no, activity_row_id, "Complete", actor.id)


def pay_agreement_in_full(actor: user_models.User, agreement) -> None:
    obligations = payment_service.get_obligations(db, agreement.id)
    allocations = [{"obligationId": f"OBL-{agreement.id:03d}-{o.sequence_number:02d}", "amount": float(o.amount_due)} for o in obligations]
    total = sum(a["amount"] for a in allocations)
    if total <= 0:
        return
    payment_service.record_payment(
        db,
        pays.RecordPaymentInput(
            agreementId=f"FA-{agreement.id:03d}",
            amountReceived=total,
            paymentDate=date(2026, 7, 1),
            paymentMode="Bank Transfer",
            payer="Stage Demo Client",
            allocations=allocations,
        ),
        actor.id,
    )


def complete_handover(actor: user_models.User, project) -> None:
    """try_complete_project (fired automatically by the last track close
    or payment above) already generated the hand-over checklist and
    notified Administrators it's ready -- this is staff confirming the
    client's signed acknowledgment, the only path to Project.status ==
    'Completed'."""
    project_service.confirm_project_handover(db, project.project_no, _pdf_upload("signed-handover.pdf"), actor.id)


# -- Document Requirements (admin, informational) --------------------------


def get_or_create_requirement(actor: user_models.User, name: str, description: str):
    existing = next((r for r in document_requirement_service.list_requirements(db) if r.name == name), None)
    if existing is not None:
        return existing
    return document_requirement_service.create_requirement(db, name, description, actor.id)


def seed_document_requirements(actor: user_models.User, design_activity_id: int, permit_id: int, supervision_activity_id: int) -> None:
    """Purely informational -- never enforced against task/activity
    closure -- so this just needs to exist to populate the reference
    checklist shown on the Design/Permit/Supervision tabs; it's not
    something the rest of the flow depends on."""
    survey = get_or_create_requirement(actor, "Site Survey Report", "Topographic survey of the plot.")
    document_requirement_service.add_link(db, str(survey.id), "Design", f"ACT-{design_activity_id:03d}")

    title_deed = get_or_create_requirement(actor, "Title Deed Copy", "Certified copy of the property title deed.")
    document_requirement_service.add_link(db, str(title_deed.id), "Permit", f"PER-{permit_id:03d}")

    site_access = get_or_create_requirement(actor, "Site Access Authorization", "Signed authorization letter permitting site visits.")
    document_requirement_service.add_link(db, str(site_access.id), "Supervision", f"ACT-{supervision_activity_id:03d}")


# -- Main -------------------------------------------------------------------


def main() -> None:
    print(f"Connecting to {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME} ...")
    actor = find_admin()
    engineer = find_or_create_user(
        username="stage_demo_engineer",
        employee_id="EMP-STAGEDEMO-001",
        email="stage.demo.engineer@example.com",
        full_name="Stage Demo Engineer",
        role="Engineer",
    )

    design_service = find_design_service(actor)
    design_activity_a, design_activity_b = design_service.activities[0], design_service.activities[1]
    supervision_service = find_supervision_service()
    supervision_activity = supervision_service.activities[0]
    permit = find_permit()
    authority = get_kuwait_municipality()
    demo_form = get_or_create_demo_form(authority, actor)

    seed_document_requirements(actor, design_activity_a.id, permit.id, supervision_activity.id)

    results: list[tuple[str, str]] = []

    def new_project(label: str):
        client = create_ready_client(actor, label)
        project = create_demo_project(
            actor,
            client,
            engineer,
            name=f"Stage Demo -- {label}",
            design_service=design_service,
            design_activities=[design_activity_a, design_activity_b],
            supervision_service=supervision_service,
            supervision_activity=supervision_activity,
            permit=permit,
        )
        return client, project

    # 1. Requirement -- scope drafted, not yet client-confirmed.
    client_1, project_1 = new_project("Requirement")
    do_requirement(actor, project_1, client_1, add_id=False, confirm=False)
    results.append((project_1.project_no, "Requirement (scope drafted, awaiting client confirmation)"))

    # 2. Quotation -- finalized, awaiting client approval.
    client_2, project_2 = new_project("Quotation")
    do_requirement(actor, project_2, client_2, add_id=True, confirm=True)
    do_quotation(actor, project_2, approve=False)
    results.append((project_2.project_no, "Quotation (finalized, awaiting client approval)"))

    # 3. Payment Plan -- agreements created, awaiting approval.
    client_3, project_3 = new_project("Payment Plan")
    do_requirement(actor, project_3, client_3, add_id=True, confirm=True)
    quotation_3 = do_quotation(actor, project_3, approve=True)
    do_payment_plan(actor, project_3, quotation_3, approve=False)
    results.append((project_3.project_no, "Payment Plan (agreements created, awaiting approval)"))

    # 4. Contract -- finalized, awaiting client signature.
    client_4, project_4 = new_project("Contract")
    do_requirement(actor, project_4, client_4, add_id=True, confirm=True)
    quotation_4 = do_quotation(actor, project_4, approve=True)
    do_payment_plan(actor, project_4, quotation_4, approve=True)
    do_contract(actor, project_4, quotation_4, sign=False)
    results.append((project_4.project_no, "Contract (finalized, awaiting client signature)"))

    # 5. Design -- one activity closed via its tasks, one still open.
    client_5, project_5 = new_project("Design")
    do_requirement(actor, project_5, client_5, add_id=True, confirm=True)
    quotation_5 = do_quotation(actor, project_5, approve=True)
    do_payment_plan(actor, project_5, quotation_5, approve=True)
    do_contract(actor, project_5, quotation_5, sign=True)
    activities_5 = {a.activity_name: a for a in project_service.get_selected_activities(db, project_5.id)}
    close_design_activity_via_tasks(actor, project_5, engineer, activities_5[design_activity_a.name].id, f"Complete {design_activity_a.name}")
    open_design_activity_via_task(actor, project_5, engineer, activities_5[design_activity_b.name].id, f"Work on {design_activity_b.name}")
    results.append((project_5.project_no, "Design (one activity Complete, one still open with an in-progress task)"))

    # 6. Government Submission -- permit application filed and under review.
    client_6, project_6 = new_project("Government Submission")
    do_requirement(actor, project_6, client_6, add_id=True, confirm=True)
    quotation_6 = do_quotation(actor, project_6, approve=True)
    do_payment_plan(actor, project_6, quotation_6, approve=True)
    do_contract(actor, project_6, quotation_6, sign=True)
    for activity in project_service.get_selected_activities(db, project_6.id):
        close_design_activity_via_tasks(actor, project_6, engineer, activity.id, f"Complete {activity.activity_name}")
    advance_past_design(actor, project_6)
    permit_row_6 = project_service.get_selected_permits(db, project_6.id)[0]
    do_government_submission(actor, project_6, authority, demo_form, permit_row_6.id, approve=False)
    results.append((project_6.project_no, "Government Submission (permit application Under Review)"))

    # 7. Supervision -- permit closed, one supervision activity still open.
    client_7, project_7 = new_project("Supervision")
    do_requirement(actor, project_7, client_7, add_id=True, confirm=True)
    quotation_7 = do_quotation(actor, project_7, approve=True)
    do_payment_plan(actor, project_7, quotation_7, approve=True)
    do_contract(actor, project_7, quotation_7, sign=True)
    for activity in project_service.get_selected_activities(db, project_7.id):
        close_design_activity_via_tasks(actor, project_7, engineer, activity.id, f"Complete {activity.activity_name}")
    advance_past_design(actor, project_7)
    permit_row_7 = project_service.get_selected_permits(db, project_7.id)[0]
    do_government_submission(actor, project_7, authority, demo_form, permit_row_7.id, approve=True)
    close_permit(actor, project_7, permit_row_7.id)
    supervision_row_7 = project_service.get_selected_supervision_activities(db, project_7.id)[0]
    set_supervision_in_progress(actor, project_7, supervision_row_7.id)
    results.append((project_7.project_no, "Supervision (permit Complete, supervision activity In Progress)"))

    # 8. Completed -- every track closed, fully paid, hand-over acknowledged.
    client_8, project_8 = new_project("Completed")
    do_requirement(actor, project_8, client_8, add_id=True, confirm=True)
    quotation_8 = do_quotation(actor, project_8, approve=True)
    design_agreement_8, supervision_agreement_8 = do_payment_plan(actor, project_8, quotation_8, approve=True)
    do_contract(actor, project_8, quotation_8, sign=True)
    for activity in project_service.get_selected_activities(db, project_8.id):
        close_design_activity_via_tasks(actor, project_8, engineer, activity.id, f"Complete {activity.activity_name}")
    advance_past_design(actor, project_8)
    permit_row_8 = project_service.get_selected_permits(db, project_8.id)[0]
    do_government_submission(actor, project_8, authority, demo_form, permit_row_8.id, approve=True)
    close_permit(actor, project_8, permit_row_8.id)
    supervision_row_8 = project_service.get_selected_supervision_activities(db, project_8.id)[0]
    close_supervision_activity(actor, project_8, supervision_row_8.id)
    pay_agreement_in_full(actor, design_agreement_8)
    pay_agreement_in_full(actor, supervision_agreement_8)
    # The final payment above already triggered try_complete_project
    # (every track was already closed) and notified Administrators the
    # project is ready for hand-over.
    complete_handover(actor, project_8)
    results.append((project_8.project_no, "Completed (fully paid, hand-over acknowledged)"))

    # Give the Completed project's client a working Customer Portal
    # login -- create_client_portal_user is normally only ever called
    # from confirm_onboarding_verification/confirm_onboarding_request
    # (the real signed-document-upload confirmation), but calling it
    # directly here is the same real provisioning step without needing
    # to run every other demo client through that extra round trip too.
    portal_user, portal_password = user_service.create_client_portal_user(db, client_8, actor.id)
    db.commit()

    print()
    print("=" * 78)
    print("STAGE-COVERAGE TEST DATA CREATED")
    print("=" * 78)
    print()
    print(f"{'Project No.':<14}{'Stage demonstrated'}")
    print("-" * 78)
    for project_no, description in results:
        print(f"{project_no:<14}{description}")
    print()
    print("--- Logins ---")
    print("  Site Engineer:   Employee ID = EMP-STAGEDEMO-001   Password = StageDemo123!")
    print(f"  Customer Portal: Mobile = {client_8.mobile}   Username = {portal_user.username}   Password = {portal_password}")
    print()
    print("=" * 78)


if __name__ == "__main__":
    try:
        main()
    finally:
        _email_patch.stop()
        _doc_email_patch.stop()
