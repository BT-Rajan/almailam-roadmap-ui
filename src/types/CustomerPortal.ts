export interface CustomerProjectStatus {
  projectId: string
  projectName: string
  description: string
  clientName: string
  startDate: string
  expectedEndDate: string
  actualEndDate?: string
  status: 'planning' | 'active' | 'on-hold' | 'completed' | 'cancelled'
  progress: number
  summary: string
}

export interface ProjectMilestone {
  id: string
  title: string
  description?: string
  dueDate: string
  status: 'pending' | 'in-progress' | 'completed' | 'delayed'
  completedDate?: string
}

export interface ProjectDeliverable {
  id: string
  name: string
  description?: string
  type: string
  status: 'pending' | 'delivered' | 'approved' | 'revision'
  deliveryDate?: string
  approvalDate?: string
}

export interface ProjectUpdate {
  id: string
  date: string
  title: string
  description: string
  type: 'milestone' | 'deliverable' | 'status' | 'general'
  attachments?: string[]
}

export interface CustomerPortalSession {
  projectId: string
  mobileNumber: string
  lastAccessed: string
}

export interface CustomerVerification {
  mobileNumber: string
  projectId: string
  verified: boolean
  timestamp?: string
}
