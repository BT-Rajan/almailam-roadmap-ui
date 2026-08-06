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
import type { PagedResponse, PageParams } from '@/types/Pagination'
import { fetchAllPages } from '@/utils/fetchAllPages'

function buildQuery(params: Record<string, string | number | undefined>): string {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') query.set(key, String(value))
  }
  const queryString = query.toString()
  return queryString ? `?${queryString}` : ''
}

/**
 * Fetch a single page of clients from the backend API. Prefer this over
 * getClients() for any UI that displays/paginates the list directly, since
 * it only asks the server for one page at a time instead of the whole table.
 */
async function getClientsPage(
  params: PageParams & { clientType?: string; status?: string; onboardingState?: string } = {},
): Promise<PagedResponse<Client>> {
  try {
    const query = buildQuery({
      search: params.search,
      clientType: params.clientType,
      status: params.status,
      onboardingState: params.onboardingState,
      sort: params.sort,
      page: params.page,
      pageSize: params.pageSize,
    })
    return await apiClient.get<PagedResponse<Client>>(`/api/clients${query}`)
  } catch (error) {
    console.error('Failed to fetch clients:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch clients')
  }
}

/**
 * Fetch every client from the backend API as a flat array. Internally
 * walks the paginated endpoint page by page (each request is still bounded
 * server-side) so existing callers that need the full list -- e.g. cross-
 * reference lookups like resolving a project's client name elsewhere in the
 * app -- don't have to change.
 */
async function getClients(): Promise<Client[]> {
  return fetchAllPages<Client>((page, pageSize) => getClientsPage({ page, pageSize }))
}

/**
 * Fetch a specific client by ID from backend API
 */
async function getClientById(clientId: string): Promise<Client | undefined> {
  try {
    return await apiClient.get<Client>(`/api/clients/${clientId}`)
  } catch (error) {
    console.error(`Failed to fetch client ${clientId}:`, error)
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
    console.error(`Failed to fetch contacts for client ${clientId}:`, error)
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
    console.error(`Failed to fetch addresses for client ${clientId}:`, error)
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
    console.error(`Failed to fetch identifications for client ${clientId}:`, error)
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
    console.error(`Failed to fetch documents for client ${clientId}:`, error)
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
    console.error(`Failed to fetch verifications for client ${clientId}:`, error)
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
    console.error(`Failed to fetch consents for client ${clientId}:`, error)
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
    console.error(`Failed to fetch audit events for client ${clientId}:`, error)
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
    const query = new URLSearchParams({ name, mobile, email }).toString()
    return await apiClient.post<ClientDuplicateMatch[]>(`/api/clients/duplicates?${query}`)
  } catch (error) {
    console.error('Failed to check for duplicate clients:', error)
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
    console.error('Failed to create client:', error)
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
    console.error(`Failed to update client ${clientId}:`, error)
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
    console.error(`Failed to delete client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to delete client')
  }
}

export const clientService = {
  getClients,
  getClientsPage,
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
