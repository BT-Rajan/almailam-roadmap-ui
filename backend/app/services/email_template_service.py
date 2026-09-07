"""Admin-editable subject/body for every automated email the app sends
(OTP codes, welcome/confirmation copies) -- the plain-text counterpart
to document_template_service.py's admin-uploaded .docx templates for
Quotation/Contract documents. Same "{{ field }} placeholder, admin
controls the wording, code supplies the data" philosophy, just simple
regex substitution instead of docxtpl since there's no document
structure (tables, images) to merge into -- these are single paragraphs
of email copy.

DEFAULT_TEMPLATES is the single source of truth for each template's
original content -- migration 0069 seeds email_templates from it
verbatim, and render() below falls back to it if a row is ever missing
(a fresh install that hasn't run the migration yet, or a row deleted
out from under the app), so a missing row degrades gracefully instead
of breaking email sending.
"""

import re

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.email_template import EMAIL_TEMPLATE_KEYS, EmailTemplate
from app.services import audit_service

ENTITY_TYPE = "EMAIL_TEMPLATE"

_TOKEN_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")

DEFAULT_TEMPLATES: dict[str, dict[str, str]] = {
    "client_onboarding_otp": {
        "subject": "Your Al Mailam verification code",
        "body": (
            "Your verification code is {{ code }}.\n\n"
            "Share this code with the staff member handling your onboarding to confirm your "
            "email address. It expires in {{ validity_label }}.\n\n"
            "If you didn't request this, you can safely ignore this email."
        ),
    },
    "client_welcome": {
        "subject": "Welcome to Al Mailam -- your account is ready",
        "body": (
            "Dear {{ contact_person }},\n\n"
            "Welcome to Al Mailam! Your email has been verified and your onboarding is complete.\n\n"
            "Here are the details we have on file for you:\n"
            "Client type: {{ client_type }}\n"
            "Name: {{ company_name }}\n"
            "Contact person: {{ contact_person }}\n"
            "Mobile: {{ mobile }}\n"
            "Email: {{ email }}\n"
            "City: {{ city }}\n"
            "Preferred language: {{ preferred_language }}\n"
            "Preferred contact channel: {{ preferred_channel }}\n\n"
            "You can now sign in to the Client Portal to track your projects:\n"
            "Customer ID: {{ customer_id }}\n"
            "Temporary password: {{ temporary_password }}\n\n"
            "For your security, please sign in and change this password as soon as possible."
        ),
    },
    "project_created": {
        "subject": "New project created: {{ project_name }} ({{ project_no }})",
        "body": (
            "Dear {{ contact_person }},\n\n"
            "A new project has been created for {{ company_name }}:\n\n"
            "Project: {{ project_name }} ({{ project_no }})\n"
            "Service: {{ service }}\n"
            "{{ site_address_line }}"
            "Start date: {{ start_date }}\n"
            "Target date: {{ target_date }}\n"
            "Assigned engineer: {{ engineer_name }}\n\n"
            "We'll keep you updated as work progresses. You can also track this project's "
            "status anytime through the Client Portal.\n\n"
            "This is an informational message -- no action is needed."
        ),
    },
    "requirement_otp": {
        "subject": "Confirm the scope of work for {{ project_name }}",
        "body": (
            "Dear {{ contact_person }},\n\n"
            "Your verification code is {{ code }}.\n\n"
            "Share this code with the staff member handling project {{ project_name }} "
            "({{ project_no }}) to confirm you accept the scope of work as written. "
            "It expires in {{ validity_label }}.\n\n"
            "If you didn't request this, you can safely ignore this email."
        ),
    },
    "requirement_confirmed": {
        "subject": "Scope of work confirmed for {{ project_name }}",
        "body": (
            "Dear {{ contact_person }},\n\n"
            "Thank you for confirming the scope of work for {{ project_name }} "
            "({{ project_no }}):\n\n{{ scope_text }}\n\n"
            "This is an informational message -- no action is needed."
        ),
    },
    "quotation_otp": {
        "subject": "Your approval code for Quotation {{ quotation_no }}",
        "body": (
            "Dear {{ contact_person }},\n\n"
            "Your verification code is {{ code }}.\n\n"
            "Share this code with the staff member handling Quotation {{ quotation_no }} "
            "to confirm you accept it. It expires in {{ validity_label }}.\n\n"
            "If you didn't request this, you can safely ignore this email."
        ),
    },
    "quotation_approved": {
        "subject": "Quotation {{ quotation_no }} confirmed",
        "body": (
            "Dear {{ contact_person }},\n\n"
            "Thank you for confirming Quotation {{ quotation_no }}. Please find a copy attached.\n\n"
            "Quotation breakdown:\n{{ breakdown }}\n\n"
            "{{ scope_change_section }}"
            "{{ payment_plan_section }}"
            "This is an informational message -- no action is needed."
        ),
    },
}

