from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.auth import router as auth_router
from app.api.ai import router as ai_router
from app.api.activity import router as activity_router
from app.api.audit_logs import router as audit_logs_router
from app.api.clients import router as clients_router
from app.api.company import router as company_router
from app.api.contracts import router as contracts_router
from app.api.customer_portal import router as customer_portal_router
from app.api.documents import router as documents_router
from app.api.government import router as government_router
from app.api.messages import router as messages_router
from app.api.notifications import router as notifications_router
from app.api.payments import router as payments_router
from app.api.projects import router as projects_router
from app.api.quotations import router as quotations_router
from app.api.reports import router as reports_router
from app.api.roles import router as roles_router
from app.api.search import router as search_router
from app.api.submissions import router as submissions_router
from app.api.tasks import router as tasks_router
from app.api.users import router as users_router
from app.api.workflows import router as workflows_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import SecurityHeadersMiddleware

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

register_exception_handlers(app)
app.include_router(auth_router)
app.include_router(audit_logs_router)
app.include_router(activity_router)
app.include_router(ai_router)
app.include_router(users_router)
app.include_router(workflows_router)
app.include_router(roles_router)
app.include_router(clients_router)
app.include_router(company_router)
app.include_router(projects_router)
app.include_router(government_router)
app.include_router(submissions_router)
app.include_router(quotations_router)
app.include_router(contracts_router)
app.include_router(customer_portal_router)
app.include_router(payments_router)
app.include_router(documents_router)
app.include_router(tasks_router)
app.include_router(notifications_router)
app.include_router(reports_router)
app.include_router(messages_router)
app.include_router(search_router)


@app.get("/api/health")
def health_check() -> dict:
    return {"status": "ok", "env": settings.ENV}
