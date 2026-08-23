from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.customer_portal import CustomerProjectOption, CustomerProjectView
from app.services import customer_portal_service

router = APIRouter(prefix="/api/customer-portal", tags=["customer-portal"])


@router.get("/projects", response_model=list[CustomerProjectOption])
def list_my_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Every project belonging to the logged-in customer's client record.
    The frontend auto-redirects straight into the project view when
    there's exactly one, and shows a picker when there's more than one --
    unlike the old flow, login no longer carries a single project ID with
    it (see customer_portal_service.list_projects_for_customer)."""
    projects = customer_portal_service.list_projects_for_customer(db, current_user)
    return [CustomerProjectOption(projectId=p.project_no, projectName=p.project_name) for p in projects]


@router.get("/projects/{project_id}", response_model=CustomerProjectView)
def get_project_view(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = customer_portal_service.get_project_for_customer(db, current_user, project_id.upper())
    return customer_portal_service.get_project_view(db, project)


@router.get("/projects/{project_id}/documents/{document_id}/download")
def download_document(
    project_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = customer_portal_service.get_project_for_customer(db, current_user, project_id.upper())
    path, original_filename = customer_portal_service.get_document_download_target(db, project, document_id)
    return FileResponse(path, filename=original_filename)
