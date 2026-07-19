import { NOTIFICATIONS } from '@/mock/notifications'
import type { AppNotification } from '@/types/Notification'
import { simulateNetworkDelay } from '@/utils/mockDelay'

async function getNotifications(): Promise<AppNotification[]> {
  await simulateNetworkDelay()
  return [...NOTIFICATIONS].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
}

async function markAsRead(notificationId: string): Promise<void> {
  await simulateNetworkDelay(150)
  const notification = NOTIFICATIONS.find((item) => item.id === notificationId)
  if (notification) notification.read = true
}

async function markAllAsRead(): Promise<void> {
  await simulateNetworkDelay(150)
  NOTIFICATIONS.forEach((notification) => {
    notification.read = true
  })
}

export const notificationService = {
  getNotifications,
  markAsRead,
  markAllAsRead,
}
