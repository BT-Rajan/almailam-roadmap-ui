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

    updateApiKey(providerId: AIProviderId, maskedKey: string) {
      if (!this.config) return
      // Deliberately leaves `status` untouched -- it reflects whether the
      // server's environment actually has a usable key for this provider,
      // which typing a value into this form does not change (see
      // AIProviderConfigOut.from_model on the backend). Flipping it to
      // 'connected' here would be a false "it worked" the instant you
      // click Update Key, before anything is even saved.
      this.config = {
        ...this.config,
        providers: this.config.providers.map((provider) =>
          provider.id === providerId ? { ...provider, apiKeyMasked: maskedKey } : provider,
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
