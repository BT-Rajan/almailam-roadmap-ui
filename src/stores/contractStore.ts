import { defineStore } from 'pinia'

import { contractService } from '@/services/contractService'
import type { Contract, ContractAISummary } from '@/types/Contract'

interface ContractStoreState {
  projectId: string | undefined
  contracts: Contract[]
  selectedContractId: string | undefined
  aiSummary: ContractAISummary | undefined
  isLoading: boolean
  isAiSummaryLoading: boolean
  error: string | undefined
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
      this.isAiSummaryLoading = true
      try {
        this.aiSummary = await contractService.getContractAISummary(contractId)
      } finally {
        this.isAiSummaryLoading = false
      }
    },
  },
})
