import type { BadgeVariant } from '@/types/Ui'
import type { Task, TaskPriority, TaskStatus } from '@/types/Task'

const PRIORITY_VARIANTS: Record<TaskPriority, BadgeVariant> = {
  High: 'danger',
  Medium: 'warning',
  Low: 'neutral',
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

export function getTaskStatusVariant(status: TaskStatus): BadgeVariant {
  return STATUS_VARIANTS[status]
}

export function getNextTaskStatus(status: TaskStatus): TaskStatus | undefined {
  const currentIndex = STATUS_ORDER.indexOf(status)
  return STATUS_ORDER[currentIndex + 1]
}

export function isTaskOverdue(task: Task): boolean {
  if (task.status === 'Completed') return false
  const dueDate = new Date(task.dueDate)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return dueDate.getTime() < today.getTime()
}
