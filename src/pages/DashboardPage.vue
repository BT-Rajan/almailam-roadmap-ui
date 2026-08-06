<script setup lang="ts">
import { Plus, FileUp, Zap } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ROUTE_NAMES } from '@/constants/routeNames'
import KPIWidget from '@/components/dashboard/KPIWidget.vue'
import StatisticsCard from '@/components/dashboard/StatisticsCard.vue'
import QuickActionCard from '@/components/dashboard/QuickActionCard.vue'
import ProjectSummaryCard from '@/components/dashboard/ProjectSummaryCard.vue'
import PendingTasksWidget from '@/components/dashboard/PendingTasksWidget.vue'
import UpcomingDeadlinesWidget from '@/components/dashboard/UpcomingDeadlinesWidget.vue'
import RecentDocumentsWidget from '@/components/dashboard/RecentDocumentsWidget.vue'
import { reportService } from '@/services/reportService'
import { useDocumentStore } from '@/stores/documentStore'
import { useProjectStore } from '@/stores/projectStore'
import { useTaskStore } from '@/stores/taskStore'
import type { KPI, StatisticItem, ProjectSummary, Task, Deadline, DocumentItem } from '@/types/Dashboard'
import type { ReportMetric } from '@/types/Report'
import type { ProjectStatus } from '@/types/Project'
import type { TaskPriority, TaskStatus } from '@/types/Task'

const router = useRouter()
const projectStore = useProjectStore()
const taskStore = useTaskStore()
const documentStore = useDocumentStore()

const summaryMetrics = ref<ReportMetric[]>([])
const isLoading = ref(true)

onMounted(async () => {
  try {
    const [metrics] = await Promise.all([
      reportService.getSummary(),
      projectStore.projects.length === 0 ? projectStore.loadProjects() : Promise.resolve(),
      taskStore.tasks.length === 0 ? taskStore.loadTasks() : Promise.resolve(),
      documentStore.documents.length === 0 ? documentStore.loadDocuments() : Promise.resolve(),
    ])
    summaryMetrics.value = metrics
  } finally {
    isLoading.value = false
  }
})

function metricValue(label: string): string | number {
  return summaryMetrics.value.find((metric) => metric.label === label)?.value ?? '—'
}

// Real KPI/statistics figures, computed from the same /api/reports/summary
// endpoint the Executive Report page uses -- this used to be hardcoded
// mock data (Total Projects: 5, Documents: 47, ...) that never changed no
// matter what was actually in the system.
const kpis = computed<KPI[]>(() => [
  { id: '1', label: 'Total Projects', value: metricValue('Total Projects') },
  { id: '2', label: 'Active Projects', value: metricValue('Active Projects') },
  { id: '3', label: 'Total Clients', value: metricValue('Total Clients') },
  { id: '4', label: 'Open Tasks', value: metricValue('Open Tasks') },
])

const statistics = computed<StatisticItem[]>(() => [
  { id: '1', label: 'Completed Projects', value: metricValue('Completed Projects'), icon: '✓', color: 'success' },
  { id: '2', label: 'Overdue Tasks', value: metricValue('Overdue Tasks'), icon: '⏱', color: 'danger' },
  {
    id: '3',
    label: 'Total Received',
    value: (() => {
      const metric = summaryMetrics.value.find((m) => m.label === 'Total Received')
      if (!metric) return '—'
      const amount = typeof metric.value === 'number' ? metric.value.toLocaleString() : metric.value
      return metric.unit ? `${amount} ${metric.unit}` : amount
    })(),
    icon: '📊',
    color: 'info',
  },
])

const PROJECT_STATUS_MAP: Record<ProjectStatus, ProjectSummary['status']> = {
  Active: 'active',
  'On Hold': 'on-hold',
  Completed: 'completed',
  Cancelled: 'completed',
}

// Most recently created projects (higher id = created later), not a fixed
// mock list -- real data, so this genuinely changes as projects are added.
const recentProjects = computed<ProjectSummary[]>(() =>
  [...projectStore.projects]
    .slice(-8)
    .reverse()
    .map((project) => ({
      id: project.id,
      name: project.projectName,
      client: projectStore.getClientById(project.clientId)?.companyName ?? 'Unknown Client',
      status: PROJECT_STATUS_MAP[project.status],
      progress: project.progress,
      dueDate: project.targetDate,
    })),
)

const TASK_STATUS_MAP: Record<TaskStatus, Task['status']> = {
  Pending: 'todo',
  'In Progress': 'in-progress',
  Completed: 'done',
}
const TASK_PRIORITY_MAP: Record<TaskPriority, Task['priority']> = {
  High: 'high',
  Medium: 'medium',
  Low: 'low',
}

function projectNameFor(projectId: string): string {
  return projectStore.projects.find((project) => project.id === projectId)?.projectName ?? 'Unknown Project'
}

const pendingTasks = computed<Task[]>(() =>
  taskStore.tasks
    .filter((task) => task.status !== 'Completed')
    .slice(0, 6)
    .map((task) => ({
      id: task.id,
      title: task.title,
      project: projectNameFor(task.projectId),
      priority: TASK_PRIORITY_MAP[task.priority],
      assignee: task.assignedTo,
      dueDate: task.dueDate,
      status: TASK_STATUS_MAP[task.status],
    })),
)

