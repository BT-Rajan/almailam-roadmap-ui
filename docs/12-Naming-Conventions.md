# 12 - Naming Conventions

**Project:** ServiceOS  
**Client:** Almailam Engineering Consultants

**Version:** 1.0

---

# Purpose

This document defines the naming standards used throughout the ServiceOS frontend.

Consistent naming improves readability, maintainability, discoverability and code generation quality.

Every developer and AI coding assistant must follow these conventions.

---

# General Principles

Names should be

- Clear
- Descriptive
- Predictable
- Consistent
- Business-oriented

Avoid abbreviations unless they are industry standards.

Good

```
ProjectWorkspace

GovernmentSubmission

ContractTemplate
```

Avoid

```
Proj

GovFrm

CntTmp
```

---

# Case Standards

| Item | Convention |
|-------|------------|
| Components | PascalCase |
| Pages | PascalCase |
| Interfaces | PascalCase |
| Types | PascalCase |
| Enums | PascalCase |
| Classes | PascalCase |
| Variables | camelCase |
| Functions | camelCase |
| Methods | camelCase |
| Stores | camelCase |
| Services | camelCase |
| Constants | UPPER_SNAKE_CASE |
| CSS Variables | kebab-case |
| Route Paths | kebab-case |
| File Names | PascalCase or camelCase as applicable |
| Folders | kebab-case |

---

# Project Structure

```
src/

assets/

components/

composables/

constants/

layouts/

mock/

pages/

router/

services/

stores/

types/

utils/
```

---

# Component Naming

Pattern

```
<Entity><Purpose>.vue
```

Examples

```
ProjectCard.vue

ProjectHeader.vue

ProjectSummary.vue

TaskCard.vue

StatusBadge.vue

DocumentViewer.vue

GovernmentFormCard.vue

WorkflowStepper.vue
```

Avoid

```
Card1.vue

Test.vue

Demo.vue

Component.vue
```

---

# Page Naming

Pattern

```
<Entity>Page.vue
```

Examples

```
LoginPage.vue

DashboardPage.vue

ProjectsPage.vue

ProjectWorkspacePage.vue

DocumentViewerPage.vue

ReportsPage.vue

SettingsPage.vue
```

---

# Layout Naming

Pattern

```
<Name>Layout.vue
```

Examples

```
AuthLayout.vue

DashboardLayout.vue

CustomerLayout.vue
```

---

# Store Naming

Pattern

```
<Entity>Store.ts
```

Examples

```
projectStore.ts

taskStore.ts

documentStore.ts

userStore.ts

settingsStore.ts
```

Store identifier

```
useProjectStore()

useTaskStore()

useUserStore()
```

---

# Service Naming

Pattern

```
<Entity>Service.ts
```

Examples

```
projectService.ts

documentService.ts

taskService.ts

aiService.ts
```

---

# Composable Naming

Pattern

```
use<Entity>.ts
```

Examples

```
useDialog.ts

usePagination.ts

useSearch.ts

useWorkflow.ts

useTheme.ts
```

---

# Utility Naming

Pattern

```
<functionality>.ts
```

Examples

```
dateFormatter.ts

currencyFormatter.ts

validators.ts

fileHelpers.ts
```

---

# Type Naming

Pattern

```
<Entity>.ts
```

Examples

```
Project.ts

Task.ts

Document.ts

GovernmentForm.ts
```

---

# Interface Naming

```
Project

Client

Task

Document

Notification

GovernmentForm
```

Avoid

```
IProject

ITask

IDocument
```

---

# Enum Naming

Pattern

```
<Entity>Enum
```

Examples

```
ProjectStatusEnum

TaskPriorityEnum

UserRoleEnum

WorkflowStageEnum
```

---

# Function Naming

Functions should begin with verbs.

Examples

```
loadProjects()

createProject()

updateTask()

deleteDocument()

searchProjects()

filterDocuments()

calculateProgress()

generateSummary()

validateForm()
```

