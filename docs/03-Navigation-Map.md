````md
# 03 - Navigation Map

**Project:** ServiceOS  
**Client:** Almailam Engineering Consultants

---

# Purpose

This document defines the complete navigation hierarchy of the ServiceOS frontend.

Every page must be reachable through the application's navigation.

Users should never encounter dead ends or orphan pages.

Navigation must remain simple, predictable and project-centric.

---

# Navigation Principles

- Maximum 3 clicks to reach any feature
- Every page has a breadcrumb
- Every workspace returns to its parent
- Primary navigation remains fixed
- Secondary navigation appears only inside workspaces
- Minimize context switching

---

# Primary Navigation

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

# Navigation Hierarchy

```text
Login
│
└── Dashboard
    │
    ├── Projects
    │   │
    │   ├── Project Explorer
    │   │
    │   ├── New Project Wizard
    │   │
    │   └── Project Workspace
    │       │
    │       ├── Overview
    │       ├── Timeline
    │       ├── Documents
    │       ├── Design
    │       ├── Government
    │       ├── Quotation
    │       ├── Contract
    │       ├── Tasks
    │       └── Activity
    │
    ├── Government Center
    │   │
    │   ├── Government Forms Library
    │   │
    │   ├── Authority Directory
    │   │
    │   └── Government Submission Workspace
    │
    ├── Documents
    │   │
    │   ├── Document Repository
    │   │
    │   ├── Document Viewer
    │   │
    │   └── AI Document Review
    │
    ├── Tasks
    │   │
    │   ├── Task Board
    │   │
    │   └── My Tasks
    │
    ├── Reports
    │   │
    │   └── Dashboard Reports
    │
    └── Administration
        │
        ├── User Management
        ├── Workflow Configuration
        ├── Government Forms Management
        ├── AI Configuration
        └── Company Settings
```

---

# Global Navigation

Available from every page.

```text
Logo

Dashboard

Sidebar

Global Search

AI Assistant

Notifications

User Menu
```

---

# Project Navigation

```text
Project Explorer

↓

Select Project

↓

Project Workspace

↓

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

The Project Workspace is the primary operational screen.

Users should remain inside this workspace for most project activities.

---

# Government Navigation

```text
Government Center

↓

Government Forms Library

↓

Select Form

↓

Preview

↓

AI Help

↓

Download
```

---

```text
Government Center

↓

Government Submission Workspace

↓

Submission Details

↓

Required Documents

↓

Officer Comments

↓

Approval Timeline
```

---

# Document Navigation

```text
Documents

↓

Repository

↓

Document Viewer

↓

AI Review

↓

Version History
```

---

# Task Navigation

```text
Tasks

↓

Task Board

↓

Task Details

↓

Update Status
```

---

```text
Tasks

↓

My Tasks

↓

Task Details
```

---

# Administration Navigation

```text
Administration

│

├── User Management

├── Workflow Configuration

├── Government Forms Management

├── AI Configuration

└── Company Settings
```

Each administration module is independent.

---

# Customer Portal Navigation

The Customer Portal is intentionally separate from the internal application.

```text
Project Status Tracker

↓

Enter

• Mobile Number
• Project ID

↓

Search

↓

Project Status

↓

Timeline

↓

Latest Update
```

No login required.

---

# AI Navigation

AI is available from every major workspace.

```text
Projects

↓

AI Drawer

↓

Prompt

↓

Response

↓

Suggested Actions
```

Also available in

- Document Viewer
- Government Forms
- Contracts
- Customer Status

AI never navigates away from the current page.

It always opens as a right-side drawer.

---

# Search Navigation

Global Search

```text
Ctrl + K

↓

Search Overlay

↓

Projects

Documents

Forms

Tasks

Users

↓

Navigate directly
```

---

# Notification Navigation

```text
Notification Icon

↓

Notification Drawer

↓

Select Notification

↓

Navigate to Related Screen
```

---

# Breadcrumb Examples

## Dashboard

```text
Dashboard
```

---

## Projects

```text
Dashboard

>

Projects
```

---

## Project Workspace

```text
Dashboard

>

Projects

>

Project Name
```

---

## Government Submission

```text
Dashboard

>

Projects

>

Project Name

>

Government
```

---

## Document Viewer

```text
Dashboard

>

Documents

>

Document Name
```

---

## AI Review

```text
Dashboard

>

Documents

>

AI Review
```

---

## User Management

```text
Dashboard

>

Administration

>

Users
```

---

# Navigation Rules

Every page must provide:

- Back navigation where appropriate
- Breadcrumb navigation
- Sidebar navigation
- Consistent page title
- Primary action button
- Access to AI Assistant
- Access to Notifications
- Access to Global Search

---

# Navigation Constraints

Do not create:

- Deep navigation trees
- Hidden menus
- More than one level of sidebar nesting
- Dead-end pages
- Duplicate navigation paths

---

# Success Criteria

A first-time user should be able to:

1. Log in
2. Open Dashboard
3. Locate a Project
4. Review Documents
5. View Government Forms
6. Track Tasks
7. Configure the System
8. Find any page within three clicks

The navigation should feel intuitive, consistent, and require minimal training.
````
