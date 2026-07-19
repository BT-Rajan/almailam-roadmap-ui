export type TaskPriority = 'High' | 'Medium' | 'Low'

export type TaskStatus = 'Pending' | 'In Progress' | 'Completed'

export interface Task {
  id: string
  projectId: string
  title: string
  assignedTo: string
  priority: TaskPriority
  dueDate: string
  status: TaskStatus
}
