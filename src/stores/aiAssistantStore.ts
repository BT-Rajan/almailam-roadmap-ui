import { defineStore } from 'pinia'

import { aiAssistantService } from '@/services/aiAssistantService'
import { useAIConfigStore } from '@/stores/aiConfigStore'
import type { AIInteraction } from '@/types/AiAssistant'

interface AIAssistantStoreState {
  isOpen: boolean
  currentPrompt: string
  selectedTemplateId: string | undefined
  history: AIInteraction[]
  isSending: boolean
  error: string | undefined
}

export const useAIAssistantStore = defineStore('aiAssistant', {
  state: (): AIAssistantStoreState => ({
    isOpen: false,
    currentPrompt: '',
    selectedTemplateId: undefined,
    history: [],
    isSending: false,
    error: undefined,
  }),

  actions: {
    open() {
      this.isOpen = true
    },

    close() {
      this.isOpen = false
    },

    toggle() {
      this.isOpen = !this.isOpen
    },

    setPrompt(text: string) {
      this.currentPrompt = text
    },

    applyTemplate(templateId: string) {
      const aiConfigStore = useAIConfigStore()
      const template = aiConfigStore.templates.find((item) => item.id === templateId)
      if (!template) return
      this.selectedTemplateId = templateId
      this.currentPrompt = template.template
    },

    async send() {
      const aiConfigStore = useAIConfigStore()
      const prompt = this.currentPrompt.trim()
      if (!prompt) return

      if (aiConfigStore.config && !aiConfigStore.config.isEnabled) {
        this.error = 'AI is currently disabled. Ask an administrator to enable it in AI Configuration.'
        return
      }

      this.isSending = true
      this.error = undefined
      try {
        const provider = aiConfigStore.config?.defaultProvider ?? 'claude'
        const templateName = aiConfigStore.templates.find((item) => item.id === this.selectedTemplateId)?.name
        const interaction = await aiAssistantService.getResponse(prompt, provider, templateName)
        this.history = [interaction, ...this.history]
        this.currentPrompt = ''
        this.selectedTemplateId = undefined
      } catch {
        this.error = 'AI service is currently unavailable. Please try again later.'
      } finally {
        this.isSending = false
      }
    },

    clearHistory() {
      this.history = []
    },

    dismissError() {
      this.error = undefined
    },
  },
})
