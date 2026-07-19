export interface ChartDataPoint {
  label: string
  value: number
  color?: string
}

export interface LineChartData {
  x: string
  value: number
  color?: string
}

export interface ReportMetric {
  label: string
  value: string | number
  unit?: string
  change?: {
    direction: 'up' | 'down'
    percentage: number
  }
  color?: string
}

export interface ReportSection {
  title: string
  description?: string
  metrics?: ReportMetric[]
}

export interface ProjectReportData {
  projectId: string
  projectName: string
  client: string
  startDate: string
  endDate: string
  status: 'active' | 'completed' | 'on-hold'
  progress: number
  budget: {
    allocated: number
    spent: number
    currency: string
  }
  team: {
    assigned: number
    utilization: number
  }
  deliverables: {
    total: number
    completed: number
    pending: number
  }
  risks: {
    count: number
    critical: number
  }
}

export interface TeamWorkloadData {
  memberId: string
  memberName: string
  role: string
  capacity: number
  allocation: number
  projects: number
  tasks: number
  overallocation?: boolean
}

export interface ExecutiveReportData {
  period: string
  generatedDate: string
  totalProjects: number
  activeProjects: number
  completedProjects: number
  totalTeamMembers: number
  averageProjectHealth: number
  budgetUtilization: number
  keyMetrics: ReportMetric[]
}
