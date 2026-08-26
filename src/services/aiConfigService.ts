import { apiClient } from '@/services/httpClient'
import type { AIConfiguration, AIProviderId, ProviderTestResult } from '@/types/AiConfig'

/**
 * Fetch AI configuration from backend API
 */
async function getConfiguration(): Promise<AIConfiguration> {
  try {
    return await apiClient.get<AIConfiguration>('/api/ai/configuration')
  } catch (error) {
    console.error('Failed to fetch AI configuration:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch configuration')
  }
}

/**
 * Save AI configuration via backend API
 */
async function saveConfiguration(config: AIConfiguration): Promise<AIConfiguration> {
  try {
    return await apiClient.post<AIConfiguration>('/api/ai/configuration', config)
  } catch (error) {
    console.error('Failed to save AI configuration:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to save configuration')
  }
}

/**
 * Test AI provider connection via backend API
 */
async function testProviderConnection(providerId: AIProviderId): Promise<ProviderTestResult> {
  try {
    return await apiClient.post<ProviderTestResult>(`/api/ai/providers/${providerId}/test-connection`, {})
  } catch (error) {
    console.error(`Failed to test provider connection:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to test connection')
  }
}

export const aiConfigService = {
  getConfiguration,
  saveConfiguration,
  testProviderConnection,
}
