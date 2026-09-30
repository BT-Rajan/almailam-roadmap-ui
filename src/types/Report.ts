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

export interface ReportPeriod {
  startDate: string
  endDate: string
}

export type ReportBucket = 'day' | 'week' | 'month' | 'year'

export interface ExecutiveSummary {
  period: ReportPeriod
  bucket: ReportBucket
  currency: string
  kpis: {
    newProjects: number
    projectsCompleted: number
    activeProjectsNow: number
    onHoldProjectsNow: number
    newClients: number
    contractsSigned: number
    contractsSignedValue: number
    cashReceived: number
    refunded: number
    netCash: number
    billed: number
    collectedOfBilled: number
    collectionRate: number | null
    outstandingNow: number
    overdueNow: number
    tasksCompleted: number
    tasksOnTimeRate: number | null
    openTasksNow: number
    overdueTasksNow: number
  }
  cashFlow: { categories: string[]; received: number[]; billed: number[] }
  projectFlow: { categories: string[]; started: number[]; completed: number[] }
  projectStatusNow: { label: string; value: number }[]
  topClients: { clientName: string; received: number; payments: number }[]
}

export type ScheduleHealth = 'on-track' | 'at-risk' | 'late' | 'completed' | 'cancelled' | 'on-hold'

export interface ProjectPerformance {
  period: ReportPeriod
  bucket: ReportBucket
  project: { projectNo: string; projectName: string; clientName: string; engineer: string; status: string; currentStage: string }
  schedule: {
    startDate: string
    targetDate: string
    totalDays: number
    timeElapsedPercent: number
    progressPercent: number
    daysToTarget: number
    health: ScheduleHealth
  }
  tasks: {
    byStatus: { label: string; value: number }[]
    total: number
    open: number
    overdue: number
    completedInPeriod: number
    onTimeRate: number | null
    overdueList: { taskNo: string; title: string; assignee: string; dueDate: string; daysLate: number }[]
  }
  money: {
    streams: {
      stream: string
      currency: string
      contractAmount: number
      received: number
      outstanding: number
      overdue: number
      receivedInPeriod: number
      billedInPeriod: number
    }[]
    chartCurrency: string | null
    cashFlow: { categories: string[]; received: number[]; billed: number[] }
    upcoming: { stream: string; description: string; dueDate: string; amountDue: number; outstanding: number; currency: string; overdue: boolean }[]
  }
  documents: { label: string; value: number }[]
  submissions: { label: string; value: number }[]
}

export interface ActivityMember {
  userId: string
  name: string
  system: boolean
  actions: number
  activeDays: number
  projectsTouched: number
  created: number
  updated: number
  completed: number
  rejected: number
  deleted: number
  byArea: Record<string, number>
  lastActivity: string
}

export interface EmployeeActivityReport {
  period: ReportPeriod
  bucket: ReportBucket
  totals: { actions: number; systemActions: number; peopleActive: number; created: number; completed: number; deleted: number }
  series: { categories: string[]; actions: number[] }
  areas: { label: string; value: number }[]
  members: ActivityMember[]
}

export interface WorkloadMember {
  userId: string
  name: string
  role: string
  inactive: boolean
  activeProjects: number
  openTasks: number
  overdueTasks: number
  dueSoonTasks: number
  laterTasks: number
  notStartedTasks: number
  oldestOverdueDays: number | null
  completedInPeriod: number
  onTimeRate: number | null
}

export interface TeamWorkloadReport {
  period: ReportPeriod
  dueSoonDays: number
  totals: {
    people: number
    peopleWithOpenWork: number
    peopleWithOverdue: number
    openTasks: number
    overdueTasks: number
    overdueShare: number | null
    dueSoonTasks: number
    completedInPeriod: number
    onTimeRate: number | null
    strandedTasks: number
  }
  members: WorkloadMember[]
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

export interface FinancialCurrencyBreakdown {
  currency: string
  totalReceived: number
  totalDue: number
  totalOutstanding: number
  totalOverdue: number
}

export interface FinancialPeriodSummary {
  startDate: string
  endDate: string
  paymentCount: number
  byCurrency: FinancialCurrencyBreakdown[]
}
