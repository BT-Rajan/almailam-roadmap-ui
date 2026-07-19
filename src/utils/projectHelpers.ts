import type { BadgeVariant } from '@/types/Ui'
import type { ProjectPriority, ProjectStatus, WorkflowStage } from '@/types/Project'

export const WORKFLOW_STAGES: WorkflowStage[] = [
  'Enquiry',
  'Quotation',
  'Contract',
  'Design',
  'Government Submission',
  'Review',
  'Correction',
  'Approval',
  'Completed',
]

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
