import { Building2, Droplet, Flame, Leaf, Zap } from '@lucide/vue'
import type { Component } from 'vue'

import type { BadgeVariant } from '@/types/Ui'
import type { AuthorityCategory, GovernmentFormCategory } from '@/types/Government'

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
