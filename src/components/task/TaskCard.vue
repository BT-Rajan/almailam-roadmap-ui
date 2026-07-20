<script setup lang="ts">
import { ArrowRight } from '@lucide/vue'
import { computed } from 'vue'

import Avatar from '@/components/common/Avatar.vue'
import IconButton from '@/components/common/IconButton.vue'
import TaskPriorityBadge from '@/components/task/TaskPriorityBadge.vue'
import TaskSeverityBadge from '@/components/task/TaskSeverityBadge.vue'
import { formatTaskDueDateTime, getNextTaskStatus, isTaskOverdue } from '@/utils/taskHelpers'
import type { Task } from '@/types/Task'

const props = defineProps<{
  task: Task
  projectName: string
}>()

const emit = defineEmits<{
  open: [taskId: string]
  advance: [taskId: string]
}>()

const overdue = computed(() => isTaskOverdue(props.task))
const nextStatus = computed(() => getNextTaskStatus(props.task.status))
</script>

<template>
  <div
    class="flex cursor-pointer flex-col gap-3 rounded-xl border border-border-light bg-bg-card p-4 shadow-soft transition-shadow duration-normal hover:shadow-medium"
    @click="emit('open', task.id)"
  >
    <div class="flex items-start justify-between gap-2">
      <p class="text-sm font-semibold leading-snug text-neutral-800">{{ task.title }}</p>
      <div class="flex shrink-0 items-center gap-1">
        <TaskPriorityBadge :priority="task.priority" />
        <TaskSeverityBadge :severity="task.severity" />
      </div>
    </div>

    <p class="truncate text-xs text-neutral-500">{{ projectName }}</p>

    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <Avatar :name="task.assignedTo" size="sm" />
        <span class="text-xs text-neutral-600">{{ task.assignedTo }}</span>
      </div>

      <span class="text-xs font-medium" :class="overdue ? 'text-danger-700' : 'text-neutral-400'">
        {{ formatTaskDueDateTime(task) }}
      </span>
    </div>

    <IconButton
      v-if="nextStatus"
      :icon="ArrowRight"
      :label="`Move to ${nextStatus}`"
      size="sm"
      variant="primary"
      class="self-end"
      @click.stop="emit('advance', task.id)"
    />
  </div>
</template>
