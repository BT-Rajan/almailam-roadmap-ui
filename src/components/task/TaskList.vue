<script setup lang="ts">
import { ListChecks } from '@lucide/vue'

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
}>()

defineEmits<{
  open: [taskId: string]
}>()

function projectName(projectId: string): string {
  return props.getProjectById(projectId)?.projectName ?? 'Unknown Project'
}
</script>

<template>
  <Card :padded="false">
    <EmptyState
      v-if="tasks.length === 0"
      :icon="ListChecks"
      title="No tasks assigned"
      description="Tasks assigned to you will appear here."
    />

    <ul v-else class="divide-y divide-border-light">
      <li v-for="task in tasks" :key="task.id">
        <button
          type="button"
          class="flex w-full items-center justify-between gap-4 px-5 py-4 text-left transition-colors duration-fast hover:bg-bg-hover"
          @click="$emit('open', task.id)"
        >
          <div class="min-w-0">
            <p class="truncate text-sm font-semibold text-neutral-800">{{ task.title }}</p>
            <p class="truncate text-xs text-neutral-500">{{ projectName(task.projectId) }}</p>
          </div>

          <div class="flex shrink-0 items-center gap-3">
            <TaskPriorityBadge :priority="task.priority" />
            <TaskSeverityBadge :severity="task.severity" />
            <TaskStatusBadge :status="task.status" />
            <span
              class="w-32 text-right text-xs font-medium"
              :class="isTaskOverdue(task) ? 'text-danger-700' : 'text-neutral-400'"
            >
              {{ formatTaskDueDateTime(task) }}
            </span>
          </div>
        </button>
      </li>
    </ul>
  </Card>
</template>
