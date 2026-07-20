<script setup lang="ts">
import DetailPanel from '@/components/common/DetailPanel.vue'
import SelectBox from '@/components/common/SelectBox.vue'
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
}>()

const emit = defineEmits<{
  'status-change': [status: TaskStatus]
  'priority-change': [priority: TaskPriority]
  'severity-change': [severity: TaskSeverity]
  reassign: [assignee: string]
}>()

const STATUS_OPTIONS: SelectOption[] = [
  { label: 'Pending', value: 'Pending' },
  { label: 'In Progress', value: 'In Progress' },
  { label: 'Completed', value: 'Completed' },
]

const PRIORITY_OPTIONS: SelectOption[] = [
  { label: 'High', value: 'High' },
  { label: 'Medium', value: 'Medium' },
  { label: 'Low', value: 'Low' },
]

const SEVERITY_OPTIONS: SelectOption[] = [
  { label: 'Critical', value: 'Critical' },
  { label: 'Major', value: 'Major' },
  { label: 'Minor', value: 'Minor' },
]

const details = [
  { label: 'Project', value: props.projectName },
  { label: 'Completion Date & Time', value: formatTaskDueDateTime(props.task) },
]
</script>

<template>
  <div class="flex flex-col gap-5">
    <div class="flex flex-wrap items-center gap-2">
      <TaskStatusBadge :status="task.status" />
      <TaskPriorityBadge :priority="task.priority" />
      <TaskSeverityBadge :severity="task.severity" />
      <span v-if="isTaskOverdue(task)" class="text-xs font-medium text-danger-700">Overdue</span>
    </div>

    <p class="text-base font-semibold leading-snug text-neutral-800">{{ task.title }}</p>

    <DetailPanel title="Task Details" :items="details" />

    <TaskAssignmentCard :assigned-to="task.assignedTo" @reassign="emit('reassign', $event)" />

    <div class="flex flex-col gap-4 rounded-xl border border-border-light bg-bg-card p-4">
      <SelectBox
        :model-value="task.status"
        :options="STATUS_OPTIONS"
        label="Status"
        @update:model-value="emit('status-change', $event as TaskStatus)"
      />
      <SelectBox
        :model-value="task.priority"
        :options="PRIORITY_OPTIONS"
        label="Priority"
        @update:model-value="emit('priority-change', $event as TaskPriority)"
      />
      <SelectBox
        :model-value="task.severity"
        :options="SEVERITY_OPTIONS"
        label="Severity"
        @update:model-value="emit('severity-change', $event as TaskSeverity)"
      />
    </div>
  </div>
</template>
