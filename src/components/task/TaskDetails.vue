<script setup lang="ts">
import { AlertTriangle, Trash2 } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import DetailPanel from '@/components/common/DetailPanel.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TimePicker from '@/components/common/TimePicker.vue'
import TaskAssignmentCard from '@/components/task/TaskAssignmentCard.vue'
import TaskPriorityBadge from '@/components/task/TaskPriorityBadge.vue'
import TaskSeverityBadge from '@/components/task/TaskSeverityBadge.vue'
import TaskStatusBadge from '@/components/task/TaskStatusBadge.vue'
import { formatTaskDueDateTime, isTaskOverdue } from '@/utils/taskHelpers'
import type { Task, TaskPriority, TaskSeverity, TaskStatus } from '@/types/Task'
import type { SelectOption } from '@/types/Ui'

const props = defineProps<{
  task: Task
  projectName: string
  clientName: string
}>()

const emit = defineEmits<{
  'status-change': [status: TaskStatus]
  'priority-change': [priority: TaskPriority]
  'severity-change': [severity: TaskSeverity]
  'start-date-change': [startDate: string]
  'due-date-change': [dueDate: string]
  'due-time-change': [dueTime: string]
  reassign: [assignee: string]
  delete: []
}>()

const { t } = useI18n()

const STATUS_OPTIONS: SelectOption[] = [
  { label: 'Pending', value: 'Pending', labelKey: 'task.status.pending' },
  { label: 'In Progress', value: 'In Progress', labelKey: 'task.status.inProgress' },
  { label: 'Completed', value: 'Completed', labelKey: 'task.status.completed' },
]

const PRIORITY_OPTIONS: SelectOption[] = [
  { label: 'High', value: 'High', labelKey: 'task.priority.high' },
  { label: 'Medium', value: 'Medium', labelKey: 'task.priority.medium' },
  { label: 'Low', value: 'Low', labelKey: 'task.priority.low' },
]

const SEVERITY_OPTIONS: SelectOption[] = [
  { label: 'Critical', value: 'Critical', labelKey: 'task.severity.critical' },
  { label: 'Major', value: 'Major', labelKey: 'task.severity.major' },
  { label: 'Minor', value: 'Minor', labelKey: 'task.severity.minor' },
]

const details = computed(() => [
  { label: t('task.details.project'), value: props.projectName },
  { label: t('task.details.client'), value: props.clientName },
  { label: t('task.details.completionDateTime'), value: formatTaskDueDateTime(props.task) },
])
</script>

<template>
  <div class="flex flex-col gap-5">
    <div class="flex flex-wrap items-center gap-2">
      <TaskStatusBadge :status="task.status" />
      <TaskPriorityBadge :priority="task.priority" />
      <TaskSeverityBadge :severity="task.severity" />
      <span v-if="isTaskOverdue(task)" class="text-xs font-medium text-danger-700">{{ t('task.overdue') }}</span>
    </div>

    <p class="text-base font-semibold leading-snug text-text-primary">{{ task.title }}</p>

    <div v-if="task.status === 'Preset'" class="flex items-center gap-2 rounded-lg border border-warning-100 bg-warning-50 px-3 py-2.5 text-sm text-warning-700">
      <AlertTriangle class="h-4 w-4 shrink-0" />
      <span>{{ t('task.details.presetFlagMessage') }}</span>
    </div>

    <DetailPanel :title="t('task.details.projectDetailsTitle')" :items="details" />

    <TaskAssignmentCard :assigned-to="task.assignedTo" @reassign="emit('reassign', $event)" />

    <div class="flex flex-col gap-4 rounded-xl border border-border-light bg-bg-card p-4">
      <SelectBox
        :model-value="task.status"
        :options="STATUS_OPTIONS"
        :label="t('task.details.status')"
        @update:model-value="emit('status-change', $event as TaskStatus)"
      />
      <SelectBox
        :model-value="task.priority"
        :options="PRIORITY_OPTIONS"
        :label="t('task.details.priority')"
        @update:model-value="emit('priority-change', $event as TaskPriority)"
      />
      <SelectBox
        :model-value="task.severity"
        :options="SEVERITY_OPTIONS"
        :label="t('task.details.severity')"
        @update:model-value="emit('severity-change', $event as TaskSeverity)"
      />
    </div>

    <div class="flex flex-col gap-4 rounded-xl border border-border-light bg-bg-card p-4">
      <DatePicker
        :model-value="task.startDate ?? ''"
        :label="t('task.details.startDate')"
        @update:model-value="emit('start-date-change', $event)"
      />
      <div class="grid grid-cols-2 gap-4">
        <DatePicker
          :model-value="task.dueDate"
          :label="t('task.details.dueDate')"
          @update:model-value="emit('due-date-change', $event)"
        />
        <TimePicker
          :model-value="task.dueTime"
          :label="t('task.details.dueTime')"
          @update:model-value="emit('due-time-change', $event)"
        />
      </div>
    </div>

    <BaseButton variant="danger" size="sm" :icon="Trash2" class="self-start no-print" @click="emit('delete')">
      {{ t('task.details.delete') }}
    </BaseButton>
  </div>
</template>
