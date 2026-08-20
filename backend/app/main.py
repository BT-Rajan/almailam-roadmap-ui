import logging
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.ai import router as ai_router
from app.api.activity import my_router as my_activity_router
from app.api.activity import router as activity_router
from app.api.audit_logs import router as audit_logs_router
from app.api.clients import router as clients_router
from app.api.company import router as company_router
from app.api.contracts import router as contracts_router
from app.api.customer_portal import router as customer_portal_router
from app.api.execution_steps import router as execution_steps_router
from app.api.documents import router as documents_router
from app.api.government import router as government_router
from app.api.messages import router as messages_router
from app.api.notifications import router as notifications_router
from app.api.payments import router as payments_router
from app.api.project_link_documents import router as project_link_documents_router
from app.api.projects import router as projects_router
from app.api.quotations import router as quotations_router
from app.api.reports import router as reports_router
from app.api.roles import router as roles_router
from app.api.search import router as search_router
from app.api.service_catalog import router as service_catalog_router
from app.api.site_portal import router as site_portal_router
from app.api.status_reports import router as status_reports_router
from app.api.submissions import router as submissions_router
from app.api.tasks import router as tasks_router
from app.api.users import router as users_router
from app.api.workflows import router as workflows_router
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.exceptions import register_exception_handlers
from app.core.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from app.services.client_service import check_and_notify_stale_onboarding
from app.services.project_service import check_and_notify_stale_projects

settings = get_settings()
logger = logging.getLogger("app.scheduler")


def _run_staleness_checks() -> None:
    # One scheduled job running both related staleness checks, not two
    # nearly-identical jobs each with their own trigger/session
    # boilerplate. A fresh session per run, not a request-scoped one --
    # this runs on a timer, independent of any HTTP request, so there's
    # no `get_db()` dependency to piggyback on. Each check gets its own
    # try/except so a failure in one doesn't prevent the other from
    # running.
    db = SessionLocal()
    try:
        notified = check_and_notify_stale_projects(db)
        if notified:
            logger.info("Stale-project check: notified %d project(s).", notified)
    except Exception:
        logger.exception("Stale-project check failed.")
        db.rollback()

    try:
        notified = check_and_notify_stale_onboarding(db)
        if notified:
            logger.info("Stale-onboarding check: notified %d client(s).", notified)
    except Exception:
        logger.exception("Stale-onboarding check failed.")
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    # Once a day is deliberately coarse for thresholds measured in
    # days, not hours -- and the interval trigger below doesn't fire
    # immediately, so also run once right away rather than only after
    # the first full day, in case the process was down when yesterday's
    # run would have fired.
    scheduler.add_job(_run_staleness_checks, "interval", days=1, id="staleness_checks")
    _run_staleness_checks()
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
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
app.include_router(my_activity_router)
app.include_router(ai_router)
app.include_router(users_router)
app.include_router(workflows_router)
app.include_router(service_catalog_router)
app.include_router(roles_router)
app.include_router(clients_router)
app.include_router(company_router)
app.include_router(projects_router)
app.include_router(government_router)
app.include_router(submissions_router)
app.include_router(quotations_router)
app.include_router(contracts_router)
app.include_router(customer_portal_router)
app.include_router(execution_steps_router)
app.include_router(payments_router)
app.include_router(documents_router)
app.include_router(project_link_documents_router)
app.include_router(tasks_router)
app.include_router(notifications_router)
app.include_router(reports_router)
app.include_router(messages_router)
app.include_router(search_router)
app.include_router(site_portal_router)
app.include_router(status_reports_router)


@app.get("/api/health")
def health_check() -> dict:
    return {"status": "ok", "env": settings.ENV}


# ---------------------------------------------------------------------------
# Single-process, single-port frontend serving
# ---------------------------------------------------------------------------
# In production the installer builds the Vue app (npm run build) and this
# process serves the result directly, so there is exactly one process and
# one port for the whole system -- no separate vite dev server. Every /api/*
# route above still wins; anything else falls back to the SPA's index.html
# so client-side (Vue Router) routes work on refresh/deep-link. If the
# frontend hasn't been built (e.g. local API-only development), this block
# is skipped and only the API is served.
_frontend_dist = (Path(__file__).resolve().parent.parent / settings.FRONTEND_DIST_DIR).resolve()

if _frontend_dist.is_dir():
    _assets_dir = _frontend_dist / "assets"
    if _assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="frontend-assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str) -> FileResponse:
        candidate = (_frontend_dist / full_path).resolve()
        if (
            full_path
            and candidate.is_file()
            and str(candidate).startswith(str(_frontend_dist))
        ):
            return FileResponse(candidate)
        return FileResponse(_frontend_dist / "index.html")
