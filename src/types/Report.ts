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

export interface ClientProjectSummary {
  projectNo: string
  projectName: string
  status: string
  currentStage: string
  progress: number
}

export interface ClientWithProjects {
  clientId: string
  clientName: string
  clientStatus: string
  projects: ClientProjectSummary[]
}

export interface PaymentLedgerEntry {
  paymentNo: string
  date: string
  projectNo: string
  projectName: string
  clientName: string
  service: string
  amount: number
  currency: string
  mode: string
  reference: string | null
  payer: string
}

export interface ProjectionByMonth {
  month: string
  amount: number
}

export interface ProjectionByProject {
  projectNo: string
  projectName: string
  amount: number
}

export interface ProjectionByService {
  service: string
  amount: number
}

export interface PaymentProjections {
  byMonth: ProjectionByMonth[]
  byProject: ProjectionByProject[]
  byService: ProjectionByService[]
}

export interface EmployeePerformance {
  userId: string
  employeeName: string
  assigned: number
  completed: number
  completionRate: number
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
