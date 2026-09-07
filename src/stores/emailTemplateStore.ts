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
      } catch (error) {
        // Surfaces the real backend message (e.g. a permission error or a
        // genuine server fault) instead of a fixed generic string --
        // EmailTemplatesPanel.vue previously had nowhere to show even
        // this much, so a failed fetch silently looked like "click a
        // template, nothing happens" with zero explanation.
        this.error = error instanceof Error && error.message ? error.message : 'Unable to load email templates. Please try again.'
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
