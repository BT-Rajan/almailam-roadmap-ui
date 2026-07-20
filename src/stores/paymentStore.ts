import { defineStore } from 'pinia'

import { clientService } from '@/services/clientService'
import { paymentService } from '@/services/paymentService'
import { projectService } from '@/services/projectService'
import type { Client } from '@/types/Client'
import type {
  Adjustment,
  AdjustmentType,
  CreateAgreementInput,
  FinancialAgreement,
  FinancialAuditEvent,
  FinancialSummary,
  Payment,
  PaymentObligation,
  Refund,
} from '@/types/Payment'
import type { Project } from '@/types/Project'
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
  projects: Project[]
  clients: Client[]
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
    projects: [],
    clients: [],
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
    getProjectById(state) {
      return (projectId: string): Project | undefined => state.projects.find((project) => project.id === projectId)
    },

    getClientById(state) {
      return (clientId: string): Client | undefined => state.clients.find((client) => client.id === clientId)
    },

    getAgreementByProject(state) {
      return (projectId: string): FinancialAgreement | undefined => state.agreements.find((agreement) => agreement.projectId === projectId)
    },

    obligationsForAgreement(state) {
      return (agreementId: string): PaymentObligation[] =>
        state.obligations.filter((obligation) => obligation.agreementId === agreementId).sort((a, b) => a.sequenceNumber - b.sequenceNumber)
    },

    summaryForAgreement() {
      return (agreementId: string): FinancialSummary | undefined => {
        const agreement = this.agreements.find((item: FinancialAgreement) => item.id === agreementId)
        if (!agreement) return undefined
        return getFinancialSummary(agreement, this.obligationsForAgreement(agreementId))
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
    async loadAll() {
      this.isLoading = true
      this.error = undefined
      try {
        const [agreements, obligations, projects, clients] = await Promise.all([
          paymentService.getFinancialAgreements(),
          paymentService.getAllObligations(),
          projectService.getProjects(),
          clientService.getClients(),
        ])
        this.agreements = agreements
        this.obligations = obligations
        this.projects = projects
        this.clients = clients
      } catch {
        this.error = 'Unable to load payment information. Please try again.'
      } finally {
        this.isLoading = false
      }
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

    async recordPayment(input: Parameters<typeof paymentService.recordPayment>[0], createdBy: string) {
      this.isSubmitting = true
      try {
        await paymentService.recordPayment(input, createdBy)
        this.obligations = await paymentService.getAllObligations()
        await this.loadAgreementDetail(input.agreementId)
      } finally {
        this.isSubmitting = false
      }
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
