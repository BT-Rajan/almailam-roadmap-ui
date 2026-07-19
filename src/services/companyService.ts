import { COMPANY_SETTINGS } from '@/mock/companySettings'
import type { CompanySettings } from '@/types/CompanySettings'
import { simulateNetworkDelay } from '@/utils/mockDelay'

async function getCompanySettings(): Promise<CompanySettings> {
  await simulateNetworkDelay()
  return { ...COMPANY_SETTINGS }
}

async function saveCompanySettings(settings: CompanySettings): Promise<CompanySettings> {
  await simulateNetworkDelay()
  return { ...settings }
}

export const companyService = {
  getCompanySettings,
  saveCompanySettings,
}
