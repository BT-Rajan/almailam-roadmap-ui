import { MESSAGE_LOG } from '@/mock/messageLog'
import { MESSAGE_TEMPLATES } from '@/mock/messageTemplates'
import type { MessageLogEntry, MessageTemplate, SendMessagePayload } from '@/types/Message'
import { simulateNetworkDelay } from '@/utils/mockDelay'

// In-memory log so newly sent messages persist for the rest of the
// session, same "mock service holds its own working copy" convention
// as the other Phase services (see governmentSubmissionService).
const log: MessageLogEntry[] = [...MESSAGE_LOG]

async function getTemplates(): Promise<MessageTemplate[]> {
  await simulateNetworkDelay()
  return [...MESSAGE_TEMPLATES]
}

async function getMessageLog(): Promise<MessageLogEntry[]> {
  await simulateNetworkDelay()
  return [...log].sort((a, b) => new Date(b.sentAt).getTime() - new Date(a.sentAt).getTime())
}

async function sendMessage(payload: SendMessagePayload): Promise<MessageLogEntry> {
  await simulateNetworkDelay()

  const entry: MessageLogEntry = {
    id: `MSG-${String(log.length + 1).padStart(3, '0')}`,
    clientId: payload.clientId,
    channel: payload.channel,
    templateId: payload.templateId,
    body: payload.body,
    projectId: payload.projectId,
    status: 'Sent',
    sentAt: new Date().toISOString(),
  }

  log.push(entry)
  return entry
}

export const messageService = {
  getTemplates,
  getMessageLog,
  sendMessage,
}
