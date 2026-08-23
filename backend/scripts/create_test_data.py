"""
Creates real, valid test data for manually testing the Site Engineer
Portal and Customer Portal end-to-end. Run this against your actual
backend/database -- it goes through the real service layer (the same
functions the API itself uses), not raw SQL, so everything created is
guaranteed to pass the app's own validation, numbering, and hashing
exactly the way a real user action would.

Safe to run against a staging/test database. Creates new records only
(a new client, a new project, two new users) -- it does not modify or
delete anything that already exists. Do not run this against
production unless you're comfortable with these test records living
there permanently (there's no cleanup step).

Usage
-----
Run from the backend/ directory, with the same environment variables
you already use to run the app itself:

  cd backend
  DB_HOST=... DB_PORT=... DB_USER=... DB_PASSWORD=... DB_NAME=... \
  JWT_SECRET_KEY=... python create_test_data.py

If you're running this on the same machine/container as the backend
normally runs on, you can usually just reuse whatever .env or shell
exports are already configured there.

At the end it prints every credential and ID you need for the manual
test steps below.
"""

import sys
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, ".")

from app.core.config import get_settings
from app.core.security import hash_password
from app.models import user as user_models
from app.schemas import client as cs
from app.schemas import project as ps
from app.schemas.company import CompanySettingsIn
from app.services import client_service, company_service, project_service

settings = get_settings()
engine = create_engine(settings.database_url)
Session = sessionmaker(bind=engine)
db = Session()


def find_or_create_admin() -> user_models.User:
    admin = db.query(user_models.User).filter(user_models.User.role == "Administrator", user_models.User.deleted_at.is_(None)).first()
    if admin:
        return admin
    admin = user_models.User(
        username="test_admin", email="test_admin@example.com", password_hash=hash_password("TestAdmin123!"),
        full_name="Test Admin", role="Administrator", is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def main() -> None:
    print(f"Connecting to {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME} ...")
    actor = find_or_create_admin()

    # ---------------- Site Engineer Portal test data ----------------
    engineer = user_models.User(
        username="test_engineer",
        employee_id="EMP-TEST-001",
        email="test.engineer@example.com",
        password_hash=hash_password("EngTest123!"),
        full_name="Test Site Engineer",
        role="Engineer",
        is_active=True,
    )
    recipient = user_models.User(
        username="test_recipient",
        email="test.recipient@example.com",
        password_hash=hash_password("RecipientTest123!"),
        full_name="Test Report Recipient",
        role="Document Controller",
        is_active=True,
    )
    db.add_all([engineer, recipient])
    db.commit()
    for u in [engineer, recipient]:
        db.refresh(u)

    site_client_payload = cs.ClientCreate(
        clientType="Individual", companyName="Test Site Client", contactPerson="Test Site Client",
        mobile="+96550001001", email="test.site.client@example.com", city="Kuwait City",
        individualProfile={
            "fullLegalName": "Test Site Client", "nationality": "Kuwaiti",
            "dateOfBirth": "1990-01-01", "countryOfResidence": "Kuwait",
        },
    )
    site_client = client_service.create_client(db, site_client_payload, actor.id)
    for state in ["Documents Required", "Under Review", "Ready"]:
        client_service.set_onboarding_state(db, site_client.id, state, None, actor.id)

    site_project = project_service.create_project(
        db,
        ps.ProjectCreate(
            clientId=f"CLT-{site_client.id:03d}", projectName="Test Site Engineer Project",
            service="Civil Engineering", engineerId=f"USR-{engineer.id:03d}", priority="Medium",
            startDate=date(2026, 1, 1), targetDate=date(2026, 12, 1),
        ),
        actor.id,
    )

    current_settings = company_service.get_settings(db)
    company_service.save_settings(
        db,
        CompanySettingsIn(
            companyName=current_settings.company_name or "Almailam Engineering Consultants",
            tagline=current_settings.tagline or "", tradeLicenseNumber=current_settings.trade_license_number or "",
            email=current_settings.email or "", phone=current_settings.phone or "", website=current_settings.website or "",
            address=current_settings.address or "", city=current_settings.city or "", country=current_settings.country or "",
            brandColor=current_settings.brand_color or "#1D4ED8", defaultLanguage=current_settings.default_language or "English",
            timezone=current_settings.timezone or "Asia/Kuwait", dateFormat=current_settings.date_format or "DD/MM/YYYY",
            currency=current_settings.currency or "KWD",
            defaultPaymentTermsDays=current_settings.default_payment_terms_days,
            defaultQuotationValidityDays=current_settings.default_quotation_validity_days,
            staleProjectAlertDays=current_settings.stale_project_alert_days,
            staleOnboardingAlertDays=current_settings.stale_onboarding_alert_days,
            statusReportRecipientId=f"USR-{recipient.id:03d}",
        ),
        actor.id,
    )

    # ---------------- Customer Portal test data ----------------
    portal_client_payload = cs.ClientCreate(
        clientType="Individual", companyName="Test Portal Client", contactPerson="Test Portal Client",
        mobile="+96550002002", email="test.portal.client@example.com", city="Kuwait City",
        individualProfile={
            "fullLegalName": "Test Portal Client", "nationality": "Kuwaiti",
            "dateOfBirth": "1985-05-15", "countryOfResidence": "Kuwait",
        },
    )
    portal_client = client_service.create_client(db, portal_client_payload, actor.id)
    for state in ["Documents Required", "Under Review", "Ready"]:
        client_service.set_onboarding_state(db, portal_client.id, state, None, actor.id)

    portal_project = project_service.create_project(
        db,
        ps.ProjectCreate(
            clientId=f"CLT-{portal_client.id:03d}", projectName="Test Customer Portal Project",
            service="Civil Engineering", engineerId=f"USR-{engineer.id:03d}", priority="Medium",
            startDate=date(2026, 1, 1), targetDate=date(2026, 12, 1),
        ),
        actor.id,
    )
    # Give the project a couple of stage moves so the customer portal's
    # milestone timeline has something real to show, not an empty list.
    project_service.set_stage(db, portal_project.project_no, "Quotation", None, actor.id)
    project_service.set_stage(db, portal_project.project_no, "Contract", None, actor.id)

    print()
    print("=" * 70)
    print("TEST DATA CREATED")
    print("=" * 70)
    print()
    print("--- Site Engineer Portal ---")
    print(f"  Engineer login:   Employee ID = EMP-TEST-001   Password = EngTest123!")
    print(f"  Assigned project: {site_project.project_no} (Test Site Engineer Project)")
    print(f"  Recipient login:  Username = test_recipient    Password = RecipientTest123!")
    print()
    print("--- Customer Portal ---")
    print(f"  Mobile number:    +96550002002")
    print(f"  Project ID:       {portal_project.project_no}")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
