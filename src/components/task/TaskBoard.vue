<script setup lang="ts">
import EmptyState from '@/components/common/EmptyState.vue'
import TaskCard from '@/components/task/TaskCard.vue'
import type { Project } from '@/types/Project'
import type { Task, TaskStatus } from '@/types/Task'

const props = defineProps<{
  tasksByStatus: Record<TaskStatus, Task[]>
  getProjectById: (projectId: string) => Project | undefined
}>()

const emit = defineEmits<{
  open: [taskId: string]
  advance: [taskId: string]
}>()

const COLUMNS: { status: TaskStatus; label: string }[] = [
  { status: 'Pending', label: 'Pending' },
  { status: 'In Progress', label: 'In Progress' },
  { status: 'Completed', label: 'Completed' },
]

function projectName(projectId: string): string {
  return props.getProjectById(projectId)?.projectName ?? 'Unknown Project'
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
        <h3 class="text-sm font-semibold text-neutral-700">{{ column.label }}</h3>
        <span class="rounded-full bg-bg-card px-2 py-0.5 text-xs font-medium text-neutral-500">
          {{ tasksByStatus[column.status].length }}
        </span>
      </div>

      <EmptyState
        v-if="tasksByStatus[column.status].length === 0"
        title="No tasks"
        description="Nothing here right now."
      />

      <TaskCard
        v-for="task in tasksByStatus[column.status]"
        :key="task.id"
        :task="task"
        :project-name="projectName(task.projectId)"
        @open="emit('open', $event)"
        @advance="emit('advance', $event)"
      />
    </div>
  </div>
</template>
