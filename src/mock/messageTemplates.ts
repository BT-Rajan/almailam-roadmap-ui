import type { MessageTemplate } from '@/types/Message'

export const MESSAGE_TEMPLATES: MessageTemplate[] = [
  {
    id: 'MTPL-001',
    name: 'Project Update',
    channel: 'Email',
    body: 'Dear {contactPerson},\n\nThank you for your continued partnership. We wanted to share a quick update on the current progress of your project. Everything is on track, and our team will follow up shortly with the next milestone details.\n\nPlease let us know if you have any questions.\n\nBest regards,\nAl Mailam Team',
  },
  {
    id: 'MTPL-002',
    name: 'Payment Reminder',
    channel: 'Email',
    body: 'Dear {contactPerson},\n\nThis is a friendly reminder that payment for the recent invoice is due. Kindly arrange settlement at your earliest convenience, or reach out if you have any questions regarding the invoice.\n\nThank you,\nAl Mailam Accounts Team',
  },
  {
    id: 'MTPL-003',
    name: 'Site Visit Confirmation',
    channel: 'SMS',
    body: 'Hi {contactPerson}, confirming our site visit is scheduled. Our engineer will contact you shortly before arrival. Thank you - Al Mailam',
  },
  {
    id: 'MTPL-004',
    name: 'Document Submission Reminder',
    channel: 'WhatsApp',
    body: 'Hello {contactPerson}, a quick reminder that we still need a few documents from you to proceed with your government submission. Please share them at your earliest convenience so we can avoid delays.',
  },
  {
    id: 'MTPL-005',
    name: 'Appointment Confirmation',
    channel: 'SMS',
    body: 'Hi {contactPerson}, your appointment with Al Mailam has been confirmed. We look forward to meeting you.',
  },
  {
    id: 'MTPL-006',
    name: 'Welcome Message',
    channel: 'WhatsApp',
    body: 'Welcome to Al Mailam, {contactPerson}! We are glad to be working with you and will keep you updated at every step of your project.',
  },
]
