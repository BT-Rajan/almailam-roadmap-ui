from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.auth import router as auth_router
from app.api.ai import router as ai_router
from app.api.activity import my_router as my_activity_router
from app.api.activity import router as activity_router
from app.api.audit_logs import router as audit_logs_router
from app.api.clients import router as clients_router
from app.api.company import router as company_router
from app.api.contracts import router as contracts_router
from app.api.dashboard import router as dashboard_router
from app.api.document_templates import router as document_templates_router
from app.api.documents import router as documents_router
from app.api.email import router as email_router
from app.api.email_templates import router as email_templates_router
from app.api.government import router as government_router
from app.api.knowledge import router as knowledge_router
from app.api.messages import router as messages_router
from app.api.notifications import router as notifications_router
from app.api.payments import router as payments_router
from app.api.project_forms import router as project_forms_router
from app.api.project_link_documents import router as project_link_documents_router
from app.api.projects import router as projects_router
from app.api.quotations import router as quotations_router
from app.api.reports import router as reports_router
from app.api.roles import router as roles_router
from app.api.scheduled_reports import router as scheduled_reports_router
from app.api.search import router as search_router
from app.api.server_time import router as server_time_router
from app.api.document_requirements import router as document_requirements_router
from app.api.permit_catalog import router as permit_catalog_router
from app.api.service_catalog import router as service_catalog_router
from app.api.site_portal import router as site_portal_router
from app.api.status_reports import router as status_reports_router
from app.api.submissions import router as submissions_router
from app.api.tasks import router as tasks_router
from app.api.users import router as users_router
from app.core.config import get_settings
from app.core.database import engine
from app.core.exceptions import register_exception_handlers
from app.core.middleware import RateLimitMiddleware, SecurityHeadersMiddleware

settings = get_settings()

# Background jobs (daily staleness checks, scheduled reports) are not run
# here -- they are separate processes started by systemd, so the API owns
# no scheduler no matter how many workers it runs. See app/jobs/ and
# deploy/systemd/.
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
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
app.include_router(service_catalog_router)
app.include_router(permit_catalog_router)
app.include_router(document_requirements_router)
app.include_router(roles_router)
app.include_router(clients_router)
app.include_router(dashboard_router)
app.include_router(company_router)
app.include_router(projects_router)
app.include_router(government_router)
app.include_router(knowledge_router)
app.include_router(submissions_router)
app.include_router(quotations_router)
app.include_router(contracts_router)
app.include_router(payments_router)
app.include_router(documents_router)
app.include_router(email_router)
app.include_router(email_templates_router)
app.include_router(document_templates_router)
app.include_router(project_link_documents_router)
app.include_router(project_forms_router)
app.include_router(tasks_router)
app.include_router(notifications_router)
app.include_router(reports_router)
app.include_router(scheduled_reports_router)
app.include_router(messages_router)
app.include_router(search_router)
app.include_router(server_time_router)
app.include_router(site_portal_router)
app.include_router(status_reports_router)


@app.get("/api/health")
def health_check():
    """Up AND able to reach the database -- install.sh fails a deploy on
    anything else. 503 (not 500) so it reads as "not ready"."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={"status": "database unavailable", "env": settings.ENV})
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

# Caching policy for the built frontend.
#
# Vite content-hashes every file it writes into /assets (index-Bc_cXs8I.js),
# so a given URL never changes: a browser can keep it forever and never ask
# again. Without this the browser has only ETag/Last-Modified to go on and
# revalidates each of the ~190 chunks on every visit.
#
# index.html is the opposite: it is the one file whose URL is fixed while its
# content changes on every deploy (it names the new hashed files), so it must
# always be revalidated. "no-cache" means "ask the server before reusing",
# not "don't store". (The catch-all route below returns a plain FileResponse,
# which re-sends the file rather than answering 304 -- fine for a ~1 KB
# index.html, and the reason this must never be applied to /assets.)
_IMMUTABLE_CACHE_CONTROL = "public, max-age=31536000, immutable"
_REVALIDATE_CACHE_CONTROL = "no-cache"


class _HashedAssetFiles(StaticFiles):
    """StaticFiles that marks every response (including 304s) as immutable.
    Only mount this on a directory whose filenames are content-hashed."""

    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = _IMMUTABLE_CACHE_CONTROL
        return response


if _frontend_dist.is_dir():
    _assets_dir = _frontend_dist / "assets"
    if _assets_dir.is_dir():
        app.mount("/assets", _HashedAssetFiles(directory=_assets_dir), name="frontend-assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str) -> FileResponse:
        candidate = (_frontend_dist / full_path).resolve()
        # is_relative_to, not a str.startswith prefix check: a bare string
        # prefix has no path-separator boundary, so a sibling directory
        # such as "dist-backup" would pass "...dist-backup".startswith("...dist").
        if full_path and candidate.is_file() and candidate.is_relative_to(_frontend_dist):
            # Unhashed files served from the dist root (favicon, static
            # pages): revalidate rather than assume they never change.
            return FileResponse(candidate, headers={"Cache-Control": _REVALIDATE_CACHE_CONTROL})
        # This route only matches because it's a catch-all -- FastAPI
        # falls through to it for any path that didn't hit one of the
        # real /api/* routes registered above, INCLUDING a genuinely
        # unmatched/mistyped API path, not just real frontend routes.
        # Without this check, e.g. a typo'd endpoint URL or a future
        # frontend/backend route mismatch would silently get back
        # index.html with 200 OK instead of a 404 -- the comment above
        # this block ("every /api/* route above still wins") wasn't
        # actually true for that case. A JSON fetch() client parsing
        # that 200 response as JSON hits a raw, confusing "Unexpected
        # token '<'" console error instead of a clean handled 404.
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found.")
        return FileResponse(_frontend_dist / "index.html", headers={"Cache-Control": _REVALIDATE_CACHE_CONTROL})
