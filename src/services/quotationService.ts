import { QUOTATIONS } from '@/mock/quotations'
import type { Quotation } from '@/types/Quotation'
import { simulateNetworkDelay } from '@/utils/mockDelay'

async function getQuotationsByProject(projectId: string): Promise<Quotation[]> {
  await simulateNetworkDelay()
  return QUOTATIONS.filter((quotation) => quotation.projectId === projectId)
}

async function getQuotationById(quotationId: string): Promise<Quotation | undefined> {
  await simulateNetworkDelay()
  return QUOTATIONS.find((quotation) => quotation.id === quotationId)
}

export const quotationService = {
  getQuotationsByProject,
  getQuotationById,
}
