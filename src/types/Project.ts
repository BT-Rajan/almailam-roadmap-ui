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
// on Project.includesDesign/includesSupervision below. See
// backend/app/models/project.py's WORKFLOW_STAGES comment.
export type WorkflowStage =
  | 'Requirement'
  | 'Quotation'
  | 'Contract'
  | 'Design'
  | 'Supervision'
  | 'Government Submission'

export type ProjectPriority = 'High' | 'Medium' | 'Low'

// One row per activity checked in the New Project wizard's final-step
// type-activity picker -- see Project.selectedTypeActivities above.
export interface ProjectSelectedTypeActivity {
  id: string
  categoryName: string
  activityName: string
  cost: number
  isCoveredByService: boolean
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
  // The engagement type(s) picked at the New Project wizard's final step
  // (Design/Supervision/etc, admin-managed under Administration > Type
  // Activity Catalog), and their own checklist breakdown -- a project can
  // span more than one category now (see includesDesign/
  // includesSupervision below). A checked activity whose
  // isCoveredByService is true is already priced under a
  // selectedActivities entry of the same name and doesn't add to
  // typeActivityTotal or get its own quotation line item a second time
  // -- see NewQuotationDialog.vue's formFromProject. Optional for the
  // same reasons as selectedActivities above.
  selectedTypeActivities?: ProjectSelectedTypeActivity[]
  typeActivityTotal?: number
  // Whether this project's workflow includes a Design and/or
  // Supervision stage -- derived server-side from selectedTypeActivities
  // (falling back to selectedActivities/service when none were picked),
  // see backend project_service.compute_stage_flags. Drives which of the
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
  | 'contract'
  | 'payments'
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
