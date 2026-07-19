# 11 - Coding Standards

**Project:** ServiceOS  
**Client:** Almailam Engineering Consultants

**Technology Stack**

- Vue 3
- Vite
- TypeScript
- Pinia
- Vue Router
- Tailwind CSS
- Lucide Icons

---

# Purpose

This document defines the coding standards for the ServiceOS frontend.

The objectives are to ensure

- Consistency
- Readability
- Maintainability
- Reusability
- Scalability
- Production-quality code

Every developer and AI assistant must follow these standards.

---

# Development Philosophy

Write code as if it will be maintained for the next ten years.

Optimize for

- Readability
- Simplicity
- Reuse

Not

- Cleverness
- Shortest code
- Experimental techniques

---

# Core Principles

- KISS (Keep It Simple)
- DRY (Don't Repeat Yourself)
- SOLID (where applicable)
- Composition over Inheritance
- Single Responsibility
- Separation of Concerns

---

# Code Quality Goals

Every file should be

- Small
- Predictable
- Easy to understand
- Easy to test
- Easy to replace

---

# Language

Use

TypeScript

Everywhere.

Do not use JavaScript files.

---

# Vue Standards

Use

- Composition API
- `<script setup>`
- TypeScript

Never use

- Options API
- Mixins
- Global event bus

---

# Component Size

## Preferred

Less than

200 lines

---

## Maximum

300 lines

If larger

↓

Split into smaller components.

---

# Page Size

Pages should only compose components.

Preferred

250 lines

Maximum

350 lines

Business logic belongs elsewhere.

---

# Function Size

Preferred

20–30 lines

Maximum

50 lines

Large functions must be decomposed.

---

# Component Structure

Every component follows

```vue
<script setup lang="ts">

Imports

Types

Props

Emits

Stores

Composables

Reactive State

Computed

Methods

Lifecycle

</script>

<template>

</template>

<style scoped>

</style>
```

Never deviate.

---

# File Naming

Components

```
PascalCase.vue
```

Example

```
ProjectCard.vue

WorkflowStepper.vue

StatusBadge.vue
```

---

Pages

```
PascalCase.vue
```

Example

```
DashboardPage.vue

ProjectWorkspacePage.vue
```

---

Stores

```
camelCase.ts
```

Example

```
projectStore.ts

taskStore.ts
```

---

Services

```
camelCase.ts
```

Example

```
projectService.ts
```

---

Utilities

```
camelCase.ts
```

---

Types

```
PascalCase.ts
```

Example

```
Project.ts

Document.ts
```

---

# Imports

Import order

```
Vue

Third Party

Components

Stores

Composables

Services

Types

Utilities

Styles
```

Maintain consistent ordering.

---

# Props

Always

- Type props
- Define defaults where appropriate

Never use

```
any
```

---

# Emits

Always

Define emitted events.

Example

```
save

delete

cancel

update
```

---

# State Management

Use Pinia.

Pages never manage shared state.

Shared state belongs inside stores.

---

# Services

All data access goes through services.

Never

```
Component

↓

Mock Data
```

Always

```
Component

↓

Store

↓

Service

↓

Mock Data
```

---

# Mock Data

Never hardcode business data inside components.

Always import through services.

---

# Styling

Use

Tailwind CSS

Never use

Inline CSS

Avoid custom CSS whenever possible.

---

# Responsive Design

Every page must support

Desktop

Tablet

Mobile

No page should break on smaller screens.

---

# Icons

Use

Lucide Icons only.

Never mix icon libraries.

---

# Forms

Use reusable form components.

Never duplicate input layouts.

---

# Tables

Always use

SmartTable

Never build custom tables.

---

# Dialogs

Always use

BaseDialog

Never create page-specific dialog implementations.

---

# Drawers

Always use

BaseDrawer

---

# AI Components

Always use

AIAssistantDrawer

AIResponseCard

Never build AI UI from scratch.

---

# Error Handling

Never expose

- Stack traces
- Raw exceptions
- Console errors

Display friendly messages.

---

# Logging

Prototype

No logging except development warnings.

Production

Logging handled by backend.

---

# Comments

Code should explain itself.

Avoid unnecessary comments.

Comment only when explaining

- Business rules
- Complex algorithms
- Non-obvious decisions

---

# Magic Values

Never hardcode

- Colors
- Sizes
- Status values
- Routes
- Role names

Use

- Constants
- Enums
- Design Tokens

---

# Constants

Application constants belong inside

```
constants/
```

Examples

- Status
- Priorities
- Roles
- Workflow Stages

---

# Enums

Use enums for

- Status
- Priority
- Roles
- Document Types

Avoid string literals throughout the application.

---

# Types

Every entity has its own interface.

Example

```
Project

Client

Task

Document

GovernmentForm
```

Never use

```
Object

any
```

---

# Reusability Rule

If UI appears twice

↓

Create a reusable component.

If logic appears twice

↓

Create a composable or utility.

---

# Performance

Prefer

- Lazy loading
- Computed properties
- Component reuse
- Virtual scrolling (future)

Avoid

- Unnecessary watchers
- Nested loops
- Repeated calculations

---

# Accessibility

Every interactive control must support

- Keyboard navigation
- Focus states
- Screen readers
- Proper labels

---

# Git Discipline

One pass

↓

One feature

↓

One commit

↓

One push

Never combine unrelated work.

---

# Build Requirements

Every pass must finish with

```bash
npm run build
```

```bash
npm run lint
```

Build errors are never acceptable.

---

# Forbidden Practices

Never

- Use `any`
- Use inline CSS
- Duplicate code
- Hardcode business data
- Access mock JSON directly
- Mix business logic with UI
- Create monolithic components
- Leave unused imports
- Leave commented code
- Leave TODOs
- Leave console.log statements

---

# Code Review Checklist

Every commit must satisfy

✓ Builds successfully

✓ Lints successfully

✓ No TypeScript errors

✓ No console errors

✓ Responsive

✓ Uses reusable components

✓ Strong typing

✓ Clean imports

✓ Small components

✓ Mock services only

✓ No duplicated logic

---

# Definition of Done

Code is considered complete only when it is

- Production quality
- Strongly typed
- Modular
- Reusable
- Readable
- Responsive
- Maintainable
- Buildable
- Fully compliant with these standards

The frontend should be capable of moving to production by replacing only the mock service layer with real Python REST API endpoints.