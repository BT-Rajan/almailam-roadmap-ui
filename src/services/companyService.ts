import { apiClient } from '@/services/httpClient'
import type { CompanySettings } from '@/types/CompanySettings'

/**
 * Fetch company settings from backend API
 */
async function getCompanySettings(): Promise<CompanySettings> {
  try {
    return await apiClient.get<CompanySettings>('/api/company/settings')
  } catch (error) {
    console.error('Failed to fetch company settings:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch settings')
  }
}

/**
 * Save company settings via backend API
 */
async function saveCompanySettings(settings: CompanySettings): Promise<CompanySettings> {
  try {
    return await apiClient.post<CompanySettings>('/api/company/settings', settings)
  } catch (error) {
    console.error('Failed to save company settings:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to save settings')
  }
}

export const companyService = {
  getCompanySettings,
  saveCompanySettings,
}
