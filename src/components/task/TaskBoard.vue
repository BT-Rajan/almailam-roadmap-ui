<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import EmptyState from '@/components/common/EmptyState.vue'
import TaskCard from '@/components/task/TaskCard.vue'
import type { Project } from '@/types/Project'
import type { Task, TaskStatus } from '@/types/Task'

const props = defineProps<{
  tasksByStatus: Record<TaskStatus, Task[]>
  getProjectById: (projectId: string) => Project | undefined
  getClientNameByProjectId: (projectId: string) => string
}>()

const emit = defineEmits<{
  open: [taskId: string]
  advance: [taskId: string]
}>()

const { t } = useI18n()

const COLUMNS = computed<{ status: TaskStatus; label: string }[]>(() => [
  { status: 'Pending', label: t('task.status.pending') },
  { status: 'In Progress', label: t('task.status.inProgress') },
  { status: 'Completed', label: t('task.status.completed') },
])

function projectName(projectId: string): string {
  return props.getProjectById(projectId)?.projectName ?? t('task.unknownProject')
}
</script>

<template>
  <div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
    <div
      v-for="column in COLUMNS"
      :key="column.status"
      class="flex flex-col gap-3 rounded-xl border border-border-light bg-bg-secondary p-3"
    >
      <div class="flex items-center justify-between px-1">
        <h3 class="text-sm font-semibold text-text-secondary">{{ column.label }}</h3>
        <span class="rounded-full bg-bg-card px-2 py-0.5 text-xs font-medium text-text-muted">
          {{ tasksByStatus[column.status].length }}
        </span>
      </div>

      <EmptyState
        v-if="tasksByStatus[column.status].length === 0"
        :title="t('task.board.noTasksTitle')"
        :description="t('task.board.noTasksDescription')"
      />

      <TaskCard
        v-for="task in tasksByStatus[column.status]"
        :key="task.id"
        :task="task"
        :project-name="projectName(task.projectId)"
        :client-name="getClientNameByProjectId(task.projectId)"
        @open="emit('open', $event)"
        @advance="emit('advance', $event)"
      />
    </div>
  </div>
</template>
