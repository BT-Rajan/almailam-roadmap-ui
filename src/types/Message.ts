export type MessageChannel = 'Email' | 'SMS' | 'WhatsApp'

export type MessageStatus = 'Sent' | 'Failed'

export interface MessageTemplate {
  id: string
  name: string
  channel: MessageChannel
  body: string
}

export interface MessageLogEntry {
  id: string
  clientId: string
  channel: MessageChannel
  templateId?: string
  body: string
  projectId?: string
  status: MessageStatus
  sentAt: string
}

export interface SendMessagePayload {
  clientId: string
  channel: MessageChannel
  templateId?: string
  body: string
  projectId?: string
}
