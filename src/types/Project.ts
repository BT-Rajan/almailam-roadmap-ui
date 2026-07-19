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
  clientId: string
  service: string
  engineer: string
  currentStage: WorkflowStage
  progress: number
  priority: ProjectPriority
  startDate: string
  targetDate: string
  status: ProjectStatus
}

export type ProjectViewMode = 'grid' | 'table'

export type ProjectWorkspaceTabKey =
  | 'overview'
  | 'timeline'
  | 'documents'
  | 'design'
  | 'government'
  | 'quotation'
  | 'contract'
  | 'tasks'
  | 'activity'

export interface ProjectWorkspaceTab {
  key: ProjectWorkspaceTabKey
  label: string
}
