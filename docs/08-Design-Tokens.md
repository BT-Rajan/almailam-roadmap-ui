# 08 - Design Tokens

**Project:** ServiceOS  
**Client:** Almailam Engineering Consultants

**Version:** 1.0

---

# Purpose

This document defines the visual design tokens used throughout ServiceOS.

These tokens establish a single source of truth for colors, spacing, typography, sizing, elevation, borders, motion and responsive behavior.

Developers must never hardcode visual values in components.

All UI must consume these tokens.

---

# Design Philosophy

The visual language should communicate:

- Premium
- Stable
- Mature
- Luxurious
- Enterprise Grade
- Calm
- Engineering Precision

The design should resemble products such as:

- Linear
- Notion
- Atlassian
- Figma
- Vercel Dashboard
- GitHub Enterprise

Avoid flashy consumer-app styling.

---

# Color System

## Primary

Used for

- Primary Buttons
- Active Navigation
- Links
- Highlights

```
Primary 50
Primary 100
Primary 200
Primary 300
Primary 400
Primary 500
Primary 600
Primary 700
Primary 800
Primary 900
```

---

## Neutral

Used for

- Backgrounds
- Borders
- Text
- Cards

```
Neutral 0
Neutral 50
Neutral 100
Neutral 200
Neutral 300
Neutral 400
Neutral 500
Neutral 600
Neutral 700
Neutral 800
Neutral 900
```

---

## Semantic Colors

### Success

```
Success 50
Success 100
Success 500
Success 700
```

Used for

- Completed
- Approved
- Active

---

### Warning

```
Warning 50
Warning 100
Warning 500
Warning 700
```

Used for

- Pending
- Attention Required

---

### Danger

```
Danger 50
Danger 100
Danger 500
Danger 700
```

Used for

- Errors
- Rejected
- Delete

---

### Information

```
Info 50
Info 100
Info 500
Info 700
```

Used for

- Progress
- Guidance
- AI

---

# Background Colors

```
Page Background

Card Background

Secondary Background

Sidebar Background

Header Background

Hover Background

Selected Background
```

Never use pure white or pure black.

---

# Text Colors

```
Primary Text

Secondary Text

Muted Text

Placeholder Text

Disabled Text

Inverse Text

Link Text
```

---

# Border Colors

```
Light Border

Default Border

Strong Border

Focus Border

Error Border
```

---

# Typography

Font Family

```
Inter
```

Fallback

```
System UI
```

---

## Font Sizes

```
12

14

16

18

20

24

30

36

48
```

Use predefined scale only.

---

## Font Weight

```
Regular

Medium

SemiBold

Bold
```

---

## Line Height

```
Compact

Comfortable

Relaxed
```

---

# Border Radius

```
Small

Medium

Large

Extra Large

Full
```

Applications should use rounded corners consistently.

Avoid sharp corners.

---

# Elevation

```
Level 0

Level 1

Level 2

Level 3

Level 4
```

Higher elevation only for

- Dialogs
- Floating Panels
- Menus

---

# Shadows

Soft shadows only.

Never use heavy shadows.

Cards

↓

Light

Dialogs

↓

Medium

Dropdowns

↓

Medium

---

# Spacing Scale

Base Unit

```
4px
```

Scale

```
4

8

12

16

20

24

32

40

48

64

80
```

Never invent custom spacing.

---

# Layout Dimensions

Sidebar Expanded

```
280px
```

Sidebar Collapsed

```
80px
```

Top Navigation

```
64px
```

Page Max Width

```
Fluid
```

Content Padding

```
32px
```

Section Gap

```
32px
```

Card Gap

```
24px
```

---

# Component Heights

Buttons

```
Small

Medium

Large
```

Inputs

```
Medium

Large
```

Toolbar

```
56px
```

Page Header

```
72px
```

Cards

```
Auto Height
```

---

# Icon Sizes

```
16

18

20

24

32
```

Navigation

↓

20

Buttons

↓

18

Cards

↓

20

---

# Avatar Sizes

```
Small

Medium

Large

Extra Large
```

---

# Table Tokens

Row Height

```
Compact

Default

Comfortable
```

Header Height

```
Standard
```

Cell Padding

```
Consistent
```

---

# Z-Index Layers

```
Base

Sticky Header

Dropdown

Drawer

Modal

Notification

Tooltip
```

Maintain consistent stacking order.

---

# Animation

Duration

```
Fast

Normal

Slow
```

Timing

```
Ease In

Ease Out

Ease In Out
```

Use animations sparingly.

---

# Transition Standards

Allowed

- Fade
- Slide
- Expand
- Collapse

Not Allowed

- Bounce
- Spin
- Flash
- Zoom

---

# Opacity

```
Disabled

Muted

Overlay

Backdrop
```

---

# Blur

Used only for

- Modal Backdrop
- Glass Navigation (optional)

---

# Status Colors

## Draft

Blue

---

## Pending

Amber

---

## In Progress

Cyan

---

## Approved

Green

---

## Completed

Slate

---

## Rejected

Red

---

## Cancelled

Gray

Status colors must remain consistent throughout the application.

---

# AI Tokens

AI Accent

Purple / Indigo family

Confidence Indicator

Green

Medium Confidence

Amber

Low Confidence

Red

AI panels should remain visually distinct without overpowering the application.

---

# Government Module

Authority

Blue

Submission

Cyan

Correction

Orange

Approval

Green

Rejected

Red

---

# Charts

Maximum five colors.

Prefer monochromatic palettes.

Avoid rainbow charts.

No gradients.

No 3D charts.

---

# Responsive Breakpoints

```
Mobile

Tablet

Laptop

Desktop

Ultra Wide
```

Layouts should adapt without changing interaction patterns.

---

# Focus Indicators

All interactive controls must have

- Visible focus ring
- Accessible contrast
- Keyboard support

---

# Disabled State

Disabled controls must

- Reduce emphasis
- Remain readable
- Never disappear

---

# Hover State

Hover should indicate

- Clickable
- Selectable
- Expandable

Hover effects should remain subtle.

---

# Selection State

Selected elements should be immediately recognizable using

- Border
- Background
- Accent

Avoid relying on color alone.

---

# Scrollbars

Use modern thin scrollbars.

Never hide scrollbars.

---

# Cards

Cards remain the primary container.

Standard structure

```
Header

↓

Body

↓

Footer
```

Every card uses identical padding and spacing.

---

# White Space

Whitespace is a design feature.

Never fill every available area.

Maintain visual breathing room.

---

# Design Constraints

Developers must never

- Hardcode colors
- Hardcode spacing
- Hardcode typography
- Hardcode shadows
- Use arbitrary border radius
- Introduce new visual styles
- Create inconsistent button variants
- Create inconsistent card styles

Every visual property must come from these design tokens.

---

# Future Theme Support

The token system must support

- Light Theme
- Dark Theme
- Client Branding
- High Contrast Mode

without changing components.

---

# Success Criteria

A user moving between any two screens should perceive a single, coherent design language. Every page should appear to have been created by the same design team, using the same visual system, with no inconsistencies in spacing, typography, colors, sizing or interaction states.