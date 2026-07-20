import type { PaymentAllocation } from '@/types/Payment'

export const PAYMENT_ALLOCATIONS: PaymentAllocation[] = [
  { id: 'ALC-001', paymentId: 'PMT-001', obligationId: 'OBL-001-01', amountAllocated: 10000 },
  { id: 'ALC-002', paymentId: 'PMT-001', obligationId: 'OBL-001-02', amountAllocated: 10000 },
  { id: 'ALC-003', paymentId: 'PMT-002', obligationId: 'OBL-001-03', amountAllocated: 10000 },
  { id: 'ALC-004', paymentId: 'PMT-003', obligationId: 'OBL-001-04', amountAllocated: 10000 },
  { id: 'ALC-005', paymentId: 'PMT-004', obligationId: 'OBL-001-05', amountAllocated: 10000 },
  { id: 'ALC-006', paymentId: 'PMT-005', obligationId: 'OBL-001-06', amountAllocated: 6000 },
  { id: 'ALC-007', paymentId: 'PMT-006', obligationId: 'OBL-002-01', amountAllocated: 15000 },
  { id: 'ALC-008', paymentId: 'PMT-007', obligationId: 'OBL-003-01', amountAllocated: 18000 },
]