// Upcoming deadlines are derived from real task due dates within the next
// 14 days -- there is no separate "deadlines" concept in the backend, so
// rather than invent one, this reuses the same task data as above.
const upcomingDeadlines = computed<Deadline[]>(() => {
  const now = Date.now()
  const twoWeeksFromNow = now + 14 * 24 * 60 * 60 * 1000
  return taskStore.tasks
    .filter((task) => task.status !== 'Completed')
    .filter((task) => {
      const due = new Date(task.dueDate).getTime()
      return due >= now && due <= twoWeeksFromNow
    })
    .sort((a, b) => a.dueDate.localeCompare(b.dueDate))
    .slice(0, 5)
    .map((task) => ({
      id: task.id,
      title: task.title,
      project: projectNameFor(task.projectId),
      dueDate: task.dueDate,
      priority: task.priority === 'High' ? 'high' : task.priority === 'Medium' ? 'medium' : 'low',
      type: 'review' as const,
    }))
})

const recentDocuments = computed<DocumentItem[]>(() =>
  [...documentStore.documents]
    .sort((a, b) => b.uploadDate.localeCompare(a.uploadDate))
    .slice(0, 5)
    .map((document) => ({
      id: document.id,
      name: document.title,
      project: projectNameFor(document.projectId),
      type: document.type,
      uploadedAt: document.uploadDate,
      uploadedBy: document.uploadedBy,
      size: document.fileSize,
    })),
)

const handleQuickAction = (action: string) => {
  switch (action) {
    case 'new-project':
      router.push({ name: ROUTE_NAMES.PROJECT_NEW })
      break
    case 'new-task':
      router.push({ name: ROUTE_NAMES.TASKS })
      break
    case 'upload-document':
      router.push({ name: ROUTE_NAMES.DOCUMENTS })
      break
    case 'submit-form':
      router.push({ name: ROUTE_NAMES.GOVERNMENT_SUBMISSIONS })
      break
  }
}

const handleProjectClick = (projectId: string) => {
  router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId } })
}

const handleTaskClick = () => {
  router.push({ name: ROUTE_NAMES.MY_TASKS })
}

// KPI/Statistics cards link out to the page that best explains that
// number -- keyed by label since these report metrics don't carry a
// route of their own.
const KPI_ROUTES: Record<string, string> = {
  'Total Projects': ROUTE_NAMES.PROJECTS,
  'Active Projects': ROUTE_NAMES.PROJECTS,
  'Total Clients': ROUTE_NAMES.CLIENTS,
  'Open Tasks': ROUTE_NAMES.TASKS,
}

const STATISTIC_ROUTES: Record<string, string> = {
  'Completed Projects': ROUTE_NAMES.PROJECTS,
  'Overdue Tasks': ROUTE_NAMES.TASKS,
  'Total Received': ROUTE_NAMES.REPORT_EXECUTIVE,
}

function handleKpiClick(label: string): void {
  const routeName = KPI_ROUTES[label]
  if (routeName) router.push({ name: routeName })
}

function handleStatisticClick(label: string): void {
  const routeName = STATISTIC_ROUTES[label]
  if (routeName) router.push({ name: routeName })
}

function handleDeadlineClick(deadlineId: string): void {
  const deadline = upcomingDeadlines.value.find((item) => item.id === deadlineId)
  if (!deadline) return
  router.push({ name: ROUTE_NAMES.TASKS })
}

function handleDocumentClick(): void {
  router.push({ name: ROUTE_NAMES.DOCUMENTS })
}
</script>

<template>
  <div class="space-y-8 pb-8">
    <!-- Page Header -->
    <div>
      <h1 class="text-3xl font-bold text-neutral-900">Executive Dashboard</h1>
      <p class="text-neutral-500 mt-1">Welcome back. Here's your project overview.</p>
    </div>

    <!-- KPI Cards -->
    <div class="grid grid-cols-1 tablet:grid-cols-2 laptop:grid-cols-4 gap-4">
      <KPIWidget v-for="kpi in kpis" :key="kpi.id" :kpi="kpi" @click="handleKpiClick(kpi.label)" />
    </div>

    <!-- Statistics Row -->
    <div class="grid grid-cols-1 tablet:grid-cols-3 gap-4">
      <StatisticsCard v-for="stat in statistics" :key="stat.id" :statistic="stat" @click="handleStatisticClick(stat.label)" />
    </div>

    <!-- Quick Actions -->
    <div>
      <h2 class="text-lg font-semibold text-neutral-900 mb-4">Quick Actions</h2>
      <div class="grid grid-cols-2 tablet:grid-cols-4 gap-4">
        <QuickActionCard label="New Project" :icon="Plus" @click="handleQuickAction('new-project')" />
        <QuickActionCard label="New Task" :icon="Plus" color="success" @click="handleQuickAction('new-task')" />
        <QuickActionCard label="Upload Document" :icon="FileUp" color="info" @click="handleQuickAction('upload-document')" />
        <QuickActionCard label="Submit Form" :icon="Zap" color="warning" @click="handleQuickAction('submit-form')" />
      </div>
    </div>

    <!-- Projects Grid -->
    <div v-if="!isLoading && recentProjects.length > 0">
      <h2 class="text-lg font-semibold text-neutral-900 mb-4">Recent Projects</h2>
      <div class="grid grid-cols-1 tablet:grid-cols-2 laptop:grid-cols-4 gap-4">
        <ProjectSummaryCard v-for="project in recentProjects" :key="project.id" :project="project" @click="handleProjectClick(project.id)" />
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="grid grid-cols-1 laptop:grid-cols-3 gap-6">
      <!-- Left Column: Tasks -->
      <div class="laptop:col-span-2 space-y-6">
        <PendingTasksWidget :tasks="pendingTasks" @task-click="handleTaskClick" />
      </div>

      <!-- Right Column: Deadlines and Documents -->
      <div class="space-y-6">
        <UpcomingDeadlinesWidget :deadlines="upcomingDeadlines" @deadline-click="handleDeadlineClick" />
        <RecentDocumentsWidget :documents="recentDocuments" @document-click="handleDocumentClick" />
      </div>
    </div>
  </div>
</template>
