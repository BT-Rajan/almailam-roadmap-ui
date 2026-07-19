````md
# ServiceOS Frontend UI Prototype - Master Prompt

## Project

Develop a **production-quality Vue 3 frontend prototype** for **ServiceOS**, an AI-assisted engineering consulting platform for **Almailam**, a consulting firm that manages engineering projects from customer enquiry through government approvals to project completion.

This is **not** a wireframe.

The prototype must look and behave like a finished commercial application. The only missing piece should be backend integration.

---

# Objective

Create a fully navigable frontend that enables Almailam's management to experience the complete product before backend development begins.

The prototype will later integrate with a Python backend by replacing mock services with real API calls.

Nothing developed during this phase should be discarded.

---

# Business Context

Almailam manages engineering consultancy projects involving:

- Customer enquiries
- Quotations
- Contracts
- Engineering design
- Technical document collection
- Government authority submissions
- Municipality comments
- Revisions
- Approvals
- Project completion

The application must be **Project-Centric**.

Every business function revolves around a Project.

---

# Primary Business Problems

The UI must clearly demonstrate solutions for these problems.

### 1. Project Visibility

Customers repeatedly call asking for project status.

Provide a public Project Status Tracker where a customer enters:

- Mobile Number
- Project ID

and sees

- Current Status
- Current Stage
- Progress
- Timeline
- Latest Update
- Pending Customer Action

---

### 2. Government Forms

Government work requires numerous forms from different authorities.

Provide a Government Forms Library with:

- Categories
- Search
- Preview
- Download
- Version
- Required Documents
- Authority
- AI Help

---

### 3. AI Assistance

AI should be integrated throughout the application.

Examples:

Projects

- Summarize project
- Suggest next action
- Detect missing documents

Documents

- Extract fields
- Summarize
- Translate
- Validate

Contracts

- Generate draft
- Rewrite clauses
- Summarize

Government Forms

- Explain purpose
- List required documents
- Explain how to complete

Customer Portal

- Generate customer-friendly status updates

Use mock AI responses only.

---

# Technology Stack

- Vue 3
- Vite
- Vue Router
- Pinia
- TypeScript
- Composition API
- `<script setup>`
- Tailwind CSS
- Lucide Icons

No backend.

No database.

No authentication implementation.

Use mock JSON services only.

---

# Architecture Principles

- Project-centric UI
- Component-first architecture
- Maximum reuse
- Thin pages
- Configurable components
- Responsive
- Production-ready structure

---

# Development Rules

1. Never duplicate UI.
2. Create reusable components whenever functionality is shared.
3. Pages compose components only.
4. No business logic inside pages.
5. No placeholder text.
6. Use realistic engineering consultancy data.
7. Keep the prototype lightweight.
8. Every page must compile successfully.
9. Every page must be fully navigable.
10. Only implement the requested development pass.

---

# Folder Structure

```text
src/
 ├── assets/
 ├── components/
 ├── composables/
 ├── layouts/
 ├── mock/
 ├── pages/
 ├── router/
 ├── services/
 ├── stores/
 ├── styles/
 ├── types/
 └── utils/
```

---

# Layouts

## Authentication Layout

- Login

---

## Dashboard Layout

- Dashboard

---

## Smart List Layout

Reusable for

- Projects
- Documents
- Forms
- Tasks
- Reports
- Users

---

## Workspace Layout

Reusable for

- Project
- Government Submission
- Document Review

---

## Administration Layout

Reusable for

- Administration
- Configuration

---

# Navigation

```text
Dashboard

Projects

Government Center

Documents

Tasks

Reports

Administration
```

---

# Pages

## Authentication

- Login

---

## Dashboard

- Executive Dashboard

---

## Projects

- Project Explorer
- New Project Wizard
- Project Workspace

Project Workspace Tabs

```text
Overview
Timeline
Documents
Design
Government
Quotation
Contract
Tasks
Activity
```

---

## Government Center

- Government Forms Library
- Government Submission Workspace
- Authority Directory

---

## Documents

- Document Repository
- Document Viewer
- AI Document Review

---

## Tasks

- Task Board
- My Tasks

---

## Customer Portal

- Project Status Tracker

---

## Reports

- Dashboard Reports

---

## Administration

- User Management
- Workflow Configuration
- Government Forms Management
- AI Configuration
- Company Settings

---

# Global UI

Available throughout the application.

- Sidebar
- Top Navigation
- Breadcrumb
- Global Search
- Notifications
- AI Assistant Drawer
- User Menu

---

# Reusable Components

## Navigation

- Sidebar
- Topbar
- Breadcrumb

## Common

- Button
- Card
- SmartTable
- SmartForm
- FilterBar
- Search
- Tabs
- Dialog
- Drawer
- StatusBadge
- ProgressBar
- Timeline
- ActivityFeed
- Comments
- Attachments
- EmptyState
- Loader
- Toast

## Dashboard

- KPI Card
- Statistics Card
- Chart Widget
- Recent Activity

## Project

- Project Header
- Workflow Stepper
- Milestone Card

## Documents

- File Uploader
- PDF Viewer
- Metadata Panel
- Version History

## Government

- Form Card
- Submission Timeline
- Authority Card

## AI

- AI Assistant Drawer
- AI Response Card
- Confidence Badge

## Tasks

- Kanban Board
- Calendar View
- Task Card

---

# Dialogs

- New Project
- Upload Document
- Add Task
- Add Comment
- Update Workflow Stage
- AI Review
- Generate Contract
- Generate Status Update
- Download Form
- User Profile

---

# Demo Data

Keep demo data intentionally small.

## Clients

5 Clients

## Projects

5 Projects

One project in each major lifecycle stage.

## Documents

10 Documents

## Government Forms

8 Forms

## Tasks

10 Tasks

## Users

5 Users

Administrator

Project Manager

Engineer

Document Controller

Viewer

## Authorities

5 Authorities

Municipality

Fire Department

Electricity

Water

Environment

## Quotations

3 Quotations

## Contracts

3 Contracts

## Workflow Templates

3 Templates

## Reports

3 Reports

## Notifications

8 Notifications

## AI Responses

5 Mock AI responses

## Customer Status Records

3 Sample records

Maintain realistic relationships between all records.

---

# UI Design

Target a premium enterprise look.

Requirements

- Clean layout
- Spacious design
- Modern typography
- Soft shadows
- Rounded corners
- Professional icons
- Consistent spacing
- Responsive
- Light/Dark mode ready
- Smooth transitions

---

# Development Workflow

Implement the project one pass at a time.

Each pass must:

- Compile successfully
- Preserve existing functionality
- Avoid breaking previous passes
- Maintain reusable architecture

Do not implement future passes.

---

# End of Every Pass

Run:

```bash
npm run build
```

Run:

```bash
npm run lint
```

Verify:

- Build succeeds
- Navigation works
- No broken imports
- No console errors

Commit:

```bash
git add .
git commit -m "<meaningful commit message>"
git push origin vue-frontend
```

---

# Response Format

At the beginning of every response provide:

```text
Phase
Pass
Objective
Deliverables
```

At the end provide:

```text
Files Created
Files Modified
Build Status
Git Commit Message
Next Pass
```

---

# Scope Control

Only implement the requested pass.

Do not:

- modify unrelated files
- start future passes
- perform unrelated refactoring
- introduce backend code
- create database code

---

# Success Criteria

The completed prototype should enable Almailam's stakeholders to navigate every major workflow—from project creation through government submission to customer status tracking—with realistic data and interactions. It should feel like a finished application awaiting backend integration, providing confidence in both the user experience and the overall product direction.
````
