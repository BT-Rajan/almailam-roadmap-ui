export type MessageChannel = 'Email' | 'SMS' | 'WhatsApp'

export type MessageStatus = 'Sent' | 'Failed'

export interface MessageTemplate {
  id: string
  name: string
  channel: MessageChannel
  body: string
}

export interface MessageAttachment {
  id: string
  filename: string
  sizeBytes: number | null
}

export interface MessageLogEntry {
  id: string
  clientId: string
  channel: MessageChannel
  templateId?: string
  subject?: string | null
  body: string
  projectId?: string
  status: MessageStatus
  errorMessage?: string | null
  attachments: MessageAttachment[]
  sentAt: string
}

export interface SendMessagePayload {
  clientId: string
  channel: MessageChannel
  templateId?: string
  body: string
  projectId?: string
}

export interface SendEmailPayload {
  clientId: string
  subject: string
  body: string
  projectId?: string
  files: File[]
}
