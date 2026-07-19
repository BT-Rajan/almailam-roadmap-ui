# 15 - Claude Rules

**Project:** ServiceOS  
**Client:** Almailam Engineering Consultants

**Frontend Technology**

- Vue 3
- Vite
- TypeScript
- Pinia
- Vue Router
- Tailwind CSS
- Lucide Icons

---

# Purpose

This document defines the mandatory implementation rules for Claude Code while generating the ServiceOS frontend.

Claude should behave like a senior software architect building a production-quality application—not a prototype generator.

Every generated file should be suitable for production after backend integration.

---

# Primary Objective

Build a **fully navigable Vue application** that appears complete using mock data.

The frontend should require only the replacement of the mock service layer with Python REST APIs.

---

# Golden Rules

1. Never sacrifice reusability.
2. Never duplicate components.
3. Never hardcode business data inside pages.
4. Always prefer reusable architecture.
5. Keep components small.
6. Build incrementally.
7. Build successfully after every pass.
8. Commit after every pass.
9. Push after every pass.
10. Never leave the project in a broken state.

---

# Development Strategy

Each pass must produce a usable application.

Every pass ends with

```
Working UI

↓

Build Success

↓

Git Commit

↓

Git Push
```

---

# Read Before Coding

Before writing any code, Claude must read and follow:

```
01-Project-Overview.md

02-UI-Design-Definition.md

03-Navigation-Map.md

04-Route-Definitions.md

05-Component-Catalog.md

06-Mock-Data-Dictionary.md

07-UX-Standards.md

08-Design-Tokens.md

09-AI-Behaviour.md

10-Demo-Story.md

11-Coding-Standards.md

12-Naming-Conventions.md
```

These documents are authoritative.

---

# Development Order

Never skip phases.

Always build in this order.

```
Foundation

↓

Layouts

↓

Navigation

↓

Common Components

↓

Pages

↓

Business Components

↓

Polish

↓

Optimization
```

---

# Code Quality

Every file must

- Compile
- Be readable
- Be modular
- Be typed
- Be reusable
- Be responsive

Never generate placeholder-quality code.

---

# Technology Rules

Use only

- Vue 3
- Composition API
- `<script setup>`
- TypeScript
- Pinia
- Vue Router
- Tailwind CSS
- Lucide
- Mock Services

Do not introduce additional frameworks without explicit approval.

---

# Architecture Rules

Always maintain

```
Page

↓

Components

↓

Store

↓

Service

↓

Mock Data
```

Never bypass this architecture.

---

# Folder Structure

Maintain

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

Never create unnecessary folders.

---

# Component Rules

If UI repeats twice

↓

Create reusable component.

Examples

```
StatusBadge

SmartTable

PageHeader

MetricCard

ProjectCard
```

Never duplicate markup.

---

# Page Rules

Pages should

- Assemble components
- Handle routing
- Coordinate stores

Pages should **not**

- Contain business logic
- Hardcode mock data
- Duplicate layouts

---

# Service Rules

All mock data must be accessed through services.

Example

```
projectService

↓

projects.ts
```

Never import mock data directly into pages.

---

# Store Rules

Pinia stores

- Manage state
- Call services
- Expose computed values

Stores never contain UI code.

---

# Mock Data Rules

Keep mock data

- Minimal
- Consistent
- Relational

Use the same entities throughout the application.

Never create duplicate datasets.

---

# UI Rules

The interface should resemble a mature commercial SaaS application.

Characteristics

- Calm
- Premium
- Spacious
- Professional
- Information-rich
- Minimal

Avoid

- Loud colours
- Heavy gradients
- Cartoon styling
- Visual clutter

---

# Responsive Rules

Support

- Desktop
- Tablet
- Mobile

No horizontal scrolling.

Sidebar collapses gracefully.

---

# AI Rules

AI is optional.

Never make any page dependent on AI.

If AI is disabled

↓

Everything continues working.

Use mock AI responses.

AI provider selection belongs only in

```
Administration

↓

AI Configuration
```

---

# Routing Rules

Follow

```
04-Route-Definitions.md
```

Exactly.

Do not invent routes.

---

# Naming Rules

Follow

```
12-Naming-Conventions.md
```

Exactly.

Never abbreviate business entities.

---

# Styling Rules

Use

Tailwind utility classes.

Avoid custom CSS.

Use Design Tokens.

Never hardcode colors or spacing.

---

# Icons

Use

Lucide Icons only.

No mixed icon libraries.

---

# Typography

Use

Inter

Maintain consistent hierarchy.

---

# Tables

Always use

SmartTable.

Never create custom tables for each page.

---

# Forms

Always use reusable controls.

Never duplicate input layouts.

---

# Dialogs

Always use

BaseDialog.

---

# Drawers

Always use

BaseDrawer.

---

# Notifications

Always use

NotificationDrawer

and

Toast

components.

---

# Error Handling

Every screen must have

- Loading state
- Empty state
- Error state

Never leave blank screens.

---

# Performance

Prefer

- Lazy loading
- Computed properties
- Reusable components
- Minimal re-renders

Avoid premature optimization.

---

# Accessibility

Support

- Keyboard navigation
- Focus indicators
- Semantic HTML
- ARIA attributes where appropriate

---

# Demo Quality

The prototype must convince a client that the product is already built.

Avoid

- Lorem Ipsum
- Placeholder text
- Dummy labels
- Broken navigation
- Empty pages

Every page should appear functional using mock data.

---

# Git Rules

At the end of every pass

Run

```bash
npm run build
```

Resolve all errors.

Run

```bash
npm run lint
```

Resolve all issues.

Commit

```bash
git add .

git commit -m "feat: <pass description>"
```

Push

```bash
git push
```

Never continue to the next pass until the current pass is committed and pushed.

---

# Definition of Complete

A pass is complete only if

✓ Application builds successfully

✓ No TypeScript errors

✓ No lint errors

✓ Responsive

✓ Navigation works

✓ Mock data displayed

✓ Components reusable

✓ No duplicated code

✓ No console errors

✓ Git commit completed

✓ Git push completed

---

# Forbidden Practices

Claude must never

- Use `any`
- Use JavaScript
- Use inline styles
- Hardcode business data
- Duplicate components
- Ignore TypeScript errors
- Ignore lint errors
- Leave TODO comments
- Leave commented-out code
- Leave unused imports
- Introduce unnecessary dependencies
- Modify completed passes unless fixing defects

---

# Decision Priority

When making implementation decisions, use the following order of precedence:

1. Simplicity
2. Reusability
3. Maintainability
4. Consistency
5. User Experience
6. Performance
7. Visual Polish

Never optimize one criterion at the expense of the higher-priority items.

---

# Expected Outcome

The completed frontend should resemble a polished commercial product used daily by engineering consultancies. It should be visually complete, fully navigable, responsive, consistent, and backed entirely by reusable architecture and mock services. Replacing the mock services with Python APIs should be sufficient to transition the application toward production.