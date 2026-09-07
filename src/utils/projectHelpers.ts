import type { BadgeVariant } from '@/types/Ui'
import type { ProjectPriority, ProjectStatus, ProjectWorkspaceTabKey, WorkflowStage } from '@/types/Project'

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

// True once the project's real current stage is strictly past
// referenceStage in the straight-line order above -- gates every
// "Advance to X" convenience button/banner (Quotation's "Advance to
// Payment Plan", Payment Plan's "Advance to Contract", and so on) so
// they only appear while genuinely still relevant. Those buttons are
// pure navigation shown once the underlying stage change has already
// auto-advanced the project -- without this check they stayed visible
// forever afterward (the quotation/agreement they check is Approved
// permanently), so revisiting an old tab long after actually moving on
// kept dangling a stale "you should go here next" prompt.
export function hasProjectPassedStage(currentStage: WorkflowStage, referenceStage: WorkflowStage): boolean {
  return WORKFLOW_STAGES.indexOf(currentStage) > WORKFLOW_STAGES.indexOf(referenceStage)
}

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

// i18n key for each stage's translated label -- was previously only
// defined inline as WorkflowProgress.vue's own STAGE_LABEL_KEYS. Pulled
// out here so anything else that needs to name the project's current
// stage (e.g. PaymentPlanPanel.vue pointing staff at wherever the
// project actually is now) can render it in the active locale too,
// instead of falling back to the English-only getWorkflowStageLabel
// above.
const WORKFLOW_STAGE_LABEL_KEYS: Record<WorkflowStage, string> = {
  Requirement: 'project.stage.requirement',
  Quotation: 'project.stage.quotation',
  'Payment Plan': 'project.stage.paymentPlan',
  Contract: 'project.stage.contract',
  Design: 'project.stage.design',
  Supervision: 'project.stage.supervision',
  'Government Submission': 'project.stage.governmentSubmission',
}

export function getWorkflowStageLabelKey(stage: WorkflowStage): string {
  return WORKFLOW_STAGE_LABEL_KEYS[stage]
}

// Single source of truth for "which tab covers this stage" -- was
// previously only defined inline as WorkflowProgress.vue's own
// STAGE_TABS. Pulled out here for the same reason as the label keys
// above.
//
// "Payment Plan" points at 'quotation', not a dedicated tab of its own
// -- the Payment Plan agreement/approval UI (PaymentPlanPanel.vue) now
// lives embedded inside the Quotation tab (see ProjectQuotationTab.vue),
// since staff work through it as part of the same quotation-negotiation
// conversation with the client. Payment Status (ongoing collections
// tracking, a different and longer-lived concern) keeps its own tab.
const WORKFLOW_STAGE_TAB_KEYS: Record<WorkflowStage, ProjectWorkspaceTabKey> = {
  Requirement: 'requirement',
  Quotation: 'quotation',
  'Payment Plan': 'quotation',
  Contract: 'contract',
  Design: 'design',
  Supervision: 'supervision',
  'Government Submission': 'government',
}

export function getWorkflowStageTabKey(stage: WorkflowStage): ProjectWorkspaceTabKey {
  return WORKFLOW_STAGE_TAB_KEYS[stage]
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
