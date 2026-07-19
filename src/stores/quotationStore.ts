import { defineStore } from 'pinia'

import { quotationService } from '@/services/quotationService'
import type { Quotation } from '@/types/Quotation'

interface QuotationStoreState {
  projectId: string | undefined
  quotations: Quotation[]
  selectedQuotationId: string | undefined
  isLoading: boolean
  error: string | undefined
}

export const useQuotationStore = defineStore('quotation', {
  state: (): QuotationStoreState => ({
    projectId: undefined,
    quotations: [],
    selectedQuotationId: undefined,
    isLoading: false,
    error: undefined,
  }),

  getters: {
    selectedQuotation(state): Quotation | undefined {
      return state.quotations.find((quotation) => quotation.id === state.selectedQuotationId)
    },

    latestQuotation(state): Quotation | undefined {
      return [...state.quotations].sort((a, b) => b.issueDate.localeCompare(a.issueDate))[0]
    },
  },

  actions: {
    async loadQuotationsForProject(projectId: string) {
      this.isLoading = true
      this.error = undefined
      try {
        this.projectId = projectId
        this.quotations = await quotationService.getQuotationsByProject(projectId)
        this.selectedQuotationId = this.latestQuotation?.id
      } catch {
        this.error = 'Unable to load quotations. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    selectQuotation(quotationId: string) {
      this.selectedQuotationId = quotationId
    },
  },
})
