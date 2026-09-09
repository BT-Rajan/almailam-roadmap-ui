import { defineStore } from 'pinia'

import { contractService } from '@/services/contractService'
import type { ContractCreateInput } from '@/services/contractService'
import type { Contract, ContractAuditEvent } from '@/types/Contract'

interface ContractStoreState {
  projectId: string | undefined
  contracts: Contract[]
  selectedContractId: string | undefined
  isLoading: boolean
  error: string | undefined
  // Keyed by contract id -- document activity (downloads/prints/
  // emails) and status changes, shown in ContractRevisionHistory
  // alongside content revisions.
  auditEventsByContract: Record<string, ContractAuditEvent[]>
}

export const useContractStore = defineStore('contract', {
  state: (): ContractStoreState => ({
    projectId: undefined,
    contracts: [],
    selectedContractId: undefined,
    isLoading: false,
    error: undefined,
    auditEventsByContract: {},
  }),

  getters: {
    selectedContract(state): Contract | undefined {
      return state.contracts.find((contract) => contract.id === state.selectedContractId)
    },

    latestContract(state): Contract | undefined {
      return [...state.contracts].sort((a, b) => b.issueDate.localeCompare(a.issueDate))[0]
    },
  },

  actions: {
    async loadContractsForProject(projectId: string) {
      this.isLoading = true
      this.error = undefined
      try {
        this.projectId = projectId
        this.contracts = await contractService.getContractsByProject(projectId)
        const defaultContractId = this.latestContract?.id
        this.selectedContractId = defaultContractId ?? undefined
      } catch {
        this.error = 'Unable to load contracts. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    selectContract(contractId: string) {
      this.selectedContractId = contractId
    },

    async createContract(input: ContractCreateInput): Promise<Contract> {
      const contract = await contractService.createContract(input)
      this.contracts = [...this.contracts, contract]
      this.selectContract(contract.id)
      return contract
    },

    async updateContract(contractId: string, patch: Partial<Contract>): Promise<Contract> {
      const updated = await contractService.updateContract(contractId, patch)
      this.contracts = this.contracts.map((c) => (c.id === contractId ? updated : c))
      return updated
    },

    async finalizeContract(contractId: string): Promise<Contract> {
      const updated = await contractService.finalizeContract(contractId)
      this.contracts = this.contracts.map((c) => (c.id === contractId ? updated : c))
      return updated
    },

    async reopenContract(contractId: string): Promise<Contract> {
      const updated = await contractService.reopenContract(contractId)
      this.contracts = this.contracts.map((c) => (c.id === contractId ? updated : c))
      return updated
    },

    async setContractStatus(contractId: string, status: string, reason?: string): Promise<Contract> {
      const updated = await contractService.setContractStatus(contractId, status, reason)
      this.contracts = this.contracts.map((c) => (c.id === contractId ? updated : c))
      return updated
    },

    async confirmContractSigning(contractId: string, file: File): Promise<Contract> {
      const updated = await contractService.confirmContractSigning(contractId, file)
      this.contracts = this.contracts.map((c) => (c.id === contractId ? updated : c))
      return updated
    },

    async loadAuditEvents(contractId: string): Promise<void> {
      const events = await contractService.getAuditEvents(contractId)
      this.auditEventsByContract = { ...this.auditEventsByContract, [contractId]: events }
    },
  },
})
