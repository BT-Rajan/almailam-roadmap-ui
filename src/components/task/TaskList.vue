<script setup lang="ts">
import { ListChecks } from '@lucide/vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import TaskPriorityBadge from '@/components/task/TaskPriorityBadge.vue'
import TaskSeverityBadge from '@/components/task/TaskSeverityBadge.vue'
import TaskStatusBadge from '@/components/task/TaskStatusBadge.vue'
import { formatTaskDueDateTime, isTaskOverdue } from '@/utils/taskHelpers'
import type { Project } from '@/types/Project'
import type { Task } from '@/types/Task'

const props = defineProps<{
  tasks: Task[]
  getProjectById: (projectId: string) => Project | undefined
  getClientNameByProjectId: (projectId: string) => string
}>()

defineEmits<{
  open: [taskId: string]
}>()

const { t } = useI18n()

function projectName(projectId: string): string {
  return props.getProjectById(projectId)?.projectName ?? t('task.unknownProject')
}
</script>

<template>
  <Card :padded="false">
    <EmptyState
      v-if="tasks.length === 0"
      :icon="ListChecks"
      :title="t('task.list.emptyTitle')"
      :description="t('task.list.emptyDescription')"
    />

    <ul v-else class="divide-y divide-border-light">
      <li v-for="task in tasks" :key="task.id">
        <button
          type="button"
          class="flex w-full items-center justify-between gap-4 px-5 py-4 text-left transition-colors duration-fast hover:bg-bg-hover"
          @click="$emit('open', task.id)"
        >
          <div class="min-w-0">
            <p class="truncate text-sm font-semibold text-text-primary">{{ task.title }}</p>
            <p class="truncate text-xs text-text-muted">
              {{ projectName(task.projectId) }} &middot; {{ getClientNameByProjectId(task.projectId) }}
            </p>
          </div>

          <div class="flex shrink-0 items-center gap-3">
            <TaskPriorityBadge :priority="task.priority" />
            <TaskSeverityBadge :severity="task.severity" />
            <TaskStatusBadge :status="task.status" />
            <span
              class="w-32 text-right text-xs font-medium"
              :class="isTaskOverdue(task) ? 'text-danger-700' : 'text-text-muted'"
            >
              {{ formatTaskDueDateTime(task) }}
            </span>
          </div>
        </button>
      </li>
    </ul>
  </Card>
</template>
