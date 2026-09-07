import { defineStore } from 'pinia'

import { emailTemplateService } from '@/services/emailTemplateService'
import type { EmailTemplate, EmailTemplateKey } from '@/types/EmailTemplate'

interface EmailTemplateStoreState {
  templates: EmailTemplate[]
  isLoading: boolean
  error: string | undefined
}

export const useEmailTemplateStore = defineStore('emailTemplate', {
  state: (): EmailTemplateStoreState => ({
    templates: [],
    isLoading: false,
    error: undefined,
  }),

  getters: {
    byKey(state) {
      return (key: EmailTemplateKey): EmailTemplate | undefined => state.templates.find((template) => template.key === key)
    },
  },

  actions: {
    async loadTemplates() {
      this.isLoading = true
      this.error = undefined
      try {
        this.templates = await emailTemplateService.getTemplates()
      } catch {
        this.error = 'Unable to load email templates. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    async updateTemplate(key: EmailTemplateKey, subject: string, body: string): Promise<EmailTemplate> {
      const updated = await emailTemplateService.updateTemplate(key, subject, body)
      this.templates = this.templates.map((template) => (template.key === key ? updated : template))
      return updated
    },
  },
})
