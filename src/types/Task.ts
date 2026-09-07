export type TaskPriority = 'High' | 'Medium' | 'Low'

export type TaskSeverity = 'Critical' | 'Major' | 'Minor'

export type TaskStatus = 'Pending' | 'In Progress' | 'Completed'

export interface Task {
  id: string
  projectId: string
  title: string
  assignedTo: string
  priority: TaskPriority
  severity: TaskSeverity
  dueDate: string
  dueTime: string
  status: TaskStatus
  // The Design activity this task belongs to, if any -- closing every
  // task linked to the same activity auto-closes it (see
  // ProjectSelectedActivity.status in Project.ts). Undefined for a
  // plain, unlinked to-do -- the vast majority of tasks.
  selectedActivityId?: string
}
