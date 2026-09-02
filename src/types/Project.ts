import type { SelectedServiceActivity } from '@/types/ServiceCatalog'

// No "Completed" value -- a project never reaches a terminal "done"
// status, only Active/On Hold/Cancelled. See backend/app/models/
// project.py's PROJECT_STATUSES comment.
export type ProjectStatus = 'Active' | 'On Hold' | 'Cancelled'

// "Correction" used to be its own stage (Review <-> Correction, a loop
// back and forth for what's really one review cycle). Merged into
// Review -- a correction cycle is logged as a note on the project's
// History instead of a separate stage. "Enquiry" was itself renamed to
// "Requirement" -- it now has its own dedicated tab
// (ProjectRequirementTab.vue) for managing the scope-of-work text with
// revision history and an internal approval step. "Execution &
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

export type ProjectPriority = 'High' | 'Medium' | 'Low'

// One Supervision activity picked in the unified ServicePickerDialog at
// project setup -- see Project.selectedSupervisionActivities below.
// startDate/endDate are this activity's own window, independent of the
// project's overall supervisionStartDate/supervisionEndDate (both are
// captured separately, per the day-prorated monthly billing rules --
// see payment_calculations.generate_prorated_monthly_schedule).
export interface SelectedSupervisionActivity {
  activityId: string
  activityName: string
  monthlyRate: number
  startDate: string
  endDate?: string | null
}

// Internal approval of a project's scope-of-work text -- see
// ScopeOfWork below. Not client-facing.
export type ScopeStatus = 'Draft' | 'Approved'

export interface Project {
  id: string
  projectNo: string
  projectName: string
  description?: string
  scopeStatus: ScopeStatus
  scopeApprovedAt?: string | null
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
  // Permits the client confirmed they already hold, captured during project
  // setup. Each name here is mandatory to upload in the Documents tab --
  // see ProjectDocumentsTab's "Required Permit Documents" checklist. Optional
  // because most existing projects predate the permits step and because a
  // backend that hasn't been extended to persist this yet can just ignore it.
  requiredPermitDocuments?: string[]
}

export type ProjectViewMode = 'grid' | 'table'

export type ProjectWorkspaceTabKey =
  | 'overview'
  | 'requirement'
  | 'documents'
  | 'design'
  | 'supervision'
  | 'government'
  | 'quotation'
  | 'payment-plan'
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
  scopeStatus: ScopeStatus
  scopeApprovedAt?: string | null
  scopeApprovedBy?: string | null
  revisions: ScopeRevision[]
}
