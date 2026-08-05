import { apiClient } from '@/services/httpClient'
import type { MessageLogEntry, MessageTemplate, SendMessagePayload } from '@/types/Message'

/**
 * Fetch all message templates from backend API
 */
async function getTemplates(): Promise<MessageTemplate[]> {
  try {
    return await apiClient.get<MessageTemplate[]>('/api/messages/templates')
  } catch (error) {
    console.error('Failed to fetch message templates:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch templates')
  }
}

/**
 * Fetch message log/history from backend API
 */
async function getMessageLog(): Promise<MessageLogEntry[]> {
  try {
    return await apiClient.get<MessageLogEntry[]>('/api/messages/log')
  } catch (error) {
    console.error('Failed to fetch message log:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch log')
  }
}

/**
 * Send a message via backend API
 */
async function sendMessage(payload: SendMessagePayload): Promise<MessageLogEntry> {
  try {
    return await apiClient.post<MessageLogEntry>('/api/messages/send', payload)
  } catch (error) {
    console.error('Failed to send message:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to send message')
  }
}

export const messageService = {
  getTemplates,
  getMessageLog,
  sendMessage,
}
