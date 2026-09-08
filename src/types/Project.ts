import type { SelectedServiceActivity } from '@/types/ServiceCatalog'

// "Completed" is the terminal status a project reaches once every
// planned Design/Permit/Supervision item is closed, payment on the
// current project value is settled in full, and the client has
// acknowledged the hand-over via a confirmed signed-document upload.
// See backend/app/models/project.py's PROJECT_STATUSES /
// PROJECT_STATUS_ALLOWED_TRANSITIONS comments.
export type ProjectStatus = 'Active' | 'On Hold' | 'Cancelled' | 'Completed'

// "Correction" used to be its own stage (Review <-> Correction, a loop
// back and forth for what's really one review cycle). Merged into
// Review -- a correction cycle is logged as a note on the project's
// History instead of a separate stage. "Enquiry" was itself renamed to
// "Requirement" (displayed to users as "Scope") -- its scope-of-work
// editing (edit / save & proceed) lives directly on ProjectOverviewTab's
// own Scope card rather than a dedicated tab of its own. "Execution &
// Tracking" and "Completed" were removed entirely -- "Government
// Submission" is now the terminal stage. "Supervision" sits alongside
// "Design" -- a project can include either, both, or neither, depending
// on Project.includesDesign/includesSupervision below. "Payment Plan"
// sits between Quotation and Contract -- the project's financial
// agreement(s) have to be generated and explicitly approved (see
// FinancialAgreement.status in types/Payment.ts) before a contract is
// even drafted. See backend/app/models/project.py's WORKFLOW_STAGES
// comment.
export type WorkflowStage =
  | 'Requirement'
  | 'Quotation'
  | 'Payment Plan'
  | 'Contract'
  | 'Design'
  | 'Supervision'
  | 'Government Submission'

// One entry per structurally-reachable next stage for this project
// right now -- see projectService.getStageEligibility and backend
// project_service.get_stage_eligibility, the single source of truth
// this mirrors. A stage the project can't reach at all (e.g. Design
// when it has no Design work) is left out entirely, not reported
// ineligible.
export interface StageEligibility {
  stage: WorkflowStage
  eligible: boolean
  reason?: string
}

// Adds more billable Design and/or Supervision activities to an
// existing project at any point in its lifecycle -- see
// projectService.addServices and backend project_service.
// add_selected_services. Only genuinely new activities (by activityId)
// get inserted; anything already selected is left alone. supervision*
// dates are only required the first time Supervision is added to a
// project that never had a Supervision window before.
export interface AddServicesInput {
  designActivities: SelectedServiceActivity[]
  supervisionActivities: SelectedSupervisionActivity[]
  supervisionStartDate?: string | null
  supervisionEndDate?: string | null
}

export type ProjectPriority = 'High' | 'Medium' | 'Low'

// One Supervision activity picked in the unified ServicePickerDialog at
// project setup -- see Project.selectedSupervisionActivities below.
// startDate/endDate are this activity's own window, independent of the
// project's overall supervisionStartDate/supervisionEndDate (both are
// captured separately, per the day-prorated monthly billing rules --
// see payment_calculations.generate_prorated_monthly_schedule).
// Gated the same way a Permit is (see SelectedPermitStatus below) --
// 'Planned' until its admin-defined SupervisionPrerequisite Design
// activities are all Complete, then 'Eligible'; 'In Progress'/
// 'Complete'/'Cancelled' are set directly by the user from there
// (no sub-tasks, same as Permits).
export type SelectedSupervisionStatus = 'Planned' | 'Eligible' | 'In Progress' | 'Complete' | 'Cancelled'

export interface SelectedSupervisionActivity {
  // This activity instance's own row id -- what setSupervisionStatus
  // operates on. Same convention as SelectedServiceActivity.id/
  // SelectedPermit.id.
  id?: string
  activityId: string
  activityName: string
  monthlyRate: number
  startDate: string
  // Required (backend migration 0081) -- an activity with no end date
  // could reach Payment Plan with no way to actually create its
  // Financial Agreement, since that always needs one to build the
  // day-prorated monthly billing schedule.
  endDate: string
  status?: SelectedSupervisionStatus
  eligibilityMetAt?: string | null
  closedAt?: string | null
}

// A Permit picked at project setup (in the unified ServicePickerDialog) --
// the missing
// counterpart to SelectedServiceActivity/SelectedSupervisionActivity
// that Permits never had before. status starts 'Planned' and becomes
// 'Eligible' once its admin-defined prerequisite Design activities are
// all Complete (see PermitPrerequisite, Administration > Permits);
// 'In Progress'/'Complete'/'Cancelled' are set directly by the user --
// Permits have no sub-tasks, unlike Design.
export type SelectedPermitStatus = 'Planned' | 'Eligible' | 'In Progress' | 'Complete' | 'Cancelled'

