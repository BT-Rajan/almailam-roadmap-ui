import { apiClient } from '@/services/httpClient'
import type { EmailProviderId, EmailProviderPreset, EmailSettings, EmailSettingsTestResult } from '@/types/EmailSettings'

/**
 * Fetch the preset SMTP host/port values per provider, for the provider
 * picker to fill the form with on selection.
 */
async function getProviderPresets(): Promise<Record<EmailProviderId, EmailProviderPreset>> {
  try {
    return await apiClient.get<Record<EmailProviderId, EmailProviderPreset>>('/api/email/providers')
  } catch (error) {
    console.error('Failed to fetch email provider presets:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch provider presets')
  }
}

/**
 * Fetch email settings from backend API
 */
async function getSettings(): Promise<EmailSettings> {
  try {
    return await apiClient.get<EmailSettings>('/api/email/settings')
  } catch (error) {
    console.error('Failed to fetch email settings:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch settings')
  }
}

/**
 * Save email settings via backend API
 */
async function saveSettings(settings: EmailSettings): Promise<EmailSettings> {
  try {
    return await apiClient.post<EmailSettings>('/api/email/settings', settings)
  } catch (error) {
    console.error('Failed to save email settings:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to save settings')
  }
}

/**
 * Test the saved SMTP connection via backend API
 */
async function testConnection(): Promise<EmailSettingsTestResult> {
  try {
    return await apiClient.post<EmailSettingsTestResult>('/api/email/settings/test-connection', {})
  } catch (error) {
    console.error('Failed to test email connection:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to test connection')
  }
}

export const emailSettingsService = {
  getProviderPresets,
  getSettings,
  saveSettings,
  testConnection,
}
