<script setup lang="ts">
import { AlertTriangle, ArrowLeft, ArrowRight } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import Avatar from '@/components/common/Avatar.vue'
import IconButton from '@/components/common/IconButton.vue'
import { useLocale } from '@/composables/useLocale'
import { formatTaskDueDateTime, getNextTaskStatus, isTaskOverdue } from '@/utils/taskHelpers'
import type { Task, TaskStatus } from '@/types/Task'

const props = defineProps<{
  task: Task
  projectName: string
  clientName: string
}>()

const emit = defineEmits<{
  open: [taskId: string]
  advance: [taskId: string]
}>()

const { t } = useI18n()
const { isRtl } = useLocale()

// Points the way this action moves the task forward, which flips with
// reading direction.
const advanceIcon = computed(() => (isRtl.value ? ArrowLeft : ArrowRight))

const overdue = computed(() => isTaskOverdue(props.task))
const nextStatus = computed(() => getNextTaskStatus(props.task.status))

const STATUS_LABEL_KEYS: Record<TaskStatus, string> = {
  Preset: 'task.status.preset',
  Pending: 'task.status.pending',
  'In Progress': 'task.status.inProgress',
  Completed: 'task.status.completed',
}

const moveToLabel = computed(() => (nextStatus.value ? t('task.moveTo', { status: t(STATUS_LABEL_KEYS[nextStatus.value]) }) : ''))
</script>

<template>
  <div
    class="flex cursor-pointer flex-col gap-3 rounded-xl border border-border-light bg-bg-card p-4 shadow-soft transition-shadow duration-normal hover:shadow-medium"
    @click="emit('open', task.id)"
  >
    <div class="flex items-start justify-between gap-2">
      <p class="text-sm font-semibold leading-snug text-text-primary">{{ task.title }}</p>
    </div>

    <p class="truncate text-xs text-text-muted">{{ projectName }} &middot; {{ clientName }}</p>

    <p v-if="task.status === 'Preset'" class="flex items-center gap-1 text-xs font-medium text-warning-700">
      <AlertTriangle class="h-3.5 w-3.5 shrink-0" />
      <span>{{ t('task.presetFlag') }}</span>
    </p>

    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <Avatar :name="task.assignedTo" size="sm" />
        <span class="text-xs text-text-secondary">{{ task.assignedTo }}</span>
      </div>

      <span class="text-xs font-medium" :class="overdue ? 'text-danger-700' : 'text-text-muted'">
        {{ formatTaskDueDateTime(task) }}
      </span>
    </div>

    <IconButton
      v-if="nextStatus"
      :icon="advanceIcon"
      :label="moveToLabel"
      size="sm"
      variant="primary"
      class="self-end"
      @click.stop="emit('advance', task.id)"
    />
  </div>
</template>
