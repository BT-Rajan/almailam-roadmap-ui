<script setup lang="ts">
import { Clock } from '@lucide/vue'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import StatisticsCard from '@/components/dashboard/StatisticsCard.vue'
import UpcomingDeadlinesWidget from '@/components/dashboard/UpcomingDeadlinesWidget.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useProjectStore } from '@/stores/projectStore'
import { useTaskStore } from '@/stores/taskStore'
import type { Deadline, StatisticItem } from '@/types/Dashboard'

const router = useRouter()
const { t } = useI18n()
const projectStore = useProjectStore()
const taskStore = useTaskStore()

// Deadlines are derived from task due dates, and each task's project name
// needs projectStore -- guarded the same way as the other tabs.
onMounted(() => {
  if (taskStore.tasks.length === 0 && !taskStore.isLoading) void taskStore.loadTasks()
  if (projectStore.projects.length === 0 && !projectStore.isLoading) void projectStore.loadProjects()
})

function projectNameFor(projectId: string): string {
  return projectStore.projects.find((project) => project.id === projectId)?.projectName ?? 'Unknown Project'
}

const today = computed(() => new Date().setHours(0, 0, 0, 0))

const statistics = computed<StatisticItem[]>(() => [
  {
    id: 'overdue',
    label: t('dashboard.overdueTasks'),
    value: taskStore.tasks.filter((task) => task.status !== 'Completed' && new Date(task.dueDate).getTime() < today.value).length,
    icon: Clock,
    color: 'danger',
  },
])

// There is no separate "deadlines" concept in the backend -- this reuses
// real task due dates, same convention as the old dashboard, just with
// more room to show them now that it has a whole tab instead of a
// sidebar slot.
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
    .slice(0, 15)
    .map((task) => ({
      id: task.id,
      title: task.title,
      project: projectNameFor(task.projectId),
      dueDate: task.dueDate,
      priority: task.priority === 'High' ? ('high' as const) : task.priority === 'Medium' ? ('medium' as const) : ('low' as const),
      type: 'review' as const,
    }))
})

function handleStatisticClick(): void {
  router.push({ name: ROUTE_NAMES.TASKS })
}

function handleDeadlineClick(): void {
  router.push({ name: ROUTE_NAMES.TASKS })
}
</script>

<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 tablet:grid-cols-3 gap-4">
      <StatisticsCard v-for="stat in statistics" :key="stat.id" :statistic="stat" @click="handleStatisticClick" />
    </div>

    <UpcomingDeadlinesWidget
      :title="t('dashboard.upcomingDeadlines')"
      :deadlines="upcomingDeadlines"
      :max-items="15"
      @deadline-click="handleDeadlineClick"
    />
  </div>
</template>
