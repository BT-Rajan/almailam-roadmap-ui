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

export interface FinancialPeriodSummary {
  startDate: string
  endDate: string
  totalReceived: number
  totalDue: number
  totalOutstanding: number
  totalOverdue: number
  paymentCount: number
}
