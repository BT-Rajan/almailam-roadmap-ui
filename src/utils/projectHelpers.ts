import type { BadgeVariant } from '@/types/Ui'
import type { ProjectPriority, ProjectStatus, WorkflowStage } from '@/types/Project'

export const WORKFLOW_STAGES: WorkflowStage[] = [
  'Requirement',
  'Quotation',
  'Contract',
  'Design',
  'Government Submission',
  'Execution & Tracking',
  'Completed',
]

// Which of the 7 workflow stages an execution activity is tagged to
// (see ExecutionStepEditor.vue) -- only the first 5 are relevant, since
// no activity is ever expected to belong to "Execution & Tracking"
// itself (that's the stage that tracks all 23 of them at once, not one
// they're filed under) or "Completed" (an end state, not a stage work
// happens during).
export const EXECUTION_STEP_STAGE_OPTIONS = WORKFLOW_STAGES.filter(
  (stage) => stage !== 'Execution & Tracking' && stage !== 'Completed',
)

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
  Contract: 'Contract',
  Design: 'Design',
  'Government Submission': 'Approvals & Permits',
  'Execution & Tracking': 'Execution & Tracking',
  Completed: 'Completed',
}

export function getWorkflowStageLabel(stage: WorkflowStage | string): string {
  return WORKFLOW_STAGE_LABELS[stage as WorkflowStage] ?? stage
}

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
