````md
# 01 - Frontend Architecture

**Project:** ServiceOS  
**Client:** Almailam Engineering Consultants

---

# Purpose

This document defines the frontend architecture for ServiceOS.

It is the architectural contract for all future development.

Every development pass must conform to this document.

---

# Objectives

The frontend must be:

- Production ready
- Component driven
- Highly reusable
- Easily maintainable
- Easy to extend
- Responsive
- Backend independent
- Easy to integrate with Python REST APIs

Nothing developed during the prototype phase should be discarded.

---

# Technology Stack

| Item | Technology |
|-------|------------|
| Framework | Vue 3 |
| Build Tool | Vite |
| Language | TypeScript |
| Router | Vue Router |
| State | Pinia |
| Styling | Tailwind CSS |
| Icons | Lucide Icons |
| Charts | ApexCharts |
| Forms | Vue Components |
| HTTP | Axios (future integration only) |

During prototype development all data comes from mock JSON.

---

# High Level Architecture

```
User

↓

Vue Router

↓

Layout

↓

Page

↓

Reusable Components

↓

Pinia Store

↓

Mock Service Layer

↓

Mock JSON Data
```

When backend development begins

```
Mock Service

↓

REST API

↓

Python Backend
```

No page should require modification.

Only the service implementation changes.

---

# Folder Structure

```
src/

├── assets/
│
├── components/
│   ├── common/
│   ├── dashboard/
│   ├── project/
│   ├── document/
│   ├── government/
│   ├── task/
│   ├── ai/
│   ├── report/
│   └── admin/
│
├── composables/
│
├── layouts/
│
├── mock/
│
├── pages/
│
├── router/
│
├── services/
│
├── stores/
│
├── styles/
│
├── types/
│
└── utils/
```

---

# Architectural Layers

## Layer 1

Layouts

Responsible for

- Sidebar
- Header
- Breadcrumb
- Footer
- Page Container

No business logic.

---

## Layer 2

Pages

Responsible for

- Route
- Page composition
- Page level events

Pages should remain small.

Target

Less than 250 lines.

Pages never contain duplicated UI.

---

## Layer 3

Components

Contain

- Business UI
- Tables
- Forms
- Cards
- Timeline
- Workflow
- Charts

Everything reusable belongs here.

---

## Layer 4

Stores

Pinia stores manage

- User
- Theme
- Navigation
- Notifications
- Dashboard
- Projects
- Documents
- Government
- Tasks

Stores never call APIs directly.

---

## Layer 5

Services

Responsible for

- Loading data
- Saving data
- Search
- Filtering

Prototype

↓

Mock JSON

Production

↓

REST API

---

# Routing Strategy

Every menu item has a route.

Nested routing where appropriate.

Example

```
Projects

↓

Project Workspace

↓

Tabs
```

Tabs are page components.

Not routes.

---

# Layout Strategy

Five layouts only.

## Authentication Layout

Used for

- Login

---

## Dashboard Layout

Used for

- Dashboard

---

## List Layout

Reusable

- Projects
- Documents
- Forms
- Tasks
- Reports
- Users

---

## Workspace Layout

Reusable

- Project
- Government Submission
- Document Review

---

## Administration Layout

Reusable

- Administration
- Configuration

---

# Component Strategy

Components must be:

- Independent
- Configurable
- Typed
- Reusable

Never duplicate UI.

If used twice

↓

Create component.

---

# State Management

Use Pinia.

Separate stores.

Example

```
ProjectStore

DocumentStore

TaskStore

GovernmentStore

UserStore

NotificationStore

ThemeStore
```

Keep stores focused.

---

# Data Flow

```
Page

↓

Store

↓

Service

↓

Mock JSON
```

Never

```
Page

↓

Mock JSON
```

---

# Mock Service Layer

Every module has a service.

Example

```
ProjectService

DocumentService

TaskService

GovernmentService
```

Initially

Returns mock JSON.

Later

Returns API response.

No page changes required.

---

# Reusability Rules

Create reusable components for

- Tables
- Forms
- Search
- Filters
- Dialogs
- Drawers
- Cards
- Status badges
- Timeline
- Workflow
- AI Panel
- Charts

No duplicated implementation.

---

# Navigation Model

```
Dashboard

Projects

Government Center

Documents

Tasks

Reports

Administration
```

Simple.

Flat.

Easy to learn.

---

# Page Model

Every page follows

```
Header

↓

Summary

↓

Toolbar

↓

Main Content

↓

Dialogs
```

Consistent across application.

---

# AI Integration

AI is embedded.

Never a separate application.

AI available from

- Projects
- Documents
- Government Forms
- Contracts
- Customer Status

Always via reusable AI Drawer.

---

# Government Forms

Government Forms are first-class entities.

Not attachments.

Each form has

- Metadata
- Version
- Category
- Authority
- Instructions
- Required Documents

---

# Customer Portal

Separate lightweight frontend.

Purpose

Project Status Tracking.

Input

- Mobile Number
- Project ID

Output

- Current Stage
- Timeline
- Progress
- Latest Update

No login required.

---

# Error Handling

Pages never crash.

Display

- Empty State
- Error State
- Retry

Never expose technical errors.

---

# Performance

Prefer

- Lazy loaded pages
- Small components
- Shared layouts
- Shared stores

Avoid unnecessary re-rendering.

---

# Coding Principles

- Composition API
- Script Setup
- Strong typing
- Single Responsibility
- DRY
- KISS
- No inline CSS
- No duplicated logic

---

# Build Requirements

Application must always

- Compile successfully
- Build successfully
- Lint successfully

Every pass ends with a working application.

---

# Git Workflow

Every pass

```
Implement

↓

Build

↓

Lint

↓

Review

↓

Commit

↓

Push

↓

Stop
```

One pass.

One commit.

One push.

---

# Architecture Constraints

Never

- Duplicate components
- Duplicate layouts
- Hardcode business logic
- Access mock JSON directly from pages
- Mix UI with data access
- Introduce backend code
- Create large monolithic components

---

# Success Criteria

The frontend architecture must support:

- Rapid feature development
- High component reuse
- Simple backend integration
- Long-term maintainability
- Production deployment with minimal refactoring

The only change required for production should be replacing the mock service layer with Python REST API calls.
````
