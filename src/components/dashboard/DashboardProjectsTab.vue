<script setup lang="ts">
import { CheckCircle2 } from '@lucide/vue'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import KPIWidget from '@/components/dashboard/KPIWidget.vue'
import StatisticsCard from '@/components/dashboard/StatisticsCard.vue'
import ProjectSummaryCard from '@/components/dashboard/ProjectSummaryCard.vue'
import PendingTasksWidget from '@/components/dashboard/PendingTasksWidget.vue'
import RecentDocumentsWidget from '@/components/dashboard/RecentDocumentsWidget.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useDocumentStore } from '@/stores/documentStore'
import { useProjectStore } from '@/stores/projectStore'
import { useTaskStore } from '@/stores/taskStore'
import type { KPI, StatisticItem, ProjectSummary, Task, DocumentItem } from '@/types/Dashboard'
import type { ProjectStatus } from '@/types/Project'
import type { TaskPriority, TaskStatus } from '@/types/Task'

const router = useRouter()
const { t } = useI18n()
const projectStore = useProjectStore()
const taskStore = useTaskStore()
const documentStore = useDocumentStore()

// Guarded the same way loadAll()/loadData() elsewhere in the app already
// are: only fetch a store that isn't already populated and isn't already
// mid-fetch, so switching back to this tab after visiting another one
// (which unmounts and remounts this panel -- see DashboardPage.vue) never
// re-issues a request the first mount already made or has in flight.
onMounted(() => {
  if (projectStore.projects.length === 0 && !projectStore.isLoading) void projectStore.loadProjects()
  if (taskStore.tasks.length === 0 && !taskStore.isLoading) void taskStore.loadTasks()
  if (documentStore.documents.length === 0 && !documentStore.isLoading) void documentStore.loadDocuments()
})

// Real counts from the same project list the "Recent Projects" grid
// below renders -- one source of truth, so the KPI number and what's
// actually listed can never disagree.
const kpis = computed<KPI[]>(() => [
  { id: 'total', label: t('dashboard.totalProjects'), value: projectStore.projects.length },
  { id: 'active', label: t('dashboard.activeProjects'), value: projectStore.projects.filter((p) => p.status === 'Active').length },
])

const statistics = computed<StatisticItem[]>(() => [
  {
    id: 'on-hold',
    label: t('dashboard.onHoldProjects'),
    value: projectStore.projects.filter((p) => p.status === 'On Hold').length,
    icon: CheckCircle2,
    color: 'warning',
  },
])

const PROJECT_STATUS_MAP: Record<ProjectStatus, ProjectSummary['status']> = {
  Active: 'active',
  'On Hold': 'on-hold',
  Cancelled: 'completed',
  Completed: 'completed',
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
  Preset: 'todo',
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

function handleProjectClick(projectId: string): void {
  router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId } })
}

function handleTaskClick(): void {
  router.push({ name: ROUTE_NAMES.MY_TASKS })
}

function handleDocumentClick(): void {
  router.push({ name: ROUTE_NAMES.DOCUMENTS })
}

function handleKpiClick(): void {
  router.push({ name: ROUTE_NAMES.PROJECTS })
}
</script>

<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 tablet:grid-cols-2 laptop:grid-cols-3 gap-4">
      <KPIWidget v-for="kpi in kpis" :key="kpi.id" :kpi="kpi" @click="handleKpiClick" />
      <StatisticsCard v-for="stat in statistics" :key="stat.id" :statistic="stat" @click="handleKpiClick" />
    </div>

    <div v-if="recentProjects.length > 0">
      <h2 class="text-lg font-semibold text-text-primary mb-4">{{ t('dashboard.recentProjects') }}</h2>
      <div class="grid grid-cols-1 tablet:grid-cols-2 laptop:grid-cols-4 gap-4">
        <ProjectSummaryCard v-for="project in recentProjects" :key="project.id" :project="project" @click="handleProjectClick(project.id)" />
      </div>
    </div>

    <div class="grid grid-cols-1 laptop:grid-cols-2 gap-6">
      <PendingTasksWidget :title="t('dashboard.pendingTasks')" :tasks="pendingTasks" @task-click="handleTaskClick" />
      <RecentDocumentsWidget :title="t('dashboard.recentDocuments')" :documents="recentDocuments" @document-click="handleDocumentClick" />
    </div>
  </div>
</template>
