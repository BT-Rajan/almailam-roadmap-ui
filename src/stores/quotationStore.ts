import { defineStore } from 'pinia'

import { quotationService } from '@/services/quotationService'
import type { QuotationCreateInput } from '@/services/quotationService'
import type { Quotation, QuotationAuditEvent } from '@/types/Quotation'

interface QuotationStoreState {
  projectId: string | undefined
  quotations: Quotation[]
  selectedQuotationId: string | undefined
  isLoading: boolean
  error: string | undefined
  // Set by "Advance to Contract" on the Payment Plan tab, consumed by
  // the contract tab (which opens its New Contract dialog prefilled from
  // this quotation, then clears it) -- the two tabs otherwise have no
  // direct way to talk to each other.
  pendingContractQuotationId: string | undefined
  // Keyed by quotation id, populated lazily (selection + any action
  // that logs a new history entry) rather than eagerly for every
  // quotation up front -- see loadAuditEvents.
  auditEventsByQuotation: Record<string, QuotationAuditEvent[]>
}

export const useQuotationStore = defineStore('quotation', {
  state: (): QuotationStoreState => ({
    projectId: undefined,
    quotations: [],
    selectedQuotationId: undefined,
    isLoading: false,
    error: undefined,
    pendingContractQuotationId: undefined,
    auditEventsByQuotation: {},
  }),

  getters: {
    selectedQuotation(state): Quotation | undefined {
      return state.quotations.find((quotation) => quotation.id === state.selectedQuotationId)
    },

    latestQuotation(state): Quotation | undefined {
      return [...state.quotations].sort((a, b) => b.issueDate.localeCompare(a.issueDate))[0]
    },

    selectedQuotationAuditEvents(state): QuotationAuditEvent[] {
      return state.selectedQuotationId ? (state.auditEventsByQuotation[state.selectedQuotationId] ?? []) : []
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
        if (this.selectedQuotationId) await this.loadAuditEvents(this.selectedQuotationId)
      } catch {
        this.error = 'Unable to load quotations. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    // Non-critical: the quotation itself already loaded fine, so a
    // failure here shouldn't surface as an error state or block
    // anything -- the history panel just falls back to showing content
    // revisions only until this succeeds (e.g. on the next selection).
    async loadAuditEvents(quotationId: string) {
      try {
        this.auditEventsByQuotation[quotationId] = await quotationService.getAuditEvents(quotationId)
      } catch {
        // Swallowed deliberately -- see comment above.
      }
    },

    selectQuotation(quotationId: string) {
      this.selectedQuotationId = quotationId
      if (!this.auditEventsByQuotation[quotationId]) void this.loadAuditEvents(quotationId)
    },

    // "Advance to Contract" only ever fires from a quotation that's
    // already Approved + Final (see PaymentPlanPanel's approvedQuotation),
    // so no re-check is needed here -- this just hands the intent off.
    requestAdvanceToContract(quotationId: string) {
      this.selectedQuotationId = quotationId
      this.pendingContractQuotationId = quotationId
    },

    consumePendingContractRequest(): string | undefined {
      const id = this.pendingContractQuotationId
      this.pendingContractQuotationId = undefined
      return id
    },

    async createQuotation(input: QuotationCreateInput): Promise<Quotation> {
      const quotation = await quotationService.createQuotation(input)
      this.quotations = [...this.quotations, quotation]
      this.selectedQuotationId = quotation.id
      await this.loadAuditEvents(quotation.id)
      return quotation
    },

    async updateQuotation(quotationId: string, patch: Partial<Quotation>): Promise<Quotation> {
      const updated = await quotationService.updateQuotation(quotationId, patch)
      this.quotations = this.quotations.map((q) => (q.id === quotationId ? updated : q))
      return updated
    },

    async finalizeQuotation(quotationId: string): Promise<Quotation> {
      const updated = await quotationService.finalizeQuotation(quotationId)
      this.quotations = this.quotations.map((q) => (q.id === quotationId ? updated : q))
      return updated
    },

    async reopenQuotation(quotationId: string): Promise<Quotation> {
      const updated = await quotationService.reopenQuotation(quotationId)
      this.quotations = this.quotations.map((q) => (q.id === quotationId ? updated : q))
      return updated
    },

    async setQuotationStatus(quotationId: string, status: string, reason?: string): Promise<Quotation> {
      const updated = await quotationService.setQuotationStatus(quotationId, status, reason)
      this.quotations = this.quotations.map((q) => (q.id === quotationId ? updated : q))
      await this.loadAuditEvents(quotationId)
      return updated
    },

    async confirmQuotationApproval(quotationId: string, file: File): Promise<Quotation> {
      const updated = await quotationService.confirmQuotationApproval(quotationId, file)
      this.quotations = this.quotations.map((q) => (q.id === quotationId ? updated : q))
      await this.loadAuditEvents(quotationId)
      return updated
    },
  },
})