export interface SelectedPermit {
  id: string
  permitId?: string | null
  permitName: string
  // Snapshotted from the catalog's fixedCost at selection time -- null
  // only for rows selected before permit pricing existed.
  permitPrice?: number | null
  status: SelectedPermitStatus
  eligibilityMetAt?: string | null
  closedAt?: string | null
}

export interface Project {
  id: string
  projectNo: string
  projectName: string
  description?: string
  // The project/plot address -- fills a Quotation/Contract document
  // template's address placeholder (see document_template_service.
  // MERGE_FIELD_CATALOG). Distinct from any of the client's own
  // ClientAddress rows.
  siteAddress?: string
  // Set once the client has confirmed `description` (the scope-of-work
  // text) via a signed document upload -- see ScopeOfWork below for
  // the full revision history behind it. The sole sign-off gating the
  // move out of the Requirement stage.
  scopeClientConfirmedAt?: string | null
  clientId: string
  service: string
  engineer: string
  currentStage: WorkflowStage
  progress: number
  priority: ProjectPriority
  startDate: string
  targetDate: string
  status: ProjectStatus
  // Granular pick from the service picker (services -> activities, each
  // with its own price) -- `service` above stays a comma-joined summary
  // for the many display-only spots that just need a label. Optional
  // because projects created before the picker existed, or where the
  // backend hasn't been extended to persist this yet, won't have it.
  selectedActivities?: SelectedServiceActivity[]
  serviceTotal?: number
  // The Supervision activities picked in the same unified service picker,
  // and their combined nominal monthly total (informational only, not
  // prorated -- the real billed schedule lives on the Supervision
  // financial agreement once one is created). supervisionStartDate/
  // supervisionEndDate are the overall Supervision engagement window,
  // captured separately from each activity's own startDate/endDate.
  // Optional for the same reasons as selectedActivities above.
  selectedSupervisionActivities?: SelectedSupervisionActivity[]
  supervisionMonthlyTotal?: number
  supervisionStartDate?: string | null
  supervisionEndDate?: string | null
  // Whether this project's workflow includes a Design and/or
  // Supervision stage -- derived server-side from which of
  // selectedActivities/selectedSupervisionActivities have rows, see
  // backend project_service.compute_stage_flags. Drives which of the
  // Design/Supervision stepper nodes and workspace tabs are shown.
  includesDesign: boolean
  includesSupervision: boolean
  // Permits this project needs to apply for, each with its own
  // eligibility/closure lifecycle. See SelectedPermit.
  selectedPermits?: SelectedPermit[]
}

export type ProjectViewMode = 'grid' | 'table'

// 'requirement' has no dedicated component of its own anymore -- the
// Workflow Progress stepper's "Scope" step still needs a tab-key value
// distinct from 'overview' (see ProjectWorkspacePage.vue) so navigating
// there always sets stageContext back to 'Requirement' even when the
// project has since moved on and activeTab was already sitting on
// 'overview' (a same-value assignment wouldn't otherwise trigger the
// watcher that updates stageContext); it renders the exact same
// ProjectOverviewTab as 'overview' does.
export type ProjectWorkspaceTabKey =
  | 'overview'
  | 'requirement'
  | 'documents'
  | 'design'
  | 'supervision'
  | 'government'
  | 'quotation'
  | 'payment-status'
  | 'contract'
  | 'tasks'

export interface ProjectWorkspaceTab {
  key: ProjectWorkspaceTabKey
  label: string
}

// One saved change to the Requirement stage's scope-of-work text --
// mirrors QuotationRevision (types/Quotation.ts), plus an optional
// attached document.
export interface ScopeRevision {
  id: string
  revision: string
  date: string
  changedBy: string
  summary: string
  hasDocument: boolean
  documentName?: string | null
}

export interface ScopeOfWork {
  description: string | null
  // Set once confirm_requirement_scope runs (see ProjectOverviewTab's
  // Save & Proceed) -- the sole sign-off required before the project can
  // leave the Requirement stage.
  scopeClientConfirmedAt?: string | null
  revisions: ScopeRevision[]
}

export interface HandoverChecklistItem {
  id: string
  sourceType: 'Design' | 'Permit' | 'Supervision'
  title: string
  completedAt: string
}

// Populated (checklist non-empty) once every planned Design/Permit/
// Supervision item is Complete/Cancelled AND the project's current
// value is fully paid (see project_service.try_complete_project) --
// handoverSentAt is set at that point (project_service.
// notify_handover_ready), before staff have confirmed anything; it's
// what gates the "Confirm Hand-over" signed-document upload action
// being available. handoverAcknowledgedAt is set once that upload is
// confirmed, the moment project.status flips to 'Completed'.
export interface HandoverStatus {
  handoverSentAt?: string | null
  handoverAcknowledgedAt?: string | null
  checklist: HandoverChecklistItem[]
}
