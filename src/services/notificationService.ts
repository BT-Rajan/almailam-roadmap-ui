import { apiClient } from '@/services/httpClient'
import type { AppNotification } from '@/types/Notification'

/**
 * Fetch all notifications for current user from backend API
 */
async function getNotifications(): Promise<AppNotification[]> {
  try {
    return await apiClient.get<AppNotification[]>('/api/notifications')
  } catch (error) {
    console.error('Failed to fetch notifications:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch notifications')
  }
}

/**
 * Fetch unread notifications only from backend API
 */
async function getUnreadNotifications(): Promise<AppNotification[]> {
  try {
    return await apiClient.get<AppNotification[]>('/api/notifications?filter=unread')
  } catch (error) {
    console.error('Failed to fetch unread notifications:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch notifications')
  }
}

/**
 * Mark a notification as read via backend API
 */
async function markAsRead(notificationId: string): Promise<void> {
  try {
    await apiClient.patch(`/api/notifications/${notificationId}/read`)
  } catch (error) {
    console.error('Failed to mark notification as read:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to mark as read')
  }
}

/**
 * Mark all notifications as read via backend API
 */
async function markAllAsRead(): Promise<void> {
  try {
    await apiClient.patch('/api/notifications/read-all')
  } catch (error) {
    console.error('Failed to mark all notifications as read:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to mark all as read')
  }
}

/**
 * Delete a notification via backend API
 */
async function deleteNotification(notificationId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/notifications/${notificationId}`)
  } catch (error) {
    console.error('Failed to delete notification:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to delete notification')
  }
}

/**
 * Clear all notifications via backend API
 */
async function clearAllNotifications(): Promise<void> {
  try {
    await apiClient.delete('/api/notifications/clear-all')
  } catch (error) {
    console.error('Failed to clear all notifications:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to clear notifications')
  }
}

export const notificationService = {
  getNotifications,
  getUnreadNotifications,
  markAsRead,
  markAllAsRead,
  deleteNotification,
  clearAllNotifications,
}
