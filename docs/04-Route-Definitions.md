````md
# 04 - Route Definitions

**Project:** ServiceOS  
**Client:** Almailam Engineering Consultants

---

# Purpose

This document defines every frontend route in the application.

It is the single source of truth for Vue Router configuration.

Every page must have exactly one route.

Routes should remain stable throughout the project.

---

# Route Design Principles

- Short URLs
- Human readable
- REST-like structure
- No technology-specific names
- Lowercase
- Hyphen separated
- Predictable hierarchy

Example

```
/projects
/projects/new
/projects/PRJ-0001
```

Avoid

```
/projectpage
/project_details
/project123
```

---

# Route Structure

```
/

↓

Login

↓

Dashboard

↓

Business Modules

↓

Administration
```

---

# Public Routes

| Route | Page |
|--------|------|
| `/` | Login |
| `/login` | Login |
| `/status` | Customer Project Status Tracker |

---

# Protected Routes

## Dashboard

| Route | Page |
|--------|------|
| `/dashboard` | Executive Dashboard |

---

## Projects

| Route | Page |
|--------|------|
| `/projects` | Project Explorer |
| `/projects/new` | New Project Wizard |
| `/projects/:projectId` | Project Workspace |

---

## Clients

| Route | Page |
|--------|------|
| `/clients` | Client Explorer |
| `/clients/new` | New Client Onboarding Wizard |
| `/clients/:clientId` | Client Workspace |

---

## Project Workspace Tabs

Tabs remain within the same page.

```
/projects/:projectId
```

Active tab is controlled by the frontend.

Available tabs

- Overview
- Timeline
- Documents
- Design
- Government
- Quotation
- Contract
- Tasks
- Activity

No additional routes are required.

---

## Government Center

| Route | Page |
|--------|------|
| `/government/forms` | Government Forms Library |
| `/government/authorities` | Authority Directory |
| `/government/submissions` | Government Submission Workspace |

---

## Documents

| Route | Page |
|--------|------|
| `/documents` | Document Repository |
| `/documents/:documentId` | Document Viewer |
| `/documents/:documentId/review` | AI Document Review |

---

## Tasks

| Route | Page |
|--------|------|
| `/tasks` | Task Board |
| `/tasks/my` | My Tasks |

---

## Reports

| Route | Page |
|--------|------|
| `/reports` | Dashboard Reports |

---

## Administration

| Route | Page |
|--------|------|
| `/admin/users` | User Management |
| `/admin/workflows` | Workflow Configuration |
| `/admin/forms` | Government Forms Management |
| `/admin/ai` | AI Configuration |
| `/admin/company` | Company Settings |

---

# Global Components

These are available on every protected route.

- Sidebar
- Top Navigation
- Breadcrumb
- AI Assistant Drawer
- Notifications
- User Menu
- Global Search

---

# Route Parameters

## Project

```
/projects/:projectId
```

Example

```
/projects/PRJ-2026-001
```

---

## Document

```
/documents/:documentId
```

Example

```
/documents/DOC-2026-015
```

---

# Route Guards

Prototype

Use mock authentication.

```
Login

↓

Authenticated

↓

Dashboard
```

Unauthenticated users

↓

Redirect to Login.

No backend authentication.

---

# Navigation Flow

```
Login

↓

Dashboard

↓

Projects

↓

Project Workspace

↓

Documents

↓

AI Review
```

---

```
Dashboard

↓

Government Forms

↓

Preview Form

↓

AI Help
```

---

```
Dashboard

↓

Tasks

↓

Task Board

↓

Task Details
```

---

```
Dashboard

↓

Administration

↓

Configuration
```

---

# Breadcrumb Mapping

| Route | Breadcrumb |
|--------|------------|
| `/dashboard` | Dashboard |
| `/projects` | Dashboard > Projects |
| `/projects/:projectId` | Dashboard > Projects > Project |
| `/clients` | Dashboard > Clients |
| `/clients/new` | Dashboard > Clients > New Client |
| `/clients/:clientId` | Dashboard > Clients > Client |
| `/government/forms` | Dashboard > Government Center > Forms |
| `/government/submissions` | Dashboard > Government Center > Submissions |
| `/documents` | Dashboard > Documents |
| `/documents/:documentId` | Dashboard > Documents > Viewer |
| `/documents/:documentId/review` | Dashboard > Documents > AI Review |
| `/tasks` | Dashboard > Tasks |
| `/tasks/my` | Dashboard > Tasks > My Tasks |
| `/reports` | Dashboard > Reports |
| `/admin/users` | Dashboard > Administration > Users |
| `/admin/workflows` | Dashboard > Administration > Workflows |
| `/admin/forms` | Dashboard > Administration > Forms |
| `/admin/ai` | Dashboard > Administration > AI |
| `/admin/company` | Dashboard > Administration > Company |

---

# Future API Mapping

The frontend routes are independent of backend endpoints.

Example

| Frontend Route | Future API |
|----------------|------------|
| `/projects` | `/api/projects` |
| `/projects/:projectId` | `/api/projects/{id}` |
| `/clients` | `/api/clients` |
| `/clients/:clientId` | `/api/clients/{id}` |
| `/documents` | `/api/documents` |
| `/government/forms` | `/api/forms` |
| `/tasks` | `/api/tasks` |

Changing backend URLs must not require changing frontend routes.

---

# Error Routes

| Route | Purpose |
|--------|---------|
| `/404` | Page Not Found |
| `*` | Redirect to 404 |

---

# URL Guidelines

Always use

- Lowercase
- Hyphens where needed
- Stable resource identifiers
- Meaningful route names

Never use

- Spaces
- Underscores
- File extensions
- Random IDs in URLs
- Query parameters for primary navigation

---

# Route Naming Convention

| Route Name | Path |
|------------|------|
| login | `/login` |
| dashboard | `/dashboard` |
| projects | `/projects` |
| project-new | `/projects/new` |
| project-workspace | `/projects/:projectId` |
| clients | `/clients` |
| client-new | `/clients/new` |
| client-workspace | `/clients/:clientId` |
| government-forms | `/government/forms` |
| government-authorities | `/government/authorities` |
| government-submissions | `/government/submissions` |
| documents | `/documents` |
| document-viewer | `/documents/:documentId` |
| document-review | `/documents/:documentId/review` |
| tasks | `/tasks` |
| my-tasks | `/tasks/my` |
| reports | `/reports` |
| admin-users | `/admin/users` |
| admin-workflows | `/admin/workflows` |
| admin-forms | `/admin/forms` |
| admin-ai | `/admin/ai` |
| admin-company | `/admin/company` |
| customer-status | `/status` |

---

# Success Criteria

The routing system must:

- Keep URLs clean and predictable.
- Allow every feature to be reached within three clicks.
- Support browser refresh without losing context.
- Be independent of backend API design.
- Require minimal changes when real services replace mock data.
- Provide a stable foundation for future frontend and backend development.
````
