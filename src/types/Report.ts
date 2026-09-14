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

export interface PaymentsReceivedByMonth {
  currency: string
  series: LineChartData[]
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
  currency: string
  amount: number
}

export interface ProjectionByProject {
  projectNo: string
  projectName: string
  currency: string
  amount: number
}

export interface ProjectionByService {
  service: string
  currency: string
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

export interface TeamWorkloadMember {
  userId: string
  name: string
  role: string
  activeProjects: number
  activeTasks: number
  overdueTasks: number
  allocationPercent: number
  overallocated: boolean
}

export interface TeamWorkload {
  members: TeamWorkloadMember[]
  totalMembers: number
  averageUtilization: number
  overallocatedCount: number
  capacityAvailable: number
}

export interface FinancialPeriodSummary {
  startDate: string
  endDate: string
  totalReceived: number
  totalDue: number
  totalOutstanding: number
  totalOverdue: number
  paymentCount: number
}
