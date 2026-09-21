import { defineStore } from 'pinia'

import { paymentService } from '@/services/paymentService'
import { ApiError } from '@/services/httpClient'
import { useClientStore } from '@/stores/clientStore'
import { useProjectStore } from '@/stores/projectStore'
import { useQuotationStore } from '@/stores/quotationStore'
import type { Client } from '@/types/Client'
import type {
  Adjustment,
  AdjustmentType,
  AgreementStream,
  CreateAgreementInput,
  FinancialAgreement,
  FinancialAuditEvent,
  FinancialSummary,
  Payment,
  PaymentObligation,
  Refund,
  UpdateAgreementInput,
} from '@/types/Payment'
import type { Project } from '@/types/Project'
import { triggerBlobDownload } from '@/utils/fileDownload'
import { CACHE_TTL_MS, getLoadGate } from '@/utils/loadGate'
import { replaceScope } from '@/utils/scopedCollection'
import { describeStoreError } from '@/utils/storeError'
import { getFinancialSummary } from '@/utils/paymentHelpers'

interface PaymentAgreementRow {
  agreement: FinancialAgreement
  project: Project | undefined
  client: Client | undefined
  summary: FinancialSummary
}

interface PaymentStoreState {
  agreements: FinancialAgreement[]
  obligations: PaymentObligation[]
  // True only once loadAll() has fetched EVERY agreement and obligation --
  // the two arrays may also hold just some projects' rows (see
  // loadForProject), so their length says nothing about completeness. See
  // needsFullLoad.
  isFullyLoaded: boolean
  isFullLoading: boolean
  // Per-agreement detail, loaded lazily when a workspace/detail view opens
  // rather than eagerly for every agreement up front.
  paymentsByAgreement: Record<string, Payment[]>
  auditEventsByAgreement: Record<string, FinancialAuditEvent[]>
  refundsByAgreement: Record<string, Refund[]>
  adjustmentsByAgreement: Record<string, Adjustment[]>
  isLoading: boolean
  isLoadingDetail: boolean
  isSubmitting: boolean
  error: string | undefined
  searchTerm: string
}

