import type { WorkflowStage } from '@/types/Project'

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
  // The real workflow stage, same value staff see -- drives
  // ProjectStageProgress.vue's stepper. includesDesign/includesSupervision
  // mirror Project.includesDesign/includesSupervision, filtering the
  // stepper down to whichever of those two stages actually applies.
  currentStage: WorkflowStage
  includesDesign: boolean
  includesSupervision: boolean
  summary: string
  engineerName: string
  supportEmail: string
  supportPhone: string
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
}

export interface ProjectActivityGroup {
  serviceName: string
  activities: string[]
}

export interface UpcomingPayment {
  description: string
  amountDue: number
  amountReceived: number
  dueDate: string
}

export interface ProjectBudget {
  contractAmount: number
  currency: string
  totalPaid: number
  totalDue: number
  upcomingPayments: UpcomingPayment[]
}
