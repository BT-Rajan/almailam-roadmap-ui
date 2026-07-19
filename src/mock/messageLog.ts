import type { MessageLogEntry } from '@/types/Message'

export const MESSAGE_LOG: MessageLogEntry[] = [
  {
    id: 'MSG-001',
    clientId: 'CLT-001',
    channel: 'Email',
    templateId: 'MTPL-001',
    body: 'Dear Khalid Al Mazrouei,\n\nThank you for your continued partnership. We wanted to share a quick update on the current progress of your project...',
    projectId: 'PRJ-2026-001',
    status: 'Sent',
    sentAt: '2026-07-14T09:20:00.000Z',
  },
  {
    id: 'MSG-002',
    clientId: 'CLT-002',
    channel: 'WhatsApp',
    templateId: 'MTPL-004',
    body: 'Hello Sara Abdullah, a quick reminder that we still need a few documents from you to proceed with your government submission...',
    projectId: 'PRJ-2026-002',
    status: 'Sent',
    sentAt: '2026-07-15T13:05:00.000Z',
  },
  {
    id: 'MSG-003',
    clientId: 'CLT-003',
    channel: 'SMS',
    templateId: 'MTPL-005',
    body: 'Hi Omar Nasser, your appointment with Al Mailam has been confirmed. We look forward to meeting you.',
    status: 'Sent',
    sentAt: '2026-07-17T08:40:00.000Z',
  },
  {
    id: 'MSG-004',
    clientId: 'CLT-004',
    channel: 'Email',
    templateId: 'MTPL-002',
    body: 'Dear Fatima Al Suwaidi,\n\nThis is a friendly reminder that payment for the recent invoice is due...',
    projectId: 'PRJ-2026-004',
    status: 'Failed',
    sentAt: '2026-07-18T11:15:00.000Z',
  },
]
