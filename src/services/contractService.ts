import { apiClient } from '@/services/httpClient'
import type { Contract, ContractAISummary } from '@/types/Contract'

/**
 * Fetch contracts for a specific project from backend API
 */
async function getContractsByProject(projectId: string): Promise<Contract[]> {
  try {
    return await apiClient.get<Contract[]>(`/api/projects/${projectId}/contracts`)
  } catch (error) {
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
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch contracts')
  }
}

/**
 * Create a new contract via backend API
 */
async function createContract(contractData: Partial<Contract>): Promise<Contract> {
  try {
    return await apiClient.post<Contract>('/api/contracts', contractData)
  } catch (error) {
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
    throw new Error(error instanceof Error ? error.message : 'Failed to update contract')
  }
}

/**
 * Delete a contract via backend API
 */
async function deleteContract(contractId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/contracts/${contractId}`)
  } catch (error) {
    throw new Error(error instanceof Error ? error.message : 'Failed to delete contract')
  }
}

export const contractService = {
  getContractsByProject,
  getContractById,
  getContractAISummary,
  getContracts,
  createContract,
  updateContract,
  deleteContract,
}
