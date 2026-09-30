<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import EmptyState from '@/components/common/EmptyState.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import TaskCard from '@/components/task/TaskCard.vue'
import type { Project } from '@/types/Project'
import type { Task, TaskStatus } from '@/types/Task'

const props = defineProps<{
  tasksByStatus: Record<TaskStatus, Task[]>
  // How many tasks each column really has on the server -- the column
  // shows the first page and loads more on demand.
  totals: Record<TaskStatus, number>
  getProjectById: (projectId: string) => Project | undefined
  getClientNameByProjectId: (projectId: string) => string
}>()

const emit = defineEmits<{
  open: [taskId: string]
  advance: [taskId: string]
  loadMore: [status: TaskStatus]
}>()

const { t } = useI18n()

const COLUMNS = computed<{ status: TaskStatus; label: string }[]>(() => [
  { status: 'Preset', label: t('task.status.preset') },
  { status: 'Pending', label: t('task.status.pending') },
  { status: 'In Progress', label: t('task.status.inProgress') },
  { status: 'Completed', label: t('task.status.completed') },
])

// Prefer the names the server sends with each task; the lookups are only a
// fallback for tasks created locally before a refetch.
function projectName(task: Task): string {
  return task.projectName || props.getProjectById(task.projectId)?.projectName || t('task.unknownProject')
}
function clientName(task: Task): string {
  return task.clientName || props.getClientNameByProjectId(task.projectId)
}
</script>

<template>
  <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-4">
    <div
      v-for="column in COLUMNS"
      :key="column.status"
      class="flex flex-col gap-3 rounded-xl border border-border-light bg-bg-secondary p-3"
    >
      <div class="flex items-center justify-between px-1">
        <h3 class="text-sm font-semibold text-text-secondary">{{ column.label }}</h3>
        <span class="rounded-full bg-bg-card px-2 py-0.5 text-xs font-medium text-text-muted">
          {{ totals[column.status] }}
        </span>
      </div>

      <EmptyState
        v-if="tasksByStatus[column.status].length === 0"
        :title="t('task.board.noTasksTitle')"
        :description="t('task.board.noTasksDescription')"
      />

      <div class="flex flex-col gap-3">
        <TaskCard
          v-for="task in tasksByStatus[column.status]"
          :key="task.id"
          :task="task"
          :project-name="projectName(task)"
          :client-name="clientName(task)"
          @open="emit('open', $event)"
          @advance="emit('advance', $event)"
        />
      </div>
      <BaseButton
        v-if="tasksByStatus[column.status].length < totals[column.status]"
        variant="ghost"
        size="sm"
        class="self-center no-print"
        @click="emit('loadMore', column.status)"
      >
        {{ t('task.board.loadMore', { count: totals[column.status] - tasksByStatus[column.status].length }) }}
      </BaseButton>
    </div>
  </div>
</template>
