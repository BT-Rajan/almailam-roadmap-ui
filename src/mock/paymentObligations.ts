import type { PaymentObligation } from '@/types/Payment'

// Current date for this mock dataset is assumed to be 2026-07-20, so
// due dates before that are past-due and after are upcoming — this is
// what lets the obligations below cover Paid / Partially Overdue /
// Overdue / Scheduled without any manual overrides.
export const PAYMENT_OBLIGATIONS: PaymentObligation[] = [
  // FA-001 — PRJ-2026-001, 120,000 KWD over 12 monthly installments of 10,000
  { id: 'OBL-001-01', agreementId: 'FA-001', sequenceNumber: 1, description: 'Installment 1 — January', amountDue: 10000, dueDate: '2026-01-01', amountReceived: 9500 },
  { id: 'OBL-001-02', agreementId: 'FA-001', sequenceNumber: 2, description: 'Installment 2 — February', amountDue: 10000, dueDate: '2026-02-01', amountReceived: 10000, datePaid: '2026-02-04', paymentMethod: 'Bank Transfer', referenceNumber: 'TRF-88213' },
  { id: 'OBL-001-03', agreementId: 'FA-001', sequenceNumber: 3, description: 'Installment 3 — March', amountDue: 10000, dueDate: '2026-03-01', amountReceived: 10000, datePaid: '2026-03-03', paymentMethod: 'Bank Transfer', referenceNumber: 'TRF-88340' },
  { id: 'OBL-001-04', agreementId: 'FA-001', sequenceNumber: 4, description: 'Installment 4 — April', amountDue: 10000, dueDate: '2026-04-01', amountReceived: 10000, datePaid: '2026-04-02', paymentMethod: 'Bank Transfer', referenceNumber: 'TRF-88477' },
  { id: 'OBL-001-05', agreementId: 'FA-001', sequenceNumber: 5, description: 'Installment 5 — May', amountDue: 10000, dueDate: '2026-05-01', amountReceived: 10000, datePaid: '2026-05-05', paymentMethod: 'Bank Transfer', referenceNumber: 'TRF-88602' },
  { id: 'OBL-001-06', agreementId: 'FA-001', sequenceNumber: 6, description: 'Installment 6 — June', amountDue: 10000, dueDate: '2026-06-01', amountReceived: 6000, datePaid: '2026-06-10', paymentMethod: 'Bank Transfer', referenceNumber: 'TRF-88755' },
  { id: 'OBL-001-07', agreementId: 'FA-001', sequenceNumber: 7, description: 'Installment 7 — July', amountDue: 10000, dueDate: '2026-07-01', amountReceived: 0 },
  { id: 'OBL-001-08', agreementId: 'FA-001', sequenceNumber: 8, description: 'Installment 8 — August', amountDue: 10000, dueDate: '2026-08-01', amountReceived: 0 },
  { id: 'OBL-001-09', agreementId: 'FA-001', sequenceNumber: 9, description: 'Installment 9 — September', amountDue: 10000, dueDate: '2026-09-01', amountReceived: 0 },
  { id: 'OBL-001-10', agreementId: 'FA-001', sequenceNumber: 10, description: 'Installment 10 — October', amountDue: 10000, dueDate: '2026-10-01', amountReceived: 0 },
  { id: 'OBL-001-11', agreementId: 'FA-001', sequenceNumber: 11, description: 'Installment 11 — November', amountDue: 10000, dueDate: '2026-11-01', amountReceived: 0 },
  { id: 'OBL-001-12', agreementId: 'FA-001', sequenceNumber: 12, description: 'Installment 12 — December', amountDue: 10000, dueDate: '2026-12-01', amountReceived: 0 },

  // FA-002 — PRJ-2026-002, 45,000 KWD over 3 quarterly installments of 15,000
  { id: 'OBL-002-01', agreementId: 'FA-002', sequenceNumber: 1, description: 'Installment 1 — Q1', amountDue: 15000, dueDate: '2026-02-01', amountReceived: 15000, datePaid: '2026-02-03', paymentMethod: 'Cheque', referenceNumber: 'CHQ-4471' },
  { id: 'OBL-002-02', agreementId: 'FA-002', sequenceNumber: 2, description: 'Installment 2 — Q2', amountDue: 17000, dueDate: '2026-05-01', amountReceived: 0, notes: 'Includes 2,000 KWD scope adjustment (ADJ-001)' },
  { id: 'OBL-002-03', agreementId: 'FA-002', sequenceNumber: 3, description: 'Installment 3 — Q3', amountDue: 15000, dueDate: '2026-08-01', amountReceived: 0 },

  // FA-003 — PRJ-2026-004, 18,000 KWD one-time
  { id: 'OBL-003-01', agreementId: 'FA-003', sequenceNumber: 1, description: 'Full payment', amountDue: 18000, dueDate: '2026-03-01', amountReceived: 18000, datePaid: '2026-03-01', paymentMethod: 'Online Payment', referenceNumber: 'PGW-99012' },
]
