import type { ClientAuditEvent } from '@/types/Client'

export const CLIENT_AUDIT_EVENTS: ClientAuditEvent[] = [
  {
    id: 'AUD-001',
    clientId: 'CLT-001',
    action: 'Client created',
    user: 'Mona Al Zaabi',
    timestamp: '2024-02-10T09:00:00+04:00',
  },
  {
    id: 'AUD-002',
    clientId: 'CLT-001',
    action: 'Trade licence document added',
    user: 'Mona Al Zaabi',
    timestamp: '2024-02-10T09:10:00+04:00',
  },
  {
    id: 'AUD-003',
    clientId: 'CLT-001',
    action: 'Verification completed',
    user: 'Mona Al Zaabi',
    timestamp: '2024-02-12T13:20:00+04:00',
    newValue: 'Ready',
  },
  {
    id: 'AUD-004',
    clientId: 'CLT-003',
    action: 'Client created',
    user: 'Omar Nasser',
    timestamp: '2025-01-08T10:00:00+04:00',
  },
  {
    id: 'AUD-005',
    clientId: 'CLT-003',
    action: 'Authorisation document added',
    user: 'Omar Nasser',
    timestamp: '2025-01-08T10:05:00+04:00',
  },
  {
    id: 'AUD-006',
    clientId: 'CLT-005',
    action: 'Client suspended review flagged',
    user: 'Rashid Al Marzooqi',
    timestamp: '2025-02-01T08:30:00+04:00',
    previousValue: 'Active',
    newValue: 'Documents Required',
    reason: 'Trade licence expired without renewal on file.',
  },
  {
    id: 'AUD-007',
    clientId: 'CLT-006',
    action: 'Client created',
    user: 'Rashid Al Marzooqi',
    timestamp: '2025-04-16T14:00:00+04:00',
  },
  {
    id: 'AUD-008',
    clientId: 'CLT-006',
    action: 'Consent recorded',
    user: 'Rashid Al Marzooqi',
    timestamp: '2025-04-16T14:05:00+04:00',
  },
]
