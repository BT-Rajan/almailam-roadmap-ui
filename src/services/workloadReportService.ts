import {
  WORKLOAD_BY_DEPARTMENT,
  WORKLOAD_DEPARTMENT_UTILIZATION,
  WORKLOAD_TEAM_MEMBERS,
  WORKLOAD_TEAM_METRICS,
  type WorkloadTeamMember,
} from '@/mock/workloadReport'
import type { ChartDataPoint, ReportMetric } from '@/types/Report'
import { simulateNetworkDelay } from '@/utils/mockDelay'

export interface WorkloadReportData {
  teamMetrics: ReportMetric[]
  workloadByDepartment: ChartDataPoint[]
  departmentUtilization: ChartDataPoint[]
  teamMembers: WorkloadTeamMember[]
}

async function getWorkloadReport(): Promise<WorkloadReportData> {
  await simulateNetworkDelay()
  return {
    teamMetrics: WORKLOAD_TEAM_METRICS,
    workloadByDepartment: WORKLOAD_BY_DEPARTMENT,
    departmentUtilization: WORKLOAD_DEPARTMENT_UTILIZATION,
    teamMembers: WORKLOAD_TEAM_MEMBERS,
  }
}

export const workloadReportService = {
  getWorkloadReport,
}
