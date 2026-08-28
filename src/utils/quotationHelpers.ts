import type { BadgeVariant } from '@/types/Ui'
import type { Quotation, QuotationStatus } from '@/types/Quotation'

const STATUS_VARIANTS: Record<QuotationStatus, BadgeVariant> = {
  Draft: 'primary',
  Approved: 'success',
  Rejected: 'danger',
  Expired: 'neutral',
}

export interface QuotationPricing {
  subtotal: number
  discount: number
  total: number
}

export function getQuotationStatusVariant(status: QuotationStatus): BadgeVariant {
  return STATUS_VARIANTS[status]
}

export function calculateQuotationPricing(quotation: Quotation): QuotationPricing {
  const subtotal = quotation.lineItems.reduce((sum, item) => sum + item.quantity * item.unitPrice, 0)

  return {
    subtotal,
    discount: quotation.discountAmount,
    total: subtotal - quotation.discountAmount,
  }
}
