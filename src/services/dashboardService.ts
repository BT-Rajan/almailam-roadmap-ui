import { apiClient, asError } from '@/services/httpClient'
import type { ProjectStatus } from '@/types/Project'
import type { TaskPriority, TaskStatus } from '@/types/Task'

// One request per dashboard tab: ready-made figures and short lists
// computed by the server (backend dashboard_service.py) -- the dashboard
// no longer downloads every client/project/task/document/payment to count
// them in the browser.

export interface DashboardClientsData {
  total: number
  active: number
  inactive: number
  onboarding: number
  recentClients: { id: string; name: string; type: string; status: 'Active' | 'Inactive'; city: string; createdDate: string }[]
}

export interface DashboardProjectsData {
  total: number
  active: number
  onHold: number
  recentProjects: { id: string; name: string; client: string; status: ProjectStatus; progress: number; dueDate: string; siteAddress?: string | null }[]
  pendingTasksTotal: number
  pendingTasks: { id: string; title: string; project: string; priority: TaskPriority; assignee: string; dueDate: string; status: TaskStatus }[]
  documentsTotal: number
  recentDocuments: { id: string; name: string; project: string; type: string; uploadedAt: string; uploadedBy: string; size: string | null }[]
}

export interface DashboardContractRow {
  contractNo: string
  projectId: string
  project: string
  expiryDate: string
}

export interface DashboardDeadlinesData {
  overdueTasks: number
  upcomingDeadlines: { id: string; title: string; project: string; dueDate: string; priority: TaskPriority }[]
  contractsExpiringSoon: DashboardContractRow[]
  contractsNotRenewed: DashboardContractRow[]
}

export interface DashboardFinancialsData {
  totalPending: number
  totalOverdue: number
  overdueAgreements: { id: string; projectId: string; project: string; client: string; overdueAmount: number; currency: string }[]
}

async function get<T>(tab: string): Promise<T> {
  try {
    return await apiClient.get<T>(`/api/dashboard/${tab}`)
  } catch (error) {
    throw asError(error, 'Failed to load the dashboard')
  }
}

export const dashboardService = {
  getClients: () => get<DashboardClientsData>('clients'),
  getProjects: () => get<DashboardProjectsData>('projects'),
  getDeadlines: () => get<DashboardDeadlinesData>('deadlines'),
  getFinancials: () => get<DashboardFinancialsData>('financials'),
}
