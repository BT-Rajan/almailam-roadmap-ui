import type { Adjustment } from '@/types/Payment'

export const ADJUSTMENTS: Adjustment[] = [
  {
    id: 'ADJ-001',
    agreementId: 'FA-002',
    type: 'Increase',
    amount: 2000,
    reason: 'Additional scope agreed with the client — extended site visits for Q2.',
    authorisingUser: 'Ahmed Rashid',
    date: '2026-04-01',
  },
]
