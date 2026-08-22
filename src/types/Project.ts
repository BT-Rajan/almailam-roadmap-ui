import type { SelectedServiceActivity } from '@/types/ServiceCatalog'

export type ProjectStatus = 'Active' | 'On Hold' | 'Completed' | 'Cancelled'

// "Correction" used to be its own stage (Review <-> Correction, a loop
// back and forth for what's really one review cycle). Merged into
// Review -- a correction cycle is logged as a note on the project's
// History instead of a separate stage. "Review" was itself renamed to
// "Execution & Tracking" and "Approval" dropped entirely -- the
// 23-step execution checklist and the 5-stage approval process stage
// gates are what actually happen during this stage. See
// backend/app/models/project.py's WORKFLOW_STAGES comment.
export type WorkflowStage =
  | 'Enquiry'
  | 'Quotation'
  | 'Contract'
  | 'Design'
  | 'Government Submission'
  | 'Execution & Tracking'
  | 'Completed'

export type ProjectPriority = 'High' | 'Medium' | 'Low'

export interface Project {
  id: string
  projectNo: string
  projectName: string
  description?: string
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
  // Permits the client confirmed they already hold, captured during project
  // setup. Each name here is mandatory to upload in the Documents tab --
  // see ProjectDocumentsTab's "Required Permit Documents" checklist. Optional
  // because most existing projects predate the permits step and because a
  // backend that hasn't been extended to persist this yet can just ignore it.
  requiredPermitDocuments?: string[]
  // Set once the project's status becomes Completed, cleared on reopen
  // -- see the Completion summary on the Overview tab.
  completedAt?: string | null
}

export type ProjectViewMode = 'grid' | 'table'

export type ProjectWorkspaceTabKey =
  | 'overview'
  | 'process'
  | 'documents'
  | 'design'
  | 'government'
  | 'quotation'
  | 'contract'
  | 'payments'
  | 'tasks'

export interface ProjectWorkspaceTab {
  key: ProjectWorkspaceTabKey
  label: string
}
