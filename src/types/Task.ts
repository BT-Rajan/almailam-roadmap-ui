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
}
