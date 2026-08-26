import { defineStore } from 'pinia'

import { aiConfigService } from '@/services/aiConfigService'
import type { AIConfiguration, AIProviderId } from '@/types/AiConfig'

interface AIConfigStoreState {
  config: AIConfiguration | undefined
  isLoading: boolean
  isSaving: boolean
  error: string | undefined
  testingProviderId: AIProviderId | undefined
  testResults: Partial<Record<AIProviderId, { success: boolean; message: string }>>
}

export const useAIConfigStore = defineStore('aiConfig', {
  state: (): AIConfigStoreState => ({
    config: undefined,
    isLoading: false,
    isSaving: false,
    error: undefined,
    testingProviderId: undefined,
    testResults: {},
  }),

  actions: {
    async loadConfiguration() {
      this.isLoading = true
      this.error = undefined
      try {
        this.config = await aiConfigService.getConfiguration()
      } catch {
        this.error = 'Unable to load AI configuration. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    updateField<K extends keyof AIConfiguration>(field: K, value: AIConfiguration[K]) {
      if (!this.config) return
      this.config = { ...this.config, [field]: value }
    },

    // Stages a raw key locally (see AIProviderConfig.apiKey) -- it isn't
    // sent to the server, and `status` isn't touched, until Save Changes
    // actually persists it (see saveConfiguration below).
    updateApiKey(providerId: AIProviderId, rawKey: string) {
      if (!this.config) return
      const preview = rawKey.length > 4 ? `••••••••${rawKey.slice(-4)}` : '••••••••'
      this.config = {
        ...this.config,
        providers: this.config.providers.map((provider) =>
          provider.id === providerId ? { ...provider, apiKey: rawKey, apiKeyMasked: preview } : provider,
        ),
      }
    },

    movePriority(providerId: AIProviderId, direction: 'up' | 'down') {
      if (!this.config) return
      const priority = [...this.config.providerPriority]
      const index = priority.indexOf(providerId)
      const targetIndex = direction === 'up' ? index - 1 : index + 1
      if (index === -1 || targetIndex < 0 || targetIndex >= priority.length) return
      ;[priority[index], priority[targetIndex]] = [priority[targetIndex], priority[index]]
      this.config = { ...this.config, providerPriority: priority }
    },

    async saveConfiguration(): Promise<boolean> {
      if (!this.config) return false
      this.isSaving = true
      try {
        this.config = await aiConfigService.saveConfiguration(this.config)
        return true
      } catch {
        this.error = 'Unable to save AI configuration. Please try again.'
        return false
      } finally {
        this.isSaving = false
      }
    },

    async testConnection(providerId: AIProviderId) {
      this.testingProviderId = providerId
      try {
        const result = await aiConfigService.testProviderConnection(providerId)
        this.testResults = { ...this.testResults, [providerId]: result }
        return result
      } finally {
        this.testingProviderId = undefined
      }
    },
  },
})
