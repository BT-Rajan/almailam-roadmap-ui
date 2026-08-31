import { defineStore } from 'pinia'

import { documentTemplateService } from '@/services/documentTemplateService'
import type { DocumentTemplate, DocumentTemplateType } from '@/types/DocumentTemplate'
import { triggerBlobDownload } from '@/utils/fileDownload'

interface DocumentTemplateStoreState {
  templates: DocumentTemplate[]
  isLoading: boolean
  error: string | undefined
}

export const useDocumentTemplateStore = defineStore('documentTemplate', {
  state: (): DocumentTemplateStoreState => ({
    templates: [],
    isLoading: false,
    error: undefined,
  }),

  getters: {
    byType(state) {
      return (documentType: DocumentTemplateType): DocumentTemplate[] =>
        state.templates.filter((template) => template.documentType === documentType)
    },
  },

  actions: {
    async loadTemplates() {
      this.isLoading = true
      this.error = undefined
      try {
        this.templates = await documentTemplateService.getTemplates()
      } catch {
        this.error = 'Unable to load document templates. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    async uploadTemplate(documentType: DocumentTemplateType, file: File): Promise<DocumentTemplate> {
      const created = await documentTemplateService.uploadTemplate(documentType, file)
      // A new default for this type demotes the sibling that used to be
      // default (see backend document_template_service.upload_template),
      // so refresh the whole list rather than just prepending.
      await this.loadTemplates()
      return created
    },

    async setDefaultTemplate(templateId: string): Promise<void> {
      await documentTemplateService.setDefaultTemplate(templateId)
      await this.loadTemplates()
    },

    async deleteTemplate(templateId: string): Promise<void> {
      await documentTemplateService.deleteTemplate(templateId)
      this.templates = this.templates.filter((template) => template.id !== templateId)
    },

    async downloadTemplate(template: DocumentTemplate): Promise<void> {
      const blob = await documentTemplateService.downloadTemplate(template.id)
      triggerBlobDownload(blob, template.originalFilename)
    },
  },
})
