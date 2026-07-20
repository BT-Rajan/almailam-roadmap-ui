import type { FinancialAuditEvent } from '@/types/Payment'

export const FINANCIAL_AUDIT_EVENTS: FinancialAuditEvent[] = [
  { id: 'FAE-001', agreementId: 'FA-001', eventType: 'Agreement Created', user: 'Layla Haddad', timestamp: '2025-12-20T09:00:00.000Z' },
  { id: 'FAE-002', agreementId: 'FA-001', eventType: 'Payment Received', user: 'Layla Haddad', timestamp: '2026-02-04T10:15:00.000Z', newValue: 'KWD 20,000 via Bank Transfer' },
  { id: 'FAE-003', agreementId: 'FA-001', eventType: 'Payment Allocated', user: 'Layla Haddad', timestamp: '2026-02-04T10:16:00.000Z', newValue: 'KWD 10,000 → Installment 1, KWD 10,000 → Installment 2' },
  { id: 'FAE-004', agreementId: 'FA-001', eventType: 'Payment Refunded', user: 'Ahmed Rashid', timestamp: '2026-02-10T13:00:00.000Z', previousValue: 'KWD 20,000 received', newValue: 'KWD 500 refunded', reason: 'Client requested a partial refund following a service scope adjustment for January.' },
  { id: 'FAE-005', agreementId: 'FA-001', eventType: 'Payment Received', user: 'Layla Haddad', timestamp: '2026-03-03T09:40:00.000Z', newValue: 'KWD 10,000 via Bank Transfer' },
  { id: 'FAE-006', agreementId: 'FA-001', eventType: 'Payment Received', user: 'Layla Haddad', timestamp: '2026-04-02T11:05:00.000Z', newValue: 'KWD 10,000 via Bank Transfer' },
  { id: 'FAE-007', agreementId: 'FA-001', eventType: 'Payment Received', user: 'Layla Haddad', timestamp: '2026-05-05T14:20:00.000Z', newValue: 'KWD 10,000 via Bank Transfer' },
  { id: 'FAE-008', agreementId: 'FA-001', eventType: 'Payment Received', user: 'Layla Haddad', timestamp: '2026-06-10T16:00:00.000Z', newValue: 'KWD 6,000 via Bank Transfer (partial — Installment 6)' },
  { id: 'FAE-009', agreementId: 'FA-002', eventType: 'Agreement Created', user: 'Ahmed Rashid', timestamp: '2026-01-15T09:00:00.000Z' },
  { id: 'FAE-010', agreementId: 'FA-002', eventType: 'Payment Received', user: 'Ahmed Rashid', timestamp: '2026-02-03T12:30:00.000Z', newValue: 'KWD 15,000 via Cheque' },
  { id: 'FAE-011', agreementId: 'FA-002', eventType: 'Adjustment Applied', user: 'Ahmed Rashid', timestamp: '2026-04-01T10:00:00.000Z', previousValue: 'Installment 2: KWD 15,000', newValue: 'Installment 2: KWD 17,000', reason: 'Additional scope agreed with the client — extended site visits for Q2.' },
  { id: 'FAE-012', agreementId: 'FA-003', eventType: 'Agreement Created', user: 'Mohammed Iqbal', timestamp: '2026-02-25T09:00:00.000Z' },
  { id: 'FAE-013', agreementId: 'FA-003', eventType: 'Payment Received', user: 'Mohammed Iqbal', timestamp: '2026-03-01T08:50:00.000Z', newValue: 'KWD 18,000 via Online Payment' },
]