export const usePaymentStore = defineStore('payment', {
  state: (): PaymentStoreState => ({
    agreements: [],
    obligations: [],
    isFullyLoaded: false,
    isFullLoading: false,
    paymentsByAgreement: {},
    auditEventsByAgreement: {},
    refundsByAgreement: {},
    adjustmentsByAgreement: {},
    isLoading: false,
    isLoadingDetail: false,
    isSubmitting: false,
    error: undefined,
    searchTerm: '',
  }),

  getters: {
    // Whether a caller that needs every agreement should start a full load:
    // not already loaded, and not already being loaded.
    needsFullLoad(state): boolean {
      return !state.isFullyLoaded && !state.isFullLoading
    },

    // projectStore/clientStore are the single, canonical places these
    // full lists live -- delegating gives an O(1) Map lookup.
    getProjectById(): (projectId: string) => Project | undefined {
      return (projectId: string) => useProjectStore().getProjectById(projectId)
    },

    getClientById(): (clientId: string) => Client | undefined {
      return (clientId: string) => useClientStore().getClientById(clientId)
    },

    // stream is optional -- a project can have one agreement per stream,
    // so any caller that cares which one should pass it.
    getAgreementByProject(state) {
      return (projectId: string, stream?: AgreementStream): FinancialAgreement | undefined =>
        state.agreements.find((agreement) => agreement.projectId === projectId && (!stream || agreement.stream === stream))
    },

    obligationsForAgreement(state) {
      return (agreementId: string): PaymentObligation[] =>
        state.obligations.filter((obligation) => obligation.agreementId === agreementId).sort((a, b) => a.sequenceNumber - b.sequenceNumber)
    },

    summaryForAgreement() {
      return (agreementId: string): FinancialSummary | undefined => {
        const agreement = this.agreements.find((item: FinancialAgreement) => item.id === agreementId)
        if (!agreement) return undefined
        const summary = getFinancialSummary(agreement, this.obligationsForAgreement(agreementId))
        // Resolved from whichever project's quotations are already loaded
        // (the project workspace loads its own before this ever renders)
        // -- null rather than a fetch here, since this is a plain getter.
        // Matches against quotationNo (the real quotation_id FK,
        // resolved server-side), not the free-text quotationReference,
        // which can drift from the actual linked quotation.
        const quotationStore = useQuotationStore()
        const quotation = agreement.quotationNo
          ? quotationStore.quotations.find((item) => item.quotationNo === agreement.quotationNo)
          : undefined
        summary.estimateAmount = quotation?.amount ?? null
        return summary
      }
    },

    // Rows for the global Payments overview table — one per financial
    // agreement, with the project/client resolved and the summary
    // pre-calculated.
    agreementRows(state): PaymentAgreementRow[] {
      const rows: PaymentAgreementRow[] = []
      state.agreements.forEach((agreement) => {
        const project = this.getProjectById(agreement.projectId)
        const client = project ? this.getClientById(project.clientId) : undefined
        const summary = this.summaryForAgreement(agreement.id)
        if (summary) rows.push({ agreement, project, client, summary })
      })
      return rows
    },

    filteredAgreementRows(): PaymentAgreementRow[] {
      const term = this.searchTerm.trim().toLowerCase()
      if (term.length === 0) return this.agreementRows
      return this.agreementRows.filter(
        (row) =>
          row.project?.projectName.toLowerCase().includes(term) ||
          row.project?.projectNo.toLowerCase().includes(term) ||
          row.client?.companyName.toLowerCase().includes(term),
      )
    },

    portfolioSummary(): { contractAmount: number; totalReceived: number; totalPending: number; totalOverdue: number } {
      return this.agreementRows.reduce(
        (totals, row) => ({
          contractAmount: totals.contractAmount + row.summary.contractAmount,
          totalReceived: totals.totalReceived + row.summary.totalReceived,
          totalPending: totals.totalPending + row.summary.totalPending,
          totalOverdue: totals.totalOverdue + row.summary.totalOverdue,
        }),
        { contractAmount: 0, totalReceived: 0, totalPending: 0, totalOverdue: 0 },
      )
    },
  },

  actions: {
    // Shared by updateAgreement/approveAgreement/reopenAgreement below --
    // all patch the same agreement into the local cache after a mutating
    // call succeeds.
    patchAgreementInCache(agreementId: string, updated: FinancialAgreement): void {
      this.agreements = this.agreements.map((agreement) => (agreement.id === agreementId ? updated : agreement))
    },

    async loadAll() {
      this.isLoading = true
      this.isFullLoading = true
      this.error = undefined
      try {
        const projectStore = useProjectStore()
        const clientStore = useClientStore()
        const [agreements, obligations] = await Promise.all([
          paymentService.getFinancialAgreements(),
          paymentService.getAllObligations(),
          projectStore.projects.length === 0 ? projectStore.loadProjects() : Promise.resolve(),
          clientStore.clients.length === 0 ? clientStore.loadClients() : Promise.resolve(),
        ])
        this.agreements = agreements
        this.obligations = obligations
        this.isFullyLoaded = true
      } catch (error) {
        // A genuine 401 here means httpClient's own refresh-and-retry
        // already failed (session cookie expired/rotated) and it has
        // already logged authStore out -- staying on this page and
        // showing a generic retry-able message would just repeat the
        // same failed request forever with no token. Let the caller
        // (PaymentsPage) redirect to login instead, the same way
        // useIdleLogout treats a real auth failure as distinct from an
        // ordinary network/server error.
        if (error instanceof ApiError && error.status === 401) throw error
        this.error = describeStoreError('Unable to load payment information. Please try again.', error)
      } finally {
        this.isLoading = false
        this.isFullLoading = false
      }
    },

    // Loads just one project's agreements (up to one per billing stream) and
    // their obligations, merging them into the shared arrays in place of that
    // project's old rows -- for views scoped to one project, which shouldn't
    // download every agreement and obligation in the company. Does NOT mark
    // the store fully loaded. A no-op when everything is already here, unless
    // `force`. Unlike loadAll it doesn't load the project/client lists; the
    // callers (project workspace, contract/payment-plan pages) already do.
    async loadForProject(projectId: string, options: { force?: boolean } = {}) {
      if (this.isFullyLoaded && !options.force) return
      await getLoadGate(this, `project:${projectId}`, CACHE_TTL_MS).run(async (isCurrent) => {
        this.isLoading = true
        this.error = undefined
        try {
          const [agreements, obligations] = await Promise.all([
            paymentService.getFinancialAgreements(projectId),
            paymentService.getAllObligations(projectId),
          ])
          if (isCurrent()) {
            // Obligations reference their agreement, not the project, so the
            // rows to replace are those of any agreement this project had
            // before or has now.
            const agreementIds = new Set(
              this.agreements.filter((agreement) => agreement.projectId === projectId).map((agreement) => agreement.id),
            )
            agreements.forEach((agreement) => agreementIds.add(agreement.id))
            this.agreements = replaceScope(this.agreements, agreements, (agreement) => agreement.projectId === projectId)
            this.obligations = replaceScope(this.obligations, obligations, (obligation) =>
              agreementIds.has(obligation.agreementId),
            )
          }
          return true
        } catch (error) {
          if (isCurrent()) {
            // A genuine 401 means httpClient's own refresh-and-retry already
            // failed and logged the user out -- same handling as loadAll.
            if (error instanceof ApiError && error.status === 401) throw error
            this.error = describeStoreError('Unable to load payment information. Please try again.', error)
          }
          return false
        } finally {
          if (isCurrent()) this.isLoading = false
        }
      }, options)
    },

    async loadAgreementDetail(agreementId: string) {
      this.isLoadingDetail = true
      try {
        const [payments, auditEvents, refunds, adjustments] = await Promise.all([
          paymentService.getPayments(agreementId),
          paymentService.getAuditEvents(agreementId),
          paymentService.getRefunds(agreementId),
          paymentService.getAdjustments(agreementId),
        ])
        this.paymentsByAgreement[agreementId] = payments
        this.auditEventsByAgreement[agreementId] = auditEvents
        this.refundsByAgreement[agreementId] = refunds
        this.adjustmentsByAgreement[agreementId] = adjustments
      } finally {
        this.isLoadingDetail = false
      }
    },

    setSearchTerm(value: string) {
      this.searchTerm = value
    },

    async createAgreement(input: CreateAgreementInput, createdBy: string): Promise<FinancialAgreement> {
      this.isSubmitting = true
      try {
        const agreement = await paymentService.createAgreement(input, createdBy)
        const obligations = await paymentService.getObligations(agreement.id)
        this.agreements = [...this.agreements, agreement]
        this.obligations = [...this.obligations, ...obligations]
        await this.loadAgreementDetail(agreement.id)
        return agreement
      } finally {
        this.isSubmitting = false
      }
    },

    async updateAgreement(agreementId: string, input: UpdateAgreementInput): Promise<FinancialAgreement> {
      this.isSubmitting = true
      try {
        const updated = await paymentService.updateAgreement(agreementId, input)
        this.patchAgreementInCache(agreementId, updated)
        // The schedule was regenerated server-side -- refetch this
        // agreement's obligations rather than trying to patch the old
        // ones in place, since their count/ids may have changed entirely.
        const obligations = await paymentService.getObligations(agreementId)
        this.obligations = [...this.obligations.filter((o) => o.agreementId !== agreementId), ...obligations]
        await this.loadAgreementDetail(agreementId)
        return updated
      } finally {
        this.isSubmitting = false
      }
    },

    async deleteAgreement(agreementId: string): Promise<void> {
      this.isSubmitting = true
      try {
        await paymentService.deleteAgreement(agreementId)
        this.agreements = this.agreements.filter((agreement) => agreement.id !== agreementId)
        this.obligations = this.obligations.filter((obligation) => obligation.agreementId !== agreementId)
        delete this.paymentsByAgreement[agreementId]
        delete this.auditEventsByAgreement[agreementId]
        delete this.refundsByAgreement[agreementId]
        delete this.adjustmentsByAgreement[agreementId]
      } finally {
        this.isSubmitting = false
      }
    },

    async approveAgreement(agreementId: string): Promise<FinancialAgreement> {
      this.isSubmitting = true
      try {
        const updated = await paymentService.approveAgreement(agreementId)
        this.patchAgreementInCache(agreementId, updated)
        return updated
      } finally {
        this.isSubmitting = false
      }
    },

    async reopenAgreement(agreementId: string, reason: string): Promise<FinancialAgreement> {
      this.isSubmitting = true
      try {
        const updated = await paymentService.reopenAgreement(agreementId, reason)
        this.patchAgreementInCache(agreementId, updated)
        return updated
      } finally {
        this.isSubmitting = false
      }
    },

    async recordPayment(input: Parameters<typeof paymentService.recordPayment>[0], createdBy: string): Promise<Payment> {
      this.isSubmitting = true
      try {
        const payment = await paymentService.recordPayment(input, createdBy)
        this.obligations = await paymentService.getAllObligations()
        await this.loadAgreementDetail(input.agreementId)
        return payment
      } finally {
        this.isSubmitting = false
      }
    },

    async attachPaymentProof(paymentId: string, file: File, agreementId: string): Promise<void> {
      this.isSubmitting = true
      try {
        await paymentService.attachPaymentProof(paymentId, file)
        await this.loadAgreementDetail(agreementId)
      } finally {
        this.isSubmitting = false
      }
    },

    async downloadPaymentProof(paymentId: string, filename: string): Promise<void> {
      const blob = await paymentService.downloadPaymentProof(paymentId)
      triggerBlobDownload(blob, filename)
    },

    async recordRefund(input: Parameters<typeof paymentService.createRefund>[0]) {
      this.isSubmitting = true
      try {
        await paymentService.createRefund(input)
        this.obligations = await paymentService.getAllObligations()
        await this.loadAgreementDetail(input.agreementId)
      } finally {
        this.isSubmitting = false
      }
    },

    async recordAdjustment(input: { agreementId: string; obligationId: string; type: AdjustmentType; amount: number; reason: string; authorisingUser: string }) {
      this.isSubmitting = true
      try {
        await paymentService.createAdjustment(input)
        this.obligations = await paymentService.getAllObligations()
        await this.loadAgreementDetail(input.agreementId)
      } finally {
        this.isSubmitting = false
      }
    },

    async cancelObligation(obligationId: string, agreementId: string, reason: string, user: string) {
      this.isSubmitting = true
      try {
        await paymentService.cancelObligation(obligationId, reason, user)
        this.obligations = await paymentService.getAllObligations()
        await this.loadAgreementDetail(agreementId)
      } finally {
        this.isSubmitting = false
      }
    },

    async waiveObligation(obligationId: string, agreementId: string, reason: string, user: string) {
      this.isSubmitting = true
      try {
        await paymentService.waiveObligation(obligationId, reason, user)
        this.obligations = await paymentService.getAllObligations()
        await this.loadAgreementDetail(agreementId)
      } finally {
        this.isSubmitting = false
      }
    },
  },
})
