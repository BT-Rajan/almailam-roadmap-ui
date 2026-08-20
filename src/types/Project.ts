import type { SelectedServiceActivity } from '@/types/ServiceCatalog'

export type ProjectStatus = 'Active' | 'On Hold' | 'Completed' | 'Cancelled'

export type WorkflowStage =
  | 'Enquiry'
  | 'Quotation'
  | 'Contract'
  | 'Design'
  | 'Government Submission'
  | 'Review'
  | 'Correction'
  | 'Approval'
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
}

export type ProjectViewMode = 'grid' | 'table'

export type ProjectWorkspaceTabKey =
  | 'overview'
  | 'execution'
  | 'timeline'
  | 'documents'
  | 'design'
  | 'government'
  | 'quotation'
  | 'contract'
  | 'payments'
  | 'tasks'
  | 'activity'

export interface ProjectWorkspaceTab {
  key: ProjectWorkspaceTabKey
  label: string
}
