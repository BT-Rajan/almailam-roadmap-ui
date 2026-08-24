import { apiClient } from '@/services/httpClient'
import type { Contract, ContractAISummary } from '@/types/Contract'

/**
 * Fetch contracts for a specific project from backend API
 */
async function getContractsByProject(projectId: string): Promise<Contract[]> {
  try {
    return await apiClient.get<Contract[]>(`/api/contracts?projectId=${projectId}`)
  } catch (error) {
    console.error(`Failed to fetch contracts for project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch contracts')
  }
}

/**
 * Fetch a specific contract by ID from backend API
 */
async function getContractById(contractId: string): Promise<Contract | undefined> {
  try {
    return await apiClient.get<Contract>(`/api/contracts/${contractId}`)
  } catch (error) {
    console.error(`Failed to fetch contract ${contractId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch contract')
  }
}

/**
 * Get AI summary for a contract from backend API
 */
async function getContractAISummary(contractId: string): Promise<ContractAISummary | undefined> {
  try {
    return await apiClient.get<ContractAISummary>(`/api/contracts/${contractId}/ai-summary`)
  } catch (error) {
    console.error(`Failed to fetch AI summary for contract ${contractId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch AI summary')
  }
}

/**
 * Fetch all contracts from backend API
 */
async function getContracts(): Promise<Contract[]> {
  try {
    return await apiClient.get<Contract[]>('/api/contracts')
  } catch (error) {
    console.error('Failed to fetch contracts:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch contracts')
  }
}

export interface ContractClauseInput {
  title: string
  content: string
}

export interface ContractCreateInput {
  projectId: string
  // The Approved, finalized quotation this contract is generated from --
  // required by the backend (see contract_service.create_contract).
  quotationId: string
  templateName: string
  currency: string
  contractValue: number
  expiryDate: string
  clientRepresentative: string
  scopeSummary: string
  clauses: ContractClauseInput[]
  templateKey?: string
  isBilingual?: boolean
  subjectLineAr?: string
  subjectLineEn?: string
  projectReference?: string
  feeFrequency?: string
  scopeItemsAr?: string[]
  scopeItemsEn?: string[]
  paymentTermsAr?: string[]
  paymentTermsEn?: string[]
}

/**
 * Create a new contract via backend API
 */
async function createContract(contractData: ContractCreateInput): Promise<Contract> {
  try {
    return await apiClient.post<Contract>('/api/contracts', contractData)
  } catch (error) {
    console.error('Failed to create contract:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to create contract')
  }
}

/**
 * Update a contract via backend API
 */
async function updateContract(contractId: string, contractData: Partial<Contract>): Promise<Contract> {
  try {
    return await apiClient.patch<Contract>(`/api/contracts/${contractId}`, contractData)
  } catch (error) {
    console.error(`Failed to update contract ${contractId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update contract')
  }
}

/**
 * Move a contract to a new status (Sent/Signed/Active/Expired/
 * Terminated/back to Draft) -- a separate call from updateContract
 * since `reason` is write-only and isn't part of the Contract read
 * model.
 */
async function setContractStatus(contractId: string, status: string, reason?: string): Promise<Contract> {
  try {
    return await apiClient.patch<Contract>(`/api/contracts/${contractId}`, { status, reason })
  } catch (error) {
    console.error(`Failed to change status for contract ${contractId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to change contract status')
  }
}

/**
 * Delete a contract via backend API
 */
async function deleteContract(contractId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/contracts/${contractId}`)
  } catch (error) {
    console.error(`Failed to delete contract ${contractId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to delete contract')
  }
}

/**
 * Lock a lettered contract's content and mark it ready to print.
 */
async function finalizeContract(contractId: string): Promise<Contract> {
  try {
    return await apiClient.post<Contract>(`/api/contracts/${contractId}/finalize`, {})
  } catch (error) {
    console.error(`Failed to finalize contract ${contractId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to finalize contract')
  }
}

/**
 * Unlock a finalized contract letter for further editing.
 */
async function reopenContract(contractId: string): Promise<Contract> {
  try {
    return await apiClient.post<Contract>(`/api/contracts/${contractId}/reopen`, {})
  } catch (error) {
    console.error(`Failed to reopen contract ${contractId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to reopen contract')
  }
}

export const contractService = {
  getContractsByProject,
  getContractById,
  getContractAISummary,
  getContracts,
  createContract,
  updateContract,
  setContractStatus,
  deleteContract,
  finalizeContract,
  reopenContract,
}