Avoid

```
project()

task()

doStuff()

test()

run()
```

---

# Boolean Naming

Always begin with

```
is

has

can

should
```

Examples

```
isActive

isLoading

hasPermission

canEdit

shouldRefresh
```

---

# Variable Naming

Good

```
project

projectList

selectedProject

filteredProjects

activeWorkflow

currentUser

pendingTasks
```

Avoid

```
p

obj

item

list

data

temp
```

---

# Constant Naming

Use

```
UPPER_SNAKE_CASE
```

Examples

```
DEFAULT_PAGE_SIZE

MAX_UPLOAD_SIZE

DEFAULT_TIMEOUT

APPLICATION_NAME

API_TIMEOUT
```

---

# Route Naming

Route names

```
dashboard

projects

project-workspace

documents

government-forms

tasks

reports

settings
```

Route paths

```
/dashboard

/projects

/projects/:projectId

/documents

/tasks

/admin/users
```

---

# CSS Variable Naming

```
--primary-color

--border-radius

--shadow-small

--font-size-large

--spacing-medium
```

---

# Tailwind Classes

Order

```
Layout

Spacing

Sizing

Typography

Colors

Borders

Effects

Transitions
```

Example

```
flex items-center
gap-4
w-full
text-sm font-medium
text-slate-700
border rounded-lg
shadow-sm
transition
```

---

# Event Naming

Events should describe actions.

Examples

```
save

cancel

delete

close

open

select

submit

refresh

search
```

Avoid

```
click

event

run

execute
```

---

# Dialog Naming

```
DeleteProjectDialog

UploadDocumentDialog

TaskDialog

UserDialog
```

---

# Drawer Naming

```
AIAssistantDrawer

NotificationDrawer

PreviewDrawer

DetailsDrawer
```

---

# Mock Data Files

Pattern

```
clients.ts

projects.ts

documents.ts

tasks.ts

forms.ts

users.ts
```

---

# Icon Naming

Match business meaning.

Examples

```
Folder

Building

Clipboard

FileText

Users

Shield

Search

Bot
```

Avoid decorative icons.

---

# Asset Naming

Images

```
logo.svg

logo-dark.svg

avatar-default.png

empty-projects.svg
```

---

# Git Branch Naming

Pattern

```
feature/login

feature/dashboard

feature/projects

feature/documents

feature/tasks

bugfix/search

refactor/components
```

---

# Commit Message Format

Pattern

```
type: description
```

Types

```
feat

fix

refactor

style

docs

test

build

chore
```

Examples

```
feat: add project workspace

feat: create reusable smart table

fix: resolve sidebar navigation

refactor: simplify project card

docs: update UX standards
```

---

# Folder Naming

Always

```
kebab-case
```

Examples

```
project-management

government-center

customer-portal

shared-components
```

---

# Reserved Words

Do not use

```
temp

newData

abc

xyz

sample

dummy

test

component

page

object

data
```

Use meaningful business names instead.

---

# Business Terminology

Use consistent terminology throughout the application.

Always use

- Project
- Client
- Document
- Government Form
- Government Submission
- Contract
- Quotation
- Task
- Workflow
- Timeline
- Authority
- Engineer
- AI Assistant

Never mix equivalent terms such as

- Customer / Client
- File / Document
- Job / Project
- Employee / User

One business term should have one canonical name.

---

# Naming Checklist

Every new item should satisfy the following:

✓ Business meaningful

✓ Self-explanatory

✓ Consistent with existing naming

✓ No abbreviations

✓ Correct casing

✓ Predictable location

✓ Easy to search

✓ Easy for AI code generation

---

# Success Criteria

A new developer should be able to understand the purpose of any file, folder, component, service, store, function or variable simply by reading its name. Naming should remain consistent across the entire codebase, making the project easy to navigate, maintain and extend over many years.