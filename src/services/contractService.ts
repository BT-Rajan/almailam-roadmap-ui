import { CONTRACT_AI_SUMMARIES } from '@/mock/contractAiSummaries'
import { CONTRACTS } from '@/mock/contracts'
import type { Contract, ContractAISummary } from '@/types/Contract'
import { simulateNetworkDelay } from '@/utils/mockDelay'

const AI_THINKING_DELAY_MS = 900

async function getContractsByProject(projectId: string): Promise<Contract[]> {
  await simulateNetworkDelay()
  return CONTRACTS.filter((contract) => contract.projectId === projectId)
}

async function getContractById(contractId: string): Promise<Contract | undefined> {
  await simulateNetworkDelay()
  return CONTRACTS.find((contract) => contract.id === contractId)
}

async function getContractAISummary(contractId: string): Promise<ContractAISummary | undefined> {
  await simulateNetworkDelay(AI_THINKING_DELAY_MS)
  return CONTRACT_AI_SUMMARIES.find((summary) => summary.contractId === contractId)
}

export const contractService = {
  getContractsByProject,
  getContractById,
  getContractAISummary,
}
