import { defineStore } from 'pinia'

import { notificationService } from '@/services/notificationService'
import type { AppNotification, NotificationGroup, NotificationGroupLabel } from '@/types/Notification'

interface NotificationStoreState {
  notifications: AppNotification[]
  isDrawerOpen: boolean
  isLoading: boolean
  error: string | undefined
}

function startOfDay(date: Date): number {
  const copy = new Date(date)
  copy.setHours(0, 0, 0, 0)
  return copy.getTime()
}

function groupLabelFor(isoDate: string): NotificationGroupLabel {
  const today = startOfDay(new Date())
  const target = startOfDay(new Date(isoDate))
  const diffDays = Math.round((today - target) / 86_400_000)

  if (diffDays <= 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  return 'Earlier'
}

export const useNotificationStore = defineStore('notification', {
  state: (): NotificationStoreState => ({
    notifications: [],
    isDrawerOpen: false,
    isLoading: false,
    error: undefined,
  }),

  getters: {
    unreadCount(state): number {
      return state.notifications.filter((notification) => !notification.read).length
    },

    hasUnread(): boolean {
      return this.unreadCount > 0
    },

    groupedNotifications(state): NotificationGroup[] {
      const order: NotificationGroupLabel[] = ['Today', 'Yesterday', 'Earlier']
      return order
        .map((label) => ({
          label,
          notifications: state.notifications.filter((notification) => groupLabelFor(notification.date) === label),
        }))
        .filter((group) => group.notifications.length > 0)
    },
  },

  actions: {
    async loadNotifications() {
      this.isLoading = true
      this.error = undefined
      try {
        this.notifications = await notificationService.getNotifications()
      } catch {
        this.error = 'Unable to load notifications. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    openDrawer() {
      this.isDrawerOpen = true
      if (this.notifications.length === 0 && !this.isLoading) {
        void this.loadNotifications()
      }
    },

    closeDrawer() {
      this.isDrawerOpen = false
    },

    toggleDrawer() {
      if (this.isDrawerOpen) {
        this.closeDrawer()
      } else {
        this.openDrawer()
      }
    },

    async markAsRead(notificationId: string) {
      const notification = this.notifications.find((item) => item.id === notificationId)
      if (!notification || notification.read) return
      notification.read = true
      try {
        await notificationService.markAsRead(notificationId)
      } catch {
        notification.read = false
      }
    },

    async markAllAsRead() {
      if (this.unreadCount === 0) return
      const previous = this.notifications.map((notification) => notification.read)
      this.notifications.forEach((notification) => {
        notification.read = true
      })
      try {
        await notificationService.markAllAsRead()
      } catch {
        this.notifications.forEach((notification, index) => {
          notification.read = previous[index] ?? notification.read
        })
      }
    },
  },
})
