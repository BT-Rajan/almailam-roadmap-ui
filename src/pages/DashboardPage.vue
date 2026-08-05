<script setup lang="ts">
import { Plus, FileUp, Zap } from '@lucide/vue'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ROUTE_NAMES } from '@/constants/routeNames'
import KPIWidget from '@/components/dashboard/KPIWidget.vue'
import StatisticsCard from '@/components/dashboard/StatisticsCard.vue'
import QuickActionCard from '@/components/dashboard/QuickActionCard.vue'
import ProjectSummaryCard from '@/components/dashboard/ProjectSummaryCard.vue'
import ActivityWidget from '@/components/dashboard/ActivityWidget.vue'
import PendingTasksWidget from '@/components/dashboard/PendingTasksWidget.vue'
import UpcomingDeadlinesWidget from '@/components/dashboard/UpcomingDeadlinesWidget.vue'
import RecentDocumentsWidget from '@/components/dashboard/RecentDocumentsWidget.vue'
import AIInsightWidget from '@/components/dashboard/AIInsightWidget.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import { dashboardService, type DashboardData } from '@/services/dashboardService'
import type { Activity, Deadline } from '@/types/Dashboard'

const router = useRouter()

const data = ref<DashboardData | undefined>(undefined)
const isLoading = ref(true)
const error = ref<string | undefined>(undefined)

async function loadData(): Promise<void> {
  isLoading.value = true
  error.value = undefined
  try {
    data.value = await dashboardService.getDashboardData()
  } catch {
    error.value = 'Unable to load the dashboard. Please try again.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadData)

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
// number — keyed by label since these mock summaries don't carry a
// route of their own.
const KPI_ROUTES: Record<string, string> = {
  'Total Projects': ROUTE_NAMES.PROJECTS,
  'Active Submissions': ROUTE_NAMES.GOVERNMENT_SUBMISSIONS,
  Documents: ROUTE_NAMES.DOCUMENTS,
  'Team Members': ROUTE_NAMES.ADMIN_USERS,
}

const STATISTIC_ROUTES: Record<string, string> = {
  'On Time': ROUTE_NAMES.REPORT_PROJECT,
  'Pending Review': ROUTE_NAMES.DOCUMENT_REVIEW,
  'Completed This Month': ROUTE_NAMES.PROJECTS,
}

const DEADLINE_TYPE_ROUTES: Record<Deadline['type'], string> = {
  submission: ROUTE_NAMES.GOVERNMENT_SUBMISSIONS,
  approval: ROUTE_NAMES.GOVERNMENT_SUBMISSIONS,
  review: ROUTE_NAMES.DOCUMENT_REVIEW,
  delivery: ROUTE_NAMES.PROJECTS,
}

const ACTIVITY_TYPE_ROUTES: Partial<Record<Activity['type'], string>> = {
  project: ROUTE_NAMES.PROJECTS,
  document: ROUTE_NAMES.DOCUMENTS,
  submission: ROUTE_NAMES.GOVERNMENT_SUBMISSIONS,
  task: ROUTE_NAMES.MY_TASKS,
  // 'ai' has no dedicated insights page yet, so it's left unmapped —
  // clicking it is a no-op rather than sending someone somewhere odd.
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
  const deadline = data.value?.deadlines.find((item) => item.id === deadlineId)
  if (!deadline) return
  router.push({ name: DEADLINE_TYPE_ROUTES[deadline.type] })
}

function handleDocumentClick(): void {
  router.push({ name: ROUTE_NAMES.DOCUMENTS })
}

function handleActivityClick(activity: Activity): void {
  const routeName = ACTIVITY_TYPE_ROUTES[activity.type]
  if (routeName) router.push({ name: routeName })
}

function handleInsightClick(): void {
  router.push({ name: ROUTE_NAMES.REPORT_EXECUTIVE })
}
</script>

<template>
  <div class="space-y-8 pb-8">
    <!-- Page Header -->
    <div>
      <h1 class="text-3xl font-bold text-neutral-900">Executive Dashboard</h1>
      <p class="text-neutral-500 mt-1">Welcome back. Here's your project overview.</p>
    </div>

    <ErrorState v-if="error" :description="error" @retry="loadData" />

    <template v-else-if="isLoading">
      <div class="grid grid-cols-1 tablet:grid-cols-2 laptop:grid-cols-4 gap-4">
        <div v-for="placeholder in 4" :key="placeholder" class="rounded-xl border border-border-light bg-bg-card p-5">
          <SkeletonLoader :rows="3" />
        </div>
      </div>
      <div class="rounded-xl border border-border-light bg-bg-card p-5">
        <SkeletonLoader :rows="8" />
      </div>
    </template>

    <template v-else-if="data">
      <!-- KPI Cards -->
      <div class="grid grid-cols-1 tablet:grid-cols-2 laptop:grid-cols-4 gap-4">
        <KPIWidget v-for="kpi in data.kpis" :key="kpi.id" :kpi="kpi" @click="handleKpiClick(kpi.label)" />
      </div>

      <!-- Statistics Row -->
      <div class="grid grid-cols-1 tablet:grid-cols-3 gap-4">
        <StatisticsCard v-for="stat in data.statistics" :key="stat.id" :statistic="stat" @click="handleStatisticClick(stat.label)" />
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
      <div>
        <h2 class="text-lg font-semibold text-neutral-900 mb-4">Recent Projects</h2>
        <div class="grid grid-cols-1 tablet:grid-cols-2 laptop:grid-cols-4 gap-4">
          <ProjectSummaryCard v-for="project in data.projects" :key="project.id" :project="project" @click="handleProjectClick(project.id)" />
        </div>
      </div>

      <!-- Main Content Grid -->
      <div class="grid grid-cols-1 laptop:grid-cols-3 gap-6">
        <!-- Left Column: Activity and Tasks -->
        <div class="laptop:col-span-2 space-y-6">
          <ActivityWidget :activities="data.activities" @activity-click="handleActivityClick" />
          <PendingTasksWidget :tasks="data.tasks" @task-click="handleTaskClick" />
        </div>

        <!-- Right Column: Deadlines, Documents, and AI -->
        <div class="space-y-6">
          <UpcomingDeadlinesWidget :deadlines="data.deadlines" @deadline-click="handleDeadlineClick" />
          <RecentDocumentsWidget :documents="data.documents" @document-click="handleDocumentClick" />
          <AIInsightWidget :insights="data.insights" @insight-click="handleInsightClick" @action-click="handleInsightClick" />
        </div>
      </div>
    </template>
  </div>
</template>
