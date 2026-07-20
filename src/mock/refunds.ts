import type { Refund } from '@/types/Payment'

export const REFUNDS: Refund[] = [
  {
    id: 'REF-001',
    paymentId: 'PMT-001',
    agreementId: 'FA-001',
    refundAmount: 500,
    refundDate: '2026-02-10',
    reason: 'Client requested a partial refund following a service scope adjustment for January.',
    authorisingUser: 'Ahmed Rashid',
    reference: 'RFD-2231',
  },
]
