# ServiceOS (Al Mailam Roadmap UI)

> A government-services / project-tracking platform for a Kuwait-based service company: client onboarding, project workspaces, government form submissions, quotations & contracts, payments, tasks, reporting, and an AI assistant — with a real FastAPI + MySQL backend behind it.

**Stack**: Vue 3 + TypeScript + Vite + Tailwind + Pinia (frontend) · FastAPI + SQLAlchemy + MySQL/MariaDB (backend)

---

## Current status

The UI was originally built pass-by-pass against mock data (frontend Passes 01–36, see [`docs/00A-Passes.md`](docs/00A-Passes.md)), then given a real backend (Passes B01–B16, see [`docs/00B-Backend-Passes.md`](docs/00B-Backend-Passes.md)). Both pass sets are complete — every module below is backed by a live API and MySQL, not mock JSON.

Since then work has moved to hardening and bug-fixing driven by code audits rather than new modules:

- **Auth/session security**: refresh tokens moved from `localStorage` to an httpOnly cookie, session-expiry/race-condition fixes, account lockout on repeated failed logins, global per-IP rate limiting, upload content validated against file signature (magic bytes) rather than trusting the extension.
- **Data-integrity fixes**: row-level locking on payment obligation updates to close a lost-update race, real unique IDs for projects/documents created via the frontend (previously client-generated), status-transition handling routed consistently through the workflow engine, a submission-deletion bug replaced with a proper "Withdrawn" status.
- **Feature completions**: a real global Audit Log viewer, a real Activity Calendar (previously 404s) now restyled into the site's design system and wired into Task Management, a working LLM integration for the AI Assistant/document review (Anthropic or DeepSeek, configured via the admin AI Configuration page).
- **UI/theme**: a "light luxurious grey" glassmorphism theme pass, dark-mode contrast fixes, lazy-loaded workspace tabs and wizard steps for performance.
- **Ops**: `install.sh`, an interactive, re-runnable Ubuntu installer that deploys to one of two fixed instances under `/apps` -- `/apps/serviceos` (dev: production build, single pm2 process serving the API and built frontend from one port) or `/apps/alhadi-test` (test: vite dev server, separate pm2 processes for backend/frontend) -- by pulling `main` into the chosen instance and applying any new `backend/migrations/*.sql` files. It never creates a database or writes `backend/.env`; both instances must already have those configured.

The `fix/code-audit-uniform-practices` branch has further in-progress fixes not yet merged to `main`.

### Modules

Dashboard · Client Onboarding (individual/company/organisation/government entity) · Project Explorer & Workspace · Project Timeline · Document Repository & AI Review · Government Forms Library & Submission Workspace · Quotations · Contracts · Task Management · Reports (executive/project/workload) · Customer Status Portal (public, mobile number + project ID) · Notification Centre · Global Search · AI Assistant · Administration (users, roles/permissions, workflow config, government forms admin, AI configuration, company settings) · Activity Calendar · Audit Log

---

## Getting started

### Automated (Ubuntu)

```bash
./install.sh                 # asks: dev or test?
./install.sh --instance=dev  # -> /apps/serviceos
./install.sh --instance=test # -> /apps/alhadi-test
```

Deploys/updates the chosen instance under `/apps` by pulling `main` and applying any pending migrations. Assumes `backend/.env` and the database already exist for that instance -- it never creates a database and never writes `.env`. Safe to re-run.

### Manual

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit DB credentials, JWT secret, etc.
mysql -u root -p -e "CREATE DATABASE almailam DEFAULT CHARSET=utf8mb4;"
mysql -u root -p almailam < schema.sql
python -m scripts.create_admin --quick-start   # creates admin / Admin#99
python -m uvicorn app.main:app --reload
```

**Frontend**
```bash
npm install
npm run dev      # http://localhost:5173, proxies /api to http://localhost:8000
```

> ⚠️ The `admin` / `Admin#99` account created by `--quick-start` is for local development only. Change it (or create a proper admin) before any shared/production use.

AI features (document review, contract summaries, AI Assistant) need a real `ANTHROPIC_API_KEY` or `DEEPSEEK_API_KEY` in `backend/.env` — without one they stay disabled rather than returning fake output. The active provider is chosen in the admin AI Configuration page.

---

## Documentation

Living reference docs are in [`docs/`](docs/): architecture ([`01`](docs/01-Architecture.md)), UI design ([`02`](docs/02-UI-Design-Definition.md)), navigation/routes ([`03`](docs/03-Navigation-Map.md)/[`04`](docs/04-Route-Definitions.md)), component catalog ([`05`](docs/05-Component-Catalog.md)), UX standards & design tokens ([`07`](docs/07-UX-Standards.md)/[`08`](docs/08-Design-Tokens.md)), AI behaviour ([`09`](docs/09-AI-Behaviour.md)), coding standards & naming conventions ([`11`](docs/11-Coding-Standards.md)/[`12`](docs/12-Naming-Conventions.md)).

[`docs/history/`](docs/history/) holds earlier integration write-ups from when the backend was first connected (setup guides, checklists, summaries). They're superseded by the sections above where they conflict, but are kept for historical context.

---

## Contributing

See [`docs/11-Coding-Standards.md`](docs/11-Coding-Standards.md) and [`docs/12-Naming-Conventions.md`](docs/12-Naming-Conventions.md) before opening a PR.
