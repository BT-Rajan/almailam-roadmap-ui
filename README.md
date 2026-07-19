# Almailem Roadmap UI

A front-end-only Vue 3 mockup of **Phase 1 — From Request to Project Tracking**, the
AI-powered workflow and dashboards for Abdulhadi Almailem Engineering Consulting Firm
(request intake through municipality approval tracking).

This is a clickable design mockup: no backend, API, or database. All content is
static data in `src/data/roadmap.js`, styled to read like a set of drafting-sheet
dashboards for the firm.

Companion project: [serviceos-ui](https://github.com/BT-Rajan/serviceos-ui) (used as
a structural reference for how this mockup is organized).

## Stack

- Vue 3 + `<script setup>`
- Vite
- Plain CSS with a small design-token system (`src/style.css`) — no framework

## Structure

```
src/
  data/roadmap.js         content transcribed from the roadmap artwork
  components/
    AppHeader.vue          firm mark, title, AI assistant note
    PhaseRail.vue          the 4-step intake → project flow + active project card
    AiFunctions.vue        the 6 AI function cards
    ServiceConfig.vue      service catalogue + per-service configuration fields
    DashboardOverview.vue  internal vs. client dashboards + example project timeline
    DocumentTracking.vue   document & approval tracking table
    Milestones.vue         12-step milestone reference grid
    Benefits.vue           key benefits grid
  App.vue
  style.css                design tokens (color, type, layout)
```

## Run locally

```bash
npm install
npm run dev       # dev server
npm run build     # production build to dist/
npm run preview   # preview the production build
```
