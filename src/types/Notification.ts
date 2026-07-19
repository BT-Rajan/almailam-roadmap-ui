export type NotificationCategory = 'Project' | 'Task' | 'Government' | 'AI' | 'System'

export interface NotificationLink {
  routeName: string
  params?: Record<string, string>
}

export interface AppNotification {
  id: string
  title: string
  message: string
  category: NotificationCategory
  date: string
  read: boolean
  link?: NotificationLink
}

export type NotificationGroupLabel = 'Today' | 'Yesterday' | 'Earlier'

export interface NotificationGroup {
  label: NotificationGroupLabel
  notifications: AppNotification[]
}
