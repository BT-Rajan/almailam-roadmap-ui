````md
# 02 - UI Design Definition

**Project:** ServiceOS  
**Client:** Almailam Engineering Consultants

---

# Purpose

This document defines the visual language, user experience, interaction patterns and design standards for the entire application.

Every page, component and layout must conform to this document.

No screen should introduce its own visual style.

---

# Design Goals

The application should communicate:

- Professional
- Premium
- Trustworthy
- Modern
- AI-Assisted
- Engineering Focused
- Government Ready
- Simple
- Fast
- Reliable

The application should **not** resemble a traditional ERP.

---

# Design Philosophy

ServiceOS is a **Project-Centric Engineering Platform**.

The interface should help users:

- Find information quickly
- Complete tasks with minimal clicks
- Understand project status immediately
- Access AI assistance naturally
- Navigate without training

---

# Design Language

Style

- Modern Enterprise SaaS
- Minimal
- Clean
- Spacious
- Information rich
- Professional

Avoid

- Busy dashboards
- Heavy gradients
- Flashy animations
- Decorative graphics
- Cluttered screens

---

# Layout Structure

Every page follows a consistent structure.

```
+--------------------------------------------------------------+
| Logo | Search | AI | Notifications | User                   |
+---------------+----------------------------------------------+
| Sidebar       | Breadcrumb                                  |
|               +----------------------------------------------+
|               | Page Header                                 |
|               +----------------------------------------------+
|               | Toolbar                                     |
|               +----------------------------------------------+
|               |                                              |
|               | Main Content                                |
|               |                                              |
|               |                                              |
+---------------+----------------------------------------------+
```

---

# Sidebar

Purpose

Primary navigation.

Characteristics

- Fixed
- Collapsible
- Icon + Label
- Active indicator
- Expandable groups
- Scrollable when required

Navigation

```
Dashboard

Projects

Government Center

Documents

Tasks

Reports

Administration
```

---

# Top Navigation

Contains

- Global Search
- AI Assistant
- Notifications
- User Menu
- Theme Switch
- Language Selector

Height

64px

---

# Page Header

Every page contains

- Title
- Subtitle
- Breadcrumb
- Primary Action
- Secondary Actions

Example

```
Projects

Manage engineering consultancy projects

[New Project]
```

---

# Toolbar

Appears below page header.

May contain

- Search
- Filters
- Sort
- View Switch
- Export
- Refresh

---

# Workspace Pages

Workspace pages are the primary work area.

Structure

```
Project Header

↓

Summary Cards

↓

Workflow Progress

↓

Tabs

↓

Selected Tab Content
```

Tabs

```
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

# Grid System

Desktop

12 Columns

Tablet

8 Columns

Mobile

4 Columns

Maintain consistent spacing.

---

# Spacing

Extra Small

4px

Small

8px

Medium

16px

Large

24px

Section

32px

Page

40px

Never use arbitrary spacing.

---

# Typography

Font

Inter

Fallback

System UI

Hierarchy

H1

Page Title

H2

Section Title

H3

Card Title

Body

Default text

Caption

Secondary information

Use consistent font weights.

---

# Color System

Semantic colors only.

Primary

Blue

Success

Green

Warning

Amber

Danger

Red

Information

Cyan

Neutral

Slate / Gray

Never hardcode colors.

---

# Cards

Cards are the primary content container.

Structure

- Header
- Body
- Optional Footer
- Optional Actions

Use cards consistently.

---

# Buttons

Primary

Filled

Secondary

Outlined

Ghost

Minimal

Danger

Destructive actions

Icon Button

Toolbar actions

Every button supports

- Hover
- Focus
- Disabled
- Loading

---

# Forms

Principles

- Short
- Sectioned
- Logical flow

Every form contains

- Labels
- Validation
- Help Text
- Required Indicator

Never place labels inside inputs.

---

# Smart Tables

All lists use a reusable Smart Table.

Features

- Search
- Filters
- Sorting
- Pagination
- Row Actions
- Bulk Actions
- Status Badges
- Empty State

Used by

- Projects
- Documents
- Forms
- Tasks
- Users

---

# Dialogs

Use dialogs for

- Create
- Edit
- Confirmation
- AI Preview

Do not navigate to separate pages for simple operations.

---

# Drawers

Use right-side drawers for

- AI Assistant
- Preview
- Quick Edit
- Details

---

# AI Experience

AI is embedded across the application.

Every AI interaction follows the same pattern.

```
Prompt

↓

Response

↓

Confidence

↓

Suggested Actions
```

AI appears in

- Projects
- Documents
- Contracts
- Government Forms
- Customer Status

Never create a separate AI application.

---

# Workflow Visualization

Use a reusable workflow stepper.

States

- Not Started
- In Progress
- Waiting
- Approved
- Rejected
- Completed

Display workflow on

- Dashboard
- Project Workspace
- Customer Portal
- Government Submission

---

# Timeline

Single reusable timeline component.

Used for

- Project History
- Activities
- Government Submission
- Customer Status

---

# Status Badges

Consistent colors.

Draft

Blue

Pending

Amber

In Progress

Cyan

Approved

Green

Rejected

Red

Completed

Gray

---

# Dashboard

Dashboard should answer

- What requires attention?
- Which projects are delayed?
- What changed today?
- What should I do next?

Do not overload with charts.

Prioritize operational information.

---

# Government Forms

Display as cards.

Each card shows

- Form Name
- Authority
- Category
- Version
- Language
- Last Updated
- Required Documents
- AI Help

---

# Document Viewer

Split layout.

```
PDF

↓

Metadata

↓

AI Summary

↓

Comments

↓

Version History
```

---

# Customer Portal

Simple interface.

Input

- Mobile Number
- Project ID

Display

- Current Stage
- Progress
- Timeline
- Latest Update
- Pending Customer Action

No unnecessary information.

---

# Search

Global Search available everywhere.

Searches

- Projects
- Documents
- Forms
- Tasks
- Users

Shortcut

Ctrl + K

---

# Notifications

Right-side drawer.

Grouped by

- Today
- Yesterday
- Earlier

Each notification links to the relevant page.

---

# Empty States

Every page requires an empty state.

Include

- Illustration/Icon
- Message
- Primary Action

---

# Loading States

Prefer skeleton loaders.

Avoid blocking the interface.

---

# Error States

Display

- Friendly message
- Retry button

Never expose technical details.

---

# Animations

Use subtle animations.

Allowed

- Fade
- Slide
- Expand

Avoid excessive motion.

---

# Responsive Behaviour

Desktop

Full layout

Tablet

Collapsible sidebar

Mobile

Drawer navigation

No horizontal scrolling.

---

# Accessibility

Support

- Keyboard navigation
- Visible focus
- Proper contrast
- ARIA labels
- Screen readers where applicable

---

# Icons

Use Lucide Icons only.

Rules

- Every menu has an icon
- Every action has an icon
- Use icons consistently
- Avoid decorative icons

---

# Demo Data

Use realistic engineering consultancy data.

Do not use

- Lorem Ipsum
- Demo
- Test
- Client A
- Project 1

Use meaningful names throughout the application.

---

# Reusability Rules

Every repeated UI element must become a reusable component.

Pages compose components.

Components compose smaller components.

Never duplicate layouts.

Never duplicate styles.

---

# Definition of Done

Every page must:

- Match this design language
- Use reusable components
- Be responsive
- Be visually consistent
- Compile successfully
- Work with mock data
- Require only backend integration for production
````