# What the admin UI's reference panel offers per template -- computed
# ("breakdown", "*_section"/"*_line") fields are still listed here (the
# admin can't compute them, but seeing what they'll contain is useful),
# just not editable/removable data the way a plain field like {{ code }}
# is understood to be.
MERGE_FIELD_CATALOG: dict[str, list[dict[str, str]]] = {
    "client_onboarding_otp": [
        {"key": "code", "label": "Verification Code"},
        {"key": "validity_label", "label": "Code Validity (e.g. '24 hours')"},
    ],
    "client_welcome": [
        {"key": "contact_person", "label": "Contact Person"},
        {"key": "client_type", "label": "Client Type"},
        {"key": "company_name", "label": "Company / Client Name"},
        {"key": "mobile", "label": "Mobile"},
        {"key": "email", "label": "Email"},
        {"key": "city", "label": "City"},
        {"key": "preferred_language", "label": "Preferred Language"},
        {"key": "preferred_channel", "label": "Preferred Contact Channel"},
        {"key": "customer_id", "label": "Client Portal Customer ID"},
        {"key": "temporary_password", "label": "Client Portal Temporary Password"},
    ],
    "project_created": [
        {"key": "contact_person", "label": "Contact Person"},
        {"key": "company_name", "label": "Client Name"},
        {"key": "project_name", "label": "Project Name"},
        {"key": "project_no", "label": "Project No."},
        {"key": "service", "label": "Service"},
        {"key": "site_address_line", "label": "Site Address (whole line, blank if not set)"},
        {"key": "start_date", "label": "Start Date"},
        {"key": "target_date", "label": "Target Date"},
        {"key": "engineer_name", "label": "Assigned Engineer"},
    ],
    "requirement_otp": [
        {"key": "contact_person", "label": "Contact Person"},
        {"key": "code", "label": "Verification Code"},
        {"key": "project_name", "label": "Project Name"},
        {"key": "project_no", "label": "Project No."},
        {"key": "validity_label", "label": "Code Validity (e.g. '24 hours')"},
    ],
    "requirement_confirmed": [
        {"key": "contact_person", "label": "Contact Person"},
        {"key": "project_name", "label": "Project Name"},
        {"key": "project_no", "label": "Project No."},
        {"key": "scope_text", "label": "Confirmed Scope of Work Text"},
    ],
    "quotation_otp": [
        {"key": "contact_person", "label": "Contact Person"},
        {"key": "code", "label": "Verification Code"},
        {"key": "quotation_no", "label": "Quotation No."},
        {"key": "validity_label", "label": "Code Validity (e.g. '24 hours')"},
    ],
    "quotation_approved": [
        {"key": "contact_person", "label": "Contact Person"},
        {"key": "quotation_no", "label": "Quotation No."},
        {"key": "breakdown", "label": "Quotation Line-Item Breakdown"},
        {"key": "scope_change_section", "label": "Scope Change Section (blank unless scope was reconfirmed)"},
        {"key": "payment_plan_section", "label": "Payment Plan Section (blank if no plan exists yet)"},
    ],
}


def _check_key(key: str) -> None:
    if key not in EMAIL_TEMPLATE_KEYS:
        raise ValidationAppError(f"key must be one of {EMAIL_TEMPLATE_KEYS}")


def list_templates(db: Session) -> list[EmailTemplate]:
    return db.query(EmailTemplate).order_by(EmailTemplate.key.asc()).all()


def get_template(db: Session, key: str) -> EmailTemplate:
    _check_key(key)
    template = db.query(EmailTemplate).filter(EmailTemplate.key == key).first()
    if template is None:
        raise NotFoundError("Email template")
    return template


def get_merge_fields(key: str) -> list[dict[str, str]]:
    _check_key(key)
    return MERGE_FIELD_CATALOG[key]


def update_template(db: Session, key: str, subject: str, body: str, user_id: int) -> EmailTemplate:
    template = get_template(db, key)
    subject = subject.strip()
    body = body.strip()
    if not subject or not body:
        raise ValidationAppError("Subject and body cannot be empty.")
    changes = {}
    if template.subject != subject:
        changes["subject"] = (template.subject, subject)
    if template.body != body:
        changes["body"] = (template.body, body)
    template.subject = subject
    template.body = body
    template.updated_by = user_id
    audit_service.log_field_changes(db, ENTITY_TYPE, template.id, changes, user_id)
    db.commit()
    db.refresh(template)
    return template


def _substitute(text: str, context: dict[str, str]) -> str:
    return _TOKEN_RE.sub(lambda m: context.get(m.group(1), ""), text)


def render(db: Session, key: str, context: dict[str, str]) -> tuple[str, str]:
    """Fetches template `key`'s current subject/body (or DEFAULT_TEMPLATES
    if the row is somehow missing) and substitutes every {{ field }}
    token against `context` -- a field with no matching context entry
    renders as "" (same graceful-empty convention as {{ logo }} in
    document_template_service._render_docx), not an error, so an admin
    who removes a placeholder from their edited copy doesn't break
    sending."""
    _check_key(key)
    template = db.query(EmailTemplate).filter(EmailTemplate.key == key).first()
    subject = template.subject if template else DEFAULT_TEMPLATES[key]["subject"]
    body = template.body if template else DEFAULT_TEMPLATES[key]["body"]
    return _substitute(subject, context), _substitute(body, context)
