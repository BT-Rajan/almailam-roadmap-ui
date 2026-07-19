export type TrendDirection = 'up' | 'down' | 'stable'

export interface KPI {
  id: string
  label: string
  value: string | number
  unit?: string
  trend?: {
    direction: TrendDirection
    percentage: number
    period: string
  }
}

export interface StatisticItem {
  id: string
  label: string
  value: string | number
  icon?: string
  color?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
}

export interface ProjectSummary {
  id: string
  name: string
  client: string
  status: 'draft' | 'active' | 'pending' | 'completed' | 'on-hold'
  progress: number
  dueDate: string
}

export interface Task {
  id: string
  title: string
  project: string
  priority: 'low' | 'medium' | 'high' | 'urgent'
  assignee: string
  dueDate: string
  status: 'todo' | 'in-progress' | 'review' | 'done'
}

export interface Activity {
  id: string
  type: 'project' | 'document' | 'submission' | 'task' | 'ai'
  title: string
  description?: string
  timestamp: string
  user: string
  icon?: string
}

export interface Deadline {
  id: string
  title: string
  project: string
  dueDate: string
  priority: 'low' | 'medium' | 'high'
  type: 'submission' | 'delivery' | 'approval' | 'review'
}

export interface DocumentItem {
  id: string
  name: string
  project: string
  type: string
  uploadedAt: string
  uploadedBy: string
  size: string
}

export interface AIInsight {
  id: string
  title: string
  description: string
  confidence: 'high' | 'medium' | 'low'
  action?: string
  timestamp: string
}
