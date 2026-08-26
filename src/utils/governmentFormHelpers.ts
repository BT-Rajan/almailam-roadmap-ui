import { Building2, Droplet, Flame, Landmark, Leaf, Zap } from '@lucide/vue'
import type { Component } from 'vue'

import type { BadgeVariant } from '@/types/Ui'
import type { AuthorityCategory, GovernmentForm, GovernmentFormCategory } from '@/types/Government'

const AUTHORITY_CATEGORY_ICONS: Record<AuthorityCategory, Component> = {
  Municipality: Building2,
  'Fire Department': Flame,
  Electricity: Zap,
  Water: Droplet,
  Environment: Leaf,
  Internal: Landmark,
}

const FORM_CATEGORY_VARIANTS: Record<GovernmentFormCategory, BadgeVariant> = {
  'Building Permit': 'info',
  'Occupancy Certificate': 'success',
  'Fire Safety Approval': 'danger',
  'Utility Connection': 'warning',
  'Environmental Clearance': 'success',
  'Business License': 'neutral',
  Agreement: 'primary',
  'Legal Undertaking': 'ai',
}

export function getAuthorityCategoryIcon(category: AuthorityCategory): Component {
  return AUTHORITY_CATEGORY_ICONS[category]
}

export function getFormCategoryVariant(category: GovernmentFormCategory): BadgeVariant {
  return FORM_CATEGORY_VARIANTS[category]
}

// Fills a form's {{token}} template with whatever merge context is
// available. This is a client-side stub: real projects don't yet have a
// backend endpoint that generates a signed, DB-backed document, so any
// token without a context value renders as a visible blank line rather
// than silently disappearing or throwing.
export function renderGovernmentFormTemplate(template: string, context: Record<string, string | undefined>): string {
  return template.replace(/{{\s*(\w+)\s*}}/g, (_match, token: string) => {
    const value = context[token]
    return value && value.trim().length > 0 ? value : '………………'
  })
}

// Every distinct {{token}} a template references, in first-appearance
// order -- drives the Fill Form dialog's one-input-per-token form without
// needing each template's fields hardcoded anywhere on the frontend.
export function extractTemplateTokens(template: string): string[] {
  const tokens: string[] = []
  const seen = new Set<string>()
  for (const match of template.matchAll(/{{\s*(\w+)\s*}}/g)) {
    const token = match[1]
    if (!seen.has(token)) {
      seen.add(token)
      tokens.push(token)
    }
  }
  return tokens
}

// A project's `service` field is a comma-joined summary of the Service
// Catalog services picked for it (see Project.service). A form is
// suggested for a project when any of its tagged services appears in
// that summary -- case-insensitive since the two are typed/edited in
// different admin screens.
export function formMatchesProjectService(form: GovernmentForm, projectService: string): boolean {
  const serviceTags = form.serviceTags ?? []
  if (serviceTags.length === 0) return false
  const pickedServices = projectService
    .split(',')
    .map((name) => name.trim().toLowerCase())
    .filter((name) => name.length > 0)
  return serviceTags.some((tag) => pickedServices.includes(tag.trim().toLowerCase()))
}

export function printFillableForm(url: string): void {
  const printWindow = window.open(url, '_blank')
  printWindow?.addEventListener('load', () => printWindow.print())
}

export function printFormSummary(form: GovernmentForm, authorityName: string): void {
  const printWindow = window.open('', '_blank')
  if (!printWindow) return

  const documentsList = form.requiredDocuments.map((doc) => `<li>${doc}</li>`).join('')

  printWindow.document.write(`
    <!DOCTYPE html>
    <html>
      <head>
        <title>${form.formCode} \u2013 ${form.title}</title>
        <style>
          body { font-family: -apple-system, sans-serif; padding: 40px; color: #1a1a2e; }
          h1 { font-size: 20px; margin-bottom: 4px; }
          .meta { color: #5a6a7e; font-size: 13px; margin-bottom: 24px; }
          .field { margin-bottom: 16px; }
          .field label { display: block; font-size: 12px; font-weight: 600; color: #5a6a7e; text-transform: uppercase; }
          .field p { margin: 2px 0 0; font-size: 14px; }
          ul { margin: 4px 0 0; padding-left: 20px; }
        </style>
      </head>
      <body>
        <h1>${form.title}</h1>
        <p class="meta">${form.formCode} &middot; ${form.version} &middot; ${authorityName}</p>
        <div class="field"><label>Category</label><p>${form.category}</p></div>
        <div class="field"><label>Language</label><p>${form.language}</p></div>
        <div class="field"><label>Description</label><p>${form.description}</p></div>
        <div class="field"><label>Required Documents</label><ul>${documentsList}</ul></div>
        <div class="field"><label>Last Updated</label><p>${form.lastUpdated}</p></div>
      </body>
    </html>
  `)
  printWindow.document.close()
  printWindow.focus()
  printWindow.print()
}
