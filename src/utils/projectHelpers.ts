import type { BadgeVariant } from '@/types/Ui'
import type { ProjectPriority, ProjectStatus, ProjectWorkspaceTabKey, WorkflowStage } from '@/types/Project'
import type { SelectedActivityStatus } from '@/types/ServiceCatalog'
import type { SelectedPermitStatus } from '@/types/Project'

// Design, Government Submission (Approvals & Permits), and Supervision
// are three independent, PARALLEL tracks off Contract -- a project
// includes any combination of the three, or none, and none of the
// three is ordered relative to the other two (see
// Project.includesDesign/includesGovernmentSubmission/
// includesSupervision, and WorkflowProgress.vue, which draws them as
// one branching band rather than three stops on a line). Their
// relative order in this array is therefore arbitrary -- nothing
// compares two of the three against each other via
// hasProjectPassedStage below, only against a genuinely-sequential
// stage like 'Contract'. All three converge on 'Handover', the real
// terminal stage.
export const WORKFLOW_STAGES: WorkflowStage[] = [
  'Requirement',
  'Quotation',
  'Payment Plan',
  'Contract',
  'Design',
  'Government Submission',
  'Supervision',
  'Handover',
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
  Requirement: 'Scope',
  Quotation: 'Quotation',
  'Payment Plan': 'Payment Plan',
  Contract: 'Contract',
  Design: 'Design',
  Supervision: 'Supervision',
  'Government Submission': 'Approvals & Permits',
  Handover: 'Handover',
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
  Handover: 'project.stage.handover',
}

export function getWorkflowStageLabelKey(stage: WorkflowStage): string {
  return WORKFLOW_STAGE_LABEL_KEYS[stage]
}

// Single source of truth for "which tab covers this stage" -- was
// previously only defined inline as WorkflowProgress.vue's own
// STAGE_TABS. Pulled out here for the same reason as the label keys
// above.
//
// "Payment Plan" points at its own 'payment-plan' tab (PaymentPlanPanel.vue),
// the same as every other stage below -- it used to point at 'quotation'
// (the agreement/approval UI lived embedded at the bottom of the Quotation
// tab), but Payment Plan is genuinely the next stage after Quotation, not
// part of it, so it gets its own dedicated landing tab like Contract/
// Design/Government Submission/Supervision do. Payment Status (ongoing
// collections tracking, a different and longer-lived concern) keeps its
// own separate tab.
//
// "Requirement" points at 'requirement', a tab key with no dedicated
// component of its own anymore -- the Scope of Work editor (edit/save &
// proceed) now lives directly on ProjectOverviewTab's own Scope card,
// replacing the former separate ProjectRequirementTab destination
// entirely, and ProjectWorkspacePage.vue renders it for 'requirement'
// the same as 'overview'. Kept distinct from 'overview' itself (rather
// than pointing here too) so the stepper's "Scope" step still reliably
// resets stageContext back to 'Requirement' -- see ProjectWorkspaceTabKey's
// own comment for why a same-value 'overview' -> 'overview' reassignment
// wouldn't do that.
const WORKFLOW_STAGE_TAB_KEYS: Record<WorkflowStage, ProjectWorkspaceTabKey> = {
  Requirement: 'requirement',
  Quotation: 'quotation',
  'Payment Plan': 'payment-plan',
  Contract: 'contract',
  Design: 'design',
  Supervision: 'supervision',
  'Government Submission': 'government',
  Handover: 'handover',
}

export function getWorkflowStageTabKey(stage: WorkflowStage): ProjectWorkspaceTabKey {
  return WORKFLOW_STAGE_TAB_KEYS[stage]
}

const STATUS_VARIANTS: Record<ProjectStatus, BadgeVariant> = {
  Active: 'success',
  'On Hold': 'warning',
  Cancelled: 'danger',
  Completed: 'success',
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

const SELECTED_ACTIVITY_STATUS_VARIANTS: Record<SelectedActivityStatus, BadgeVariant> = {
  'Not Started': 'neutral',
  'In Progress': 'info',
  Complete: 'success',
  Cancelled: 'danger',
}

export function getSelectedActivityStatusVariant(status: SelectedActivityStatus): BadgeVariant {
  return SELECTED_ACTIVITY_STATUS_VARIANTS[status]
}

const SELECTED_PERMIT_STATUS_VARIANTS: Record<SelectedPermitStatus, BadgeVariant> = {
  Planned: 'neutral',
  Eligible: 'info',
  'In Progress': 'info',
  Complete: 'success',
  Cancelled: 'danger',
}

export function getSelectedPermitStatusVariant(status: SelectedPermitStatus): BadgeVariant {
  return SELECTED_PERMIT_STATUS_VARIANTS[status]
}
