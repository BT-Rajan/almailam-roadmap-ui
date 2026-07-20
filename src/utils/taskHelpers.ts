import type { BadgeVariant } from '@/types/Ui'
import type { Task, TaskPriority, TaskSeverity, TaskStatus } from '@/types/Task'
import { formatDateTime } from '@/utils/dateFormatter'

const PRIORITY_VARIANTS: Record<TaskPriority, BadgeVariant> = {
  High: 'danger',
  Medium: 'warning',
  Low: 'neutral',
}

const SEVERITY_VARIANTS: Record<TaskSeverity, BadgeVariant> = {
  Critical: 'danger',
  Major: 'warning',
  Minor: 'info',
}

const STATUS_VARIANTS: Record<TaskStatus, BadgeVariant> = {
  Pending: 'neutral',
  'In Progress': 'info',
  Completed: 'success',
}

const STATUS_ORDER: TaskStatus[] = ['Pending', 'In Progress', 'Completed']

export function getTaskPriorityVariant(priority: TaskPriority): BadgeVariant {
  return PRIORITY_VARIANTS[priority]
}

export function getTaskSeverityVariant(severity: TaskSeverity): BadgeVariant {
  return SEVERITY_VARIANTS[severity]
}

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
