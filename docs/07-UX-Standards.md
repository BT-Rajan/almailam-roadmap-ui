# 07 - UX Standards

**Project:** ServiceOS  
**Client:** Almailam Engineering Consultants

**Version:** 1.0

---

# Purpose

This document defines the User Experience (UX) standards for ServiceOS.

Its purpose is to ensure every screen behaves consistently regardless of who develops it.

A user should never have to relearn how to use another part of the application.

These standards are mandatory for every page, component and interaction.

---

# UX Philosophy

ServiceOS is an operational platform used daily by engineers, project managers, document controllers and administrators.

The application should feel like:

- Calm
- Confident
- Fast
- Predictable
- Premium
- Reliable
- Intelligent
- Effortless

Users should feel that the software assists them rather than demands their attention.

---

# Core UX Principles

## 1. Consistency

The same action should always behave the same way.

Examples

- Save button always appears in the same location.
- Delete confirmations always look identical.
- Search behaves identically across every module.
- Filters always appear in the same order.
- Dialog buttons are always positioned consistently.

Users should never wonder:

> "Does this screen work differently?"

---

## 2. Recognition over Recall

Never expect users to remember information.

Always display:

- Current project
- Current workflow stage
- Current client
- Current document
- Current task
- Current authority

The interface should continuously provide context.

---

## 3. Progressive Disclosure

Only display information needed at that moment.

Instead of showing:

- 80 fields

Show

- Important information first
- Advanced options only when needed

---

## 4. Fewer Clicks

Common tasks should require the minimum number of interactions.

Examples

Good

```
Dashboard

↓

Projects

↓

Open Project
```

Bad

```
Dashboard

↓

Projects

↓

Search

↓

Details

↓

Workspace
```

---

## 5. Never Surprise the User

Buttons always do what users expect.

Avoid

- Hidden actions
- Unexpected navigation
- Silent failures
- Automatic changes

---

# Page Behaviour

Every page follows this structure.

```
Breadcrumb

↓

Page Title

↓

Summary

↓

Toolbar

↓

Content

↓

Dialogs
```

Never rearrange this order.

---

# Page Loading

Pages should appear immediately.

While loading

Display

- Skeletons
- Placeholder cards
- Placeholder tables

Never display blank pages.

---

# Empty States

Every list requires an empty state.

Should include

- Friendly illustration/icon
- Short explanation
- Primary action

Example

"No projects have been created."

[Create Project]

---

# Error States

Errors must be understandable.

Never display

```
500

Null Reference

Undefined

Stack Trace
```

Instead

```
Unable to load projects.

Please try again.
```

[Retry]

---

# Search

Every searchable page behaves identically.

Typing immediately filters results.

Search is

- Fast
- Responsive
- Case insensitive

Search field always appears first in the toolbar.

---

# Filters

Filter order never changes.

Recommended order

```
Search

↓

Status

↓

Category

↓

Assigned To

↓

Date

↓

Advanced Filters
```

---

# Sorting

Default

Newest first.

Remember user selection during the session.

---

# Tables

Every Smart Table behaves identically.

Capabilities

- Search
- Sort
- Filter
- Pagination
- Row actions
- Bulk selection
- Empty state

Never implement custom table behaviour.

---

# Forms

Forms should feel effortless.

Rules

- Group related fields
- Clear labels
- Required fields only
- Inline validation
- Logical tab order

Avoid overwhelming users.

---

# Validation

Validation occurs

- While typing where appropriate
- On submit
- Before save

Messages should explain

- What is wrong
- How to fix it

Never use technical terminology.

---

# Save Behaviour

Save button always

Bottom-right

or

Top-right

Never change location.

After successful save

- Show success toast
- Keep user context
- Never refresh entire page unnecessarily

---

# Delete Behaviour

Delete is always protected.

Workflow

```
Delete

↓

Confirmation Dialog

↓

Delete

↓

Success Message
```

Never delete immediately.

---

# Dialog Standards

Dialogs are used for

- Create
- Edit
- AI Preview
- Confirm
- Upload

Never use dialogs for large workflows.

---

# Drawer Standards

Drawers are preferred for

- Details
- AI Assistant
- Quick Edit
- Preview

Opening a drawer should never lose page context.

---

# Notifications

Notifications are informative.

Never interrupt workflow.

Types

Information

Success

Warning

Error

Toast duration

Approximately 3–5 seconds.

Critical messages require user acknowledgement.

---

# Workflow UX

Workflow should always answer

- Where am I?
- What is complete?
- What is pending?
- What happens next?

Never force users to infer workflow state.

---

# AI Experience

AI should feel like an experienced consultant.

AI should

- Explain
- Suggest
- Summarize
- Highlight risks
- Recommend next actions

AI should never appear authoritative or final.

Users remain in control.

---

# AI Response Format

Every response displays

- Summary
- Details
- Confidence
- Suggested actions

Consistent across every module.

---

# Navigation

Navigation should require almost no learning.

Sidebar remains stable.

Breadcrumb always visible.

Current page clearly highlighted.

---

# Keyboard Experience

Support

Tab

Shift+Tab

Esc

Enter

Ctrl+K (Global Search)

Arrow navigation where appropriate.

---

# Mouse Experience

Clickable areas should be generous.

Hover feedback should always exist.

Interactive elements should clearly indicate action.

---

# Mobile Experience

Navigation becomes drawer.

Cards stack vertically.

Tables convert to cards where appropriate.

Buttons become full-width only when necessary.

---

# Performance Perception

Application should feel instant.

Use

- Skeletons
- Optimistic UI where appropriate
- Smooth transitions

Avoid

- Flickering
- Large layout shifts
- Blocking spinners

---

# Visual Hierarchy

Users should immediately identify

1. Page title
2. Primary action
3. Current status
4. Important metrics
5. Main content

Avoid giving equal emphasis to everything.

---

# Information Density

Target

High information density

WITHOUT

- Clutter
- Visual noise
- Tiny fonts
- Excessive scrolling

Whitespace is intentional.

---

# Accessibility

Every interactive element

- Keyboard accessible
- Visible focus state
- Sufficient contrast
- ARIA labels where applicable

Do not rely on colour alone.

---

# Trust Indicators

The interface should continuously reinforce confidence.

Display

- Last updated
- Current status
- Responsible person
- Workflow progress
- AI confidence
- Document version

Users should always know the current state.

---

# Responsiveness

Desktop

Primary experience.

Tablet

No loss of functionality.

Mobile

Critical workflows only.

No horizontal scrolling.

---

# Animation Standards

Animations should communicate state changes.

Allowed

- Fade
- Slide
- Expand
- Collapse

Animation duration

150–250ms

Never use decorative animations.

---

# Premium Experience

The application should resemble a high-end commercial SaaS platform rather than a traditional business application.

Characteristics

- Generous spacing
- Excellent typography
- Consistent rhythm
- Refined shadows
- Smooth transitions
- Elegant interactions
- High visual polish
- Calm interface
- Minimal cognitive load

Luxury is achieved through restraint, precision and consistency—not visual excess.

---

# User Confidence

At every moment, the user should know:

- Where they are
- What they are viewing
- What requires attention
- What can be done next
- Whether their action succeeded

The interface should never create uncertainty.

---

# UX Success Criteria

A first-time user should be able to:

- Log in without guidance.
- Locate any project within seconds.
- Understand project status immediately.
- Upload documents intuitively.
- Track government submissions effortlessly.
- Use AI features without training.
- Find information quickly.
- Complete common tasks confidently.

The finished application should feel like a mature, enterprise-grade product that has evolved through years of refinement, while remaining approachable for a small, growing consultancy like Almailam.