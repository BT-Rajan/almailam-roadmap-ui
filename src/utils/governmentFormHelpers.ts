import { Building2, Droplet, Flame, Leaf, Zap } from '@lucide/vue'
import type { Component } from 'vue'

import type { BadgeVariant } from '@/types/Ui'
import type { AuthorityCategory, GovernmentForm, GovernmentFormCategory } from '@/types/Government'

const AUTHORITY_CATEGORY_ICONS: Record<AuthorityCategory, Component> = {
  Municipality: Building2,
  'Fire Department': Flame,
  Electricity: Zap,
  Water: Droplet,
  Environment: Leaf,
}

const FORM_CATEGORY_VARIANTS: Record<GovernmentFormCategory, BadgeVariant> = {
  'Building Permit': 'info',
  'Occupancy Certificate': 'success',
  'Fire Safety Approval': 'danger',
  'Utility Connection': 'warning',
  'Environmental Clearance': 'success',
  'Business License': 'neutral',
}

export function getAuthorityCategoryIcon(category: AuthorityCategory): Component {
  return AUTHORITY_CATEGORY_ICONS[category]
}

export function getFormCategoryVariant(category: GovernmentFormCategory): BadgeVariant {
  return FORM_CATEGORY_VARIANTS[category]
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
