import type { BadgeVariant } from '@/types/Ui'
import type { Task, TaskStatus } from '@/types/Task'
import { formatDateTime } from '@/utils/dateFormatter'

const STATUS_VARIANTS: Record<TaskStatus, BadgeVariant> = {
  Preset: 'warning',
  Pending: 'neutral',
  'In Progress': 'info',
  Completed: 'success',
}

const STATUS_ORDER: TaskStatus[] = ['Preset', 'Pending', 'In Progress', 'Completed']

export function getTaskStatusVariant(status: TaskStatus): BadgeVariant {
  return STATUS_VARIANTS[status]
}

export function getNextTaskStatus(status: TaskStatus): TaskStatus | undefined {
  const currentIndex = STATUS_ORDER.indexOf(status)
  return STATUS_ORDER[currentIndex + 1]
}

export function isTaskOverdue(task: Task): boolean {
  if (task.status === 'Completed') return false
  const due = new Date(`${task.dueDate}T${task.dueTime || '23:59'}`)
  return due.getTime() < Date.now()
}

export function formatTaskDueDateTime(task: Task): string {
  return formatDateTime(`${task.dueDate}T${task.dueTime || '00:00'}`)
}
