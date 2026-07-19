import type { BadgeVariant } from '@/types/Ui'
import type { Quotation, QuotationStatus } from '@/types/Quotation'

const STATUS_VARIANTS: Record<QuotationStatus, BadgeVariant> = {
  Draft: 'primary',
  Sent: 'info',
  Approved: 'success',
  Rejected: 'danger',
  Expired: 'neutral',
}

export interface QuotationPricing {
  subtotal: number
  discount: number
  taxRatePercent: number
  taxAmount: number
  total: number
}

export function getQuotationStatusVariant(status: QuotationStatus): BadgeVariant {
  return STATUS_VARIANTS[status]
}

export function calculateQuotationPricing(quotation: Quotation): QuotationPricing {
  const subtotal = quotation.lineItems.reduce((sum, item) => sum + item.quantity * item.unitPrice, 0)
  const taxableAmount = subtotal - quotation.discountAmount
  const taxAmount = (taxableAmount * quotation.taxRatePercent) / 100

  return {
    subtotal,
    discount: quotation.discountAmount,
    taxRatePercent: quotation.taxRatePercent,
    taxAmount,
    total: taxableAmount + taxAmount,
  }
}
