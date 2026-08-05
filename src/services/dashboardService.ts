import {
  DASHBOARD_ACTIVITIES,
  DASHBOARD_DEADLINES,
  DASHBOARD_DOCUMENTS,
  DASHBOARD_INSIGHTS,
  DASHBOARD_KPIS,
  DASHBOARD_PROJECTS,
  DASHBOARD_STATISTICS,
  DASHBOARD_TASKS,
} from '@/mock/dashboard'
import type {
  AIInsight,
  Activity,
  Deadline,
  DocumentItem,
  KPI,
  ProjectSummary,
  StatisticItem,
  Task,
} from '@/types/Dashboard'
import { simulateNetworkDelay } from '@/utils/mockDelay'

export interface DashboardData {
  kpis: KPI[]
  statistics: StatisticItem[]
  projects: ProjectSummary[]
  tasks: Task[]
  activities: Activity[]
  deadlines: Deadline[]
  documents: DocumentItem[]
  insights: AIInsight[]
}

async function getDashboardData(): Promise<DashboardData> {
  await simulateNetworkDelay()
  return {
    kpis: DASHBOARD_KPIS,
    statistics: DASHBOARD_STATISTICS,
    projects: DASHBOARD_PROJECTS,
    tasks: DASHBOARD_TASKS,
    activities: DASHBOARD_ACTIVITIES,
    deadlines: DASHBOARD_DEADLINES,
    documents: DASHBOARD_DOCUMENTS,
    insights: DASHBOARD_INSIGHTS,
  }
}

export const dashboardService = {
  getDashboardData,
}
