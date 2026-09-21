<script setup lang="ts">
import { Activity, Layers, PauseCircle } from '@lucide/vue'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import StatisticsCard from '@/components/dashboard/StatisticsCard.vue'
import ProjectSummaryCard from '@/components/dashboard/ProjectSummaryCard.vue'
import PaginatedList from '@/components/common/PaginatedList.vue'
import PendingTasksWidget from '@/components/dashboard/PendingTasksWidget.vue'
import RecentDocumentsWidget from '@/components/dashboard/RecentDocumentsWidget.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useDocumentStore } from '@/stores/documentStore'
import { useProjectStore } from '@/stores/projectStore'
import { useTaskStore } from '@/stores/taskStore'
import type { StatisticItem, ProjectSummary, Task, DocumentItem } from '@/types/Dashboard'
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
  if (taskStore.needsFullLoad) void taskStore.loadTasks()
  if (documentStore.needsFullLoad) void documentStore.loadDocuments()
})

// Real counts from the same project list the "Recent Projects" grid
// below renders -- one source of truth, so the tile number and what's
// actually listed can never disagree. One consistent tile (StatisticsCard)
// for every figure here, same as DashboardFinancialsTab.vue's own -- this
// tab previously mixed StatisticsCard with a second, differently-styled
// KPIWidget for no functional reason.
const statistics = computed<StatisticItem[]>(() => [
  { id: 'total', label: t('dashboard.totalProjects'), value: projectStore.projects.length, icon: Layers, color: 'primary' },
  { id: 'active', label: t('dashboard.activeProjects'), value: projectStore.projects.filter((p) => p.status === 'Active').length, icon: Activity, color: 'success' },
  { id: 'on-hold', label: t('dashboard.onHoldProjects'), value: projectStore.projects.filter((p) => p.status === 'On Hold').length, icon: PauseCircle, color: 'warning' },
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
      <StatisticsCard v-for="stat in statistics" :key="stat.id" :statistic="stat" @click="handleKpiClick" />
    </div>

    <div v-if="recentProjects.length > 0" class="flex flex-col gap-3">
      <h2 class="text-sm font-semibold text-text-primary">{{ t('dashboard.recentProjects') }}</h2>
      <PaginatedList :items="recentProjects" :page-size="8" :page-size-options="[4, 8, 12, 24]">
        <template #default="{ items }">
          <div class="grid grid-cols-1 tablet:grid-cols-2 laptop:grid-cols-4 gap-4">
            <ProjectSummaryCard v-for="project in items" :key="project.id" :project="project" @click="handleProjectClick(project.id)" />
          </div>
        </template>
      </PaginatedList>
    </div>

    <div class="grid grid-cols-1 laptop:grid-cols-2 gap-6">
      <PendingTasksWidget :title="t('dashboard.pendingTasks')" :tasks="pendingTasks" @task-click="handleTaskClick" />
      <RecentDocumentsWidget :title="t('dashboard.recentDocuments')" :documents="recentDocuments" @document-click="handleDocumentClick" />
    </div>
  </div>
</template>
