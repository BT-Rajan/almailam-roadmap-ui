<script setup lang="ts">
import { Activity, Layers, PauseCircle } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import StatisticsCard from '@/components/dashboard/StatisticsCard.vue'
import ProjectSummaryCard from '@/components/dashboard/ProjectSummaryCard.vue'
import PaginatedList from '@/components/common/PaginatedList.vue'
import PendingTasksWidget from '@/components/dashboard/PendingTasksWidget.vue'
import RecentDocumentsWidget from '@/components/dashboard/RecentDocumentsWidget.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import { useDashboardData } from '@/composables/useDashboardData'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { dashboardService } from '@/services/dashboardService'
import type { StatisticItem, ProjectSummary, Task, DocumentItem } from '@/types/Dashboard'
import type { ProjectStatus } from '@/types/Project'
import type { TaskPriority, TaskStatus } from '@/types/Task'

const router = useRouter()
const { t } = useI18n()

// Counts, the newest projects, the soonest-due open tasks and the latest
// documents all come ready-made from one server request -- this tab no
// longer downloads every project, task and document to count them.
const { data, error, isStale, reload } = useDashboardData('projects', dashboardService.getProjects)

const statistics = computed<StatisticItem[]>(() => [
  { id: 'total', label: t('dashboard.totalProjects'), value: data.value?.total ?? 0, icon: Layers, color: 'primary' },
  { id: 'active', label: t('dashboard.activeProjects'), value: data.value?.active ?? 0, icon: Activity, color: 'success' },
  { id: 'on-hold', label: t('dashboard.onHoldProjects'), value: data.value?.onHold ?? 0, icon: PauseCircle, color: 'warning' },
])

const PROJECT_STATUS_MAP: Record<ProjectStatus, ProjectSummary['status']> = {
  Active: 'active',
  'On Hold': 'on-hold',
  Cancelled: 'completed',
  Completed: 'completed',
}

// Newest projects first.
const recentProjects = computed<ProjectSummary[]>(() =>
  (data.value?.recentProjects ?? []).map((project) => ({
    id: project.id,
    name: project.name,
    client: project.client || t('project.unknownClient'),
    status: PROJECT_STATUS_MAP[project.status],
    progress: project.progress,
    dueDate: project.dueDate,
    siteAddress: project.siteAddress ?? undefined,
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

// Soonest-due open tasks (the full list is on My Tasks / Tasks).
const pendingTasks = computed<Task[]>(() =>
  (data.value?.pendingTasks ?? []).map((task) => ({
    id: task.id,
    title: task.title,
    project: task.project,
    priority: TASK_PRIORITY_MAP[task.priority],
    assignee: task.assignee,
    dueDate: task.dueDate,
    status: TASK_STATUS_MAP[task.status],
  })),
)

const recentDocuments = computed<DocumentItem[]>(() => data.value?.recentDocuments ?? [])

function handleProjectClick(projectId: string): void {
  router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId } })
}

// Opens that task, the same way every other task list does.
function handleTaskClick(taskId: string): void {
  router.push({ name: ROUTE_NAMES.TASK_WORKSPACE, params: { taskId } })
}

function handleDocumentClick(): void {
  router.push({ name: ROUTE_NAMES.DOCUMENTS })
}

function handleKpiClick(): void {
  router.push({ name: ROUTE_NAMES.PROJECTS })
}
</script>

<template>
  <ErrorState v-if="error" :description="error" @retry="reload" />
  <div v-else class="space-y-6">
    <p v-if="isStale" class="flex flex-wrap items-center gap-2 text-xs text-text-muted" role="status">
      {{ t('dashboard.staleNotice') }}
      <button type="button" class="font-medium text-primary-600 hover:text-primary-700" @click="reload">{{ t('dashboard.retry') }}</button>
    </p>
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
