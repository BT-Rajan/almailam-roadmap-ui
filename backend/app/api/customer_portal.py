from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AuthError
from app.schemas.customer_portal import (
    CustomerPortalVerifyRequest,
    CustomerPortalVerifyResponse,
    CustomerProjectView,
)
from app.services import customer_portal_service

router = APIRouter(prefix="/api/customer-portal", tags=["customer-portal"])

# Deliberately its own bearer scheme, not app.api.deps.bearer_scheme --
# this endpoint is public (no staff login involved) and issues its own
# distinct token type, so it has no reason to share plumbing with the
# staff-facing auth dependency.
bearer_scheme = HTTPBearer(auto_error=False)


@router.post("/verify", response_model=CustomerPortalVerifyResponse)
def verify(payload: CustomerPortalVerifyRequest, db: Session = Depends(get_db)):
    token = customer_portal_service.verify_and_issue_token(db, payload.projectId.upper(), payload.mobileNumber)
    if not token:
        # Generic message on purpose: doesn't reveal whether the project
        # exists or the mobile number was simply wrong, same reasoning as
        # the staff login's generic "invalid credentials" message.
        raise AuthError("We couldn't verify that mobile number for this project ID. Please check and try again.")
    return CustomerPortalVerifyResponse(accessToken=token, projectId=payload.projectId.upper())


@router.get("/projects/{project_id}", response_model=CustomerProjectView)
def get_project_view(
    project_id: str,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if credentials is None:
        raise AuthError("Access link required.")
    project = customer_portal_service.get_project_for_token(db, credentials.credentials, project_id.upper())
    return customer_portal_service.get_project_view(db, project)


@router.get("/projects/{project_id}/documents/{document_id}/download")
def download_document(
    project_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if credentials is None:
        raise AuthError("Access link required.")
    project = customer_portal_service.get_project_for_token(db, credentials.credentials, project_id.upper())
    path, original_filename = customer_portal_service.get_document_download_target(db, project, document_id)
    return FileResponse(path, filename=original_filename)
