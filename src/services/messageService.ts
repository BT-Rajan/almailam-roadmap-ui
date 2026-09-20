import { apiClient, asError } from '@/services/httpClient'
import type { MessageLogEntry, MessageTemplate, SendEmailPayload, SendMessagePayload } from '@/types/Message'

/**
 * Fetch all message templates from backend API
 */
async function getTemplates(): Promise<MessageTemplate[]> {
  try {
    return await apiClient.get<MessageTemplate[]>('/api/messages/templates')
  } catch (error) {
    console.error('Failed to fetch message templates:', error)
    throw asError(error, 'Failed to fetch templates')
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
    throw asError(error, 'Failed to fetch log')
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
    throw asError(error, 'Failed to send message')
  }
}

/**
 * Send a real email (with optional attachments) via backend API --
 * distinct from sendMessage above because it needs a multipart body
 * for the files, and because it actually delivers over SMTP instead
 * of just logging a claimed send (see message_service.send_email).
 */
async function sendEmail(payload: SendEmailPayload): Promise<MessageLogEntry> {
  const formData = new FormData()
  formData.append('clientId', payload.clientId)
  formData.append('subject', payload.subject)
  formData.append('body', payload.body)
  if (payload.projectId) formData.append('projectId', payload.projectId)
  for (const file of payload.files) formData.append('files', file)

  try {
    return await apiClient.postForm<MessageLogEntry>('/api/messages/send-email', formData)
  } catch (error) {
    console.error('Failed to send email:', error)
    throw asError(error, 'Failed to send email')
  }
}

/**
 * Download one attachment from a logged message -- same Blob-based
 * pattern as documentService.downloadDocument.
 */
async function downloadAttachment(messageId: string, attachmentId: string): Promise<Blob> {
  try {
    return await apiClient.getBlob(`/api/messages/log/${messageId}/attachments/${attachmentId}/download`)
  } catch (error) {
    console.error(`Failed to download attachment ${attachmentId}:`, error)
    throw asError(error, 'Failed to download attachment')
  }
}

export const messageService = {
  getTemplates,
  getMessageLog,
  sendMessage,
  sendEmail,
  downloadAttachment,
}
