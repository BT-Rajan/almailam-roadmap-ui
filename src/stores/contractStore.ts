import { defineStore } from 'pinia'

import { contractService } from '@/services/contractService'
import type { ContractCreateInput } from '@/services/contractService'
import type { Contract, ContractAISummary } from '@/types/Contract'

interface ContractStoreState {
  projectId: string | undefined
  contracts: Contract[]
  selectedContractId: string | undefined
  aiSummary: ContractAISummary | undefined
  isLoading: boolean
  isAiSummaryLoading: boolean
  error: string | undefined
  aiSummaryError: string | undefined
}

export const useContractStore = defineStore('contract', {
  state: (): ContractStoreState => ({
    projectId: undefined,
    contracts: [],
    selectedContractId: undefined,
    aiSummary: undefined,
    isLoading: false,
    isAiSummaryLoading: false,
    error: undefined,
    aiSummaryError: undefined,
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
        if (defaultContractId) {
          await this.selectContract(defaultContractId)
        } else {
          this.selectedContractId = undefined
          this.aiSummary = undefined
        }
      } catch {
        this.error = 'Unable to load contracts. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    async selectContract(contractId: string) {
      this.selectedContractId = contractId
      this.aiSummary = undefined
      // AI summary is a supplementary enhancement, not core to viewing a
      // contract, so a failure here must never break contract loading or
      // selection -- it's caught and surfaced separately.
      this.aiSummaryError = undefined
      this.isAiSummaryLoading = true
      try {
        this.aiSummary = await contractService.getContractAISummary(contractId)
      } catch {
        this.aiSummaryError = 'AI summary is currently unavailable.'
      } finally {
        this.isAiSummaryLoading = false
      }
    },

    async createContract(input: ContractCreateInput): Promise<Contract> {
      const contract = await contractService.createContract(input)
      this.contracts = [...this.contracts, contract]
      await this.selectContract(contract.id)
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
  },
})
