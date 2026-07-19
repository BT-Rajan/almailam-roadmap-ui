import type { BadgeVariant } from '@/types/Ui'
import type { ProjectPriority, ProjectStatus } from '@/types/Project'

const STATUS_VARIANTS: Record<ProjectStatus, BadgeVariant> = {
  Active: 'success',
  'On Hold': 'warning',
  Completed: 'primary',
  Cancelled: 'danger',
}

const PRIORITY_VARIANTS: Record<ProjectPriority, BadgeVariant> = {
  High: 'danger',
  Medium: 'warning',
  Low: 'neutral',
}

export function getProjectStatusVariant(status: ProjectStatus): BadgeVariant {
  return STATUS_VARIANTS[status]
}

export function getProjectPriorityVariant(priority: ProjectPriority): BadgeVariant {
  return PRIORITY_VARIANTS[priority]
}

export function generateProjectNo(existingCount: number): string {
  const year = new Date().getFullYear()
  const sequence = String(existingCount + 1).padStart(3, '0')
  return `PRJ-${year}-${sequence}`
}
