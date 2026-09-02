import type { BadgeVariant } from '@/types/Ui'
import type { ProjectPriority, ProjectStatus, WorkflowStage } from '@/types/Project'

// "Supervision" is an independent add-on stage that comes after
// Government Submission (Approvals & Permits), not before it -- a
// project can include Design, Supervision, both, or neither, and the
// stepper (WorkflowProgress.vue) filters this full list down to
// whichever stages actually apply to the project being viewed (see
// Project.includesDesign/includesSupervision).
export const WORKFLOW_STAGES: WorkflowStage[] = [
  'Requirement',
  'Quotation',
  'Payment Plan',
  'Contract',
  'Design',
  'Government Submission',
  'Supervision',
]

// Display-only relabeling -- "Government Submission" reads as "Approvals &
// Permits" everywhere shown to users. The stored/compared value stays
// "Government Submission" (it's a real backend ENUM value -- see
// backend/app/models/project.py's project_workflow_stage), so every
// transition table, filter, and stage-key comparison keeps working
// unchanged. Route every user-facing display of a WorkflowStage through
// this instead of interpolating the raw string.
const WORKFLOW_STAGE_LABELS: Record<WorkflowStage, string> = {
  Requirement: 'Requirement',
  Quotation: 'Quotation',
  'Payment Plan': 'Payment Plan',
  Contract: 'Contract',
  Design: 'Design',
  Supervision: 'Supervision',
  'Government Submission': 'Approvals & Permits',
}

export function getWorkflowStageLabel(stage: WorkflowStage | string): string {
  return WORKFLOW_STAGE_LABELS[stage as WorkflowStage] ?? stage
}

const STATUS_VARIANTS: Record<ProjectStatus, BadgeVariant> = {
  Active: 'success',
  'On Hold': 'warning',
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
