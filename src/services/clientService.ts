import { apiClient } from '@/services/httpClient'
import type {
  Client,
  ClientAddress,
  ClientAuditEvent,
  ClientConsent,
  ClientContact,
  ClientDocument,
  ClientDuplicateMatch,
  ClientIdentification,
  ClientVerification,
} from '@/types/Client'

/**
 * Fetch all clients from backend API
 */
async function getClients(): Promise<Client[]> {
  try {
    return await apiClient.get<Client[]>('/api/clients')
  } catch (error) {
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch clients')
  }
}

/**
 * Fetch a specific client by ID from backend API
 */
async function getClientById(clientId: string): Promise<Client | undefined> {
  try {
    return await apiClient.get<Client>(`/api/clients/${clientId}`)
  } catch (error) {
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch client')
  }
}

/**
 * Fetch contacts for a specific client from backend API
 */
async function getContactsForClient(clientId: string): Promise<ClientContact[]> {
  try {
    return await apiClient.get<ClientContact[]>(`/api/clients/${clientId}/contacts`)
  } catch (error) {
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch contacts')
  }
}

/**
 * Fetch addresses for a specific client from backend API
 */
async function getAddressesForClient(clientId: string): Promise<ClientAddress[]> {
  try {
    return await apiClient.get<ClientAddress[]>(`/api/clients/${clientId}/addresses`)
  } catch (error) {
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch addresses')
  }
}

/**
 * Fetch identifications for a specific client from backend API
 */
async function getIdentificationsForClient(clientId: string): Promise<ClientIdentification[]> {
  try {
    return await apiClient.get<ClientIdentification[]>(`/api/clients/${clientId}/identifications`)
  } catch (error) {
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch identifications')
  }
}

/**
 * Fetch documents for a specific client from backend API
 */
async function getDocumentsForClient(clientId: string): Promise<ClientDocument[]> {
  try {
    return await apiClient.get<ClientDocument[]>(`/api/clients/${clientId}/documents`)
  } catch (error) {
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch documents')
  }
}

/**
 * Fetch verifications for a specific client from backend API
 */
async function getVerificationsForClient(clientId: string): Promise<ClientVerification[]> {
  try {
    return await apiClient.get<ClientVerification[]>(`/api/clients/${clientId}/verifications`)
  } catch (error) {
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch verifications')
  }
}

/**
 * Fetch consents for a specific client from backend API
 */
async function getConsentsForClient(clientId: string): Promise<ClientConsent[]> {
  try {
    return await apiClient.get<ClientConsent[]>(`/api/clients/${clientId}/consents`)
  } catch (error) {
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch consents')
  }
}

/**
 * Fetch audit events for a specific client from backend API
 */
async function getAuditEventsForClient(clientId: string): Promise<ClientAuditEvent[]> {
  try {
    return await apiClient.get<ClientAuditEvent[]>(`/api/clients/${clientId}/audit-events`)
  } catch (error) {
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch audit events')
  }
}

/**
 * Find possible duplicate clients based on name, mobile, and email
 * Calls backend API to check for duplicates before creating new client
 */
async function findPossibleDuplicates(
  name: string,
  mobile: string,
  email: string
): Promise<ClientDuplicateMatch[]> {
  try {
    return await apiClient.post<ClientDuplicateMatch[]>('/api/clients/check-duplicates', {
      name,
      mobile,
      email,
    })
  } catch (error) {
    throw new Error(error instanceof Error ? error.message : 'Failed to check for duplicates')
  }
}

/**
 * Create a new client via backend API
 */
async function createClient(clientData: Partial<Client>): Promise<Client> {
  try {
    return await apiClient.post<Client>('/api/clients', clientData)
  } catch (error) {
    throw new Error(error instanceof Error ? error.message : 'Failed to create client')
  }
}

/**
 * Update an existing client via backend API
 */
async function updateClient(clientId: string, clientData: Partial<Client>): Promise<Client> {
  try {
    return await apiClient.patch<Client>(`/api/clients/${clientId}`, clientData)
  } catch (error) {
    throw new Error(error instanceof Error ? error.message : 'Failed to update client')
  }
}

/**
 * Delete a client via backend API
 */
async function deleteClient(clientId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/clients/${clientId}`)
  } catch (error) {
    throw new Error(error instanceof Error ? error.message : 'Failed to delete client')
  }
}

export const clientService = {
  getClients,
  getClientById,
  getContactsForClient,
  getAddressesForClient,
  getIdentificationsForClient,
  getDocumentsForClient,
  getVerificationsForClient,
  getConsentsForClient,
  getAuditEventsForClient,
  findPossibleDuplicates,
  createClient,
  updateClient,
  deleteClient,
}
