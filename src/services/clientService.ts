import { apiClient } from '@/services/httpClient'
import { useAuthStore } from '@/stores/authStore'
import type {
  Client,
  ClientAddress,
  ClientCommunicationPreference,
  ClientContact,
  ClientDocument,
  ClientDuplicateMatch,
  ClientIdentification,
  ClientIndividualProfile,
  ClientOrganisationProfile,
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
  params: PageParams & {
    clientType?: string
    status?: string
    onboardingState?: string
    accountManagerId?: string
    /** true to browse soft-deleted clients instead of active ones -- see restoreClient. */
    deleted?: boolean
  } = {},
): Promise<PagedResponse<Client>> {
  try {
    const query = buildQuery({
      search: params.search,
      clientType: params.clientType,
      status: params.status,
      onboardingState: params.onboardingState,
      accountManagerId: params.accountManagerId,
      sort: params.sort,
      page: params.page,
      pageSize: params.pageSize,
      deleted: params.deleted ? 'true' : undefined,
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

export type ClientContactInput = Omit<ClientContact, 'id' | 'clientId'>

/**
 * Record a new client contact via backend API
 */
async function createContact(clientId: string, input: ClientContactInput): Promise<ClientContact> {
  try {
    return await apiClient.post<ClientContact>(`/api/clients/${clientId}/contacts`, input)
  } catch (error) {
    console.error(`Failed to record contact for client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to record contact')
  }
}

export type ClientContactUpdateInput = Partial<ClientContactInput>

/**
 * Update an existing client contact via backend API
 */
async function updateContact(clientId: string, contactId: string, input: ClientContactUpdateInput): Promise<ClientContact> {
  try {
    return await apiClient.patch<ClientContact>(`/api/clients/${clientId}/contacts/${contactId}`, input)
  } catch (error) {
    console.error(`Failed to update contact ${contactId} for client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update contact')
  }
}

/**
 * Remove a client contact via backend API (soft delete)
 */
async function deleteContact(clientId: string, contactId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/clients/${clientId}/contacts/${contactId}`)
  } catch (error) {
    console.error(`Failed to delete contact ${contactId} for client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to delete contact')
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

export type ClientAddressInput = Omit<ClientAddress, 'id' | 'clientId'>

/**
 * Record a new client address via backend API
 */
async function createAddress(clientId: string, input: ClientAddressInput): Promise<ClientAddress> {
  try {
    return await apiClient.post<ClientAddress>(`/api/clients/${clientId}/addresses`, input)
  } catch (error) {
    console.error(`Failed to record address for client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to record address')
  }
}

export type ClientAddressUpdateInput = Partial<ClientAddressInput>

/**
 * Update an existing client address via backend API
 */
async function updateAddress(clientId: string, addressId: string, input: ClientAddressUpdateInput): Promise<ClientAddress> {
  try {
    return await apiClient.patch<ClientAddress>(`/api/clients/${clientId}/addresses/${addressId}`, input)
  } catch (error) {
    console.error(`Failed to update address ${addressId} for client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update address')
  }
}

/**
 * Remove a client address via backend API (soft delete)
 */
async function deleteAddress(clientId: string, addressId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/clients/${clientId}/addresses/${addressId}`)
  } catch (error) {
    console.error(`Failed to delete address ${addressId} for client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to delete address')
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

export type ClientIdentificationInput = Omit<ClientIdentification, 'id' | 'clientId'>

/**
 * Record a new client identification document via backend API
 */
async function createIdentification(
  clientId: string,
  input: ClientIdentificationInput,
): Promise<ClientIdentification> {
  try {
    return await apiClient.post<ClientIdentification>(`/api/clients/${clientId}/identifications`, input)
  } catch (error) {
    console.error(`Failed to record identification for client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to record identification')
  }
}

export type ClientIdentificationUpdateInput = Partial<ClientIdentificationInput>

/**
 * Update an existing client identification via backend API
 */
async function updateIdentification(
  clientId: string,
  identificationId: string,
  input: ClientIdentificationUpdateInput,
): Promise<ClientIdentification> {
  try {
    return await apiClient.patch<ClientIdentification>(`/api/clients/${clientId}/identifications/${identificationId}`, input)
  } catch (error) {
    console.error(`Failed to update identification ${identificationId} for client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update identification')
  }
}

/**
 * Remove a client identification via backend API (soft delete)
 */
async function deleteIdentification(clientId: string, identificationId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/clients/${clientId}/identifications/${identificationId}`)
  } catch (error) {
    console.error(`Failed to delete identification ${identificationId} for client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to delete identification')
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
 * Download a client document's stored file from backend API.
 */
async function downloadDocument(clientId: string, documentId: string): Promise<Blob> {
  const authStore = useAuthStore()
  try {
    const response = await fetch(`/api/clients/${clientId}/documents/${documentId}/download`, {
      method: 'GET',
      headers: authStore.accessToken ? { Authorization: `Bearer ${authStore.accessToken}` } : undefined,
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error(`Download failed with status ${response.status}`)
    }

    return await response.blob()
  } catch (error) {
    console.error(`Failed to download document ${documentId} for client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to download document')
  }
}

/**
 * Find possible duplicate clients based on name, mobile, and email
 * Calls backend API to check for duplicates before creating new client
 */
async function findPossibleDuplicates(
  name: string,
  mobile: string,
  email: string,
  registrationNumber?: string,
): Promise<ClientDuplicateMatch[]> {
  try {
    return await apiClient.post<ClientDuplicateMatch[]>('/api/clients/duplicates', {
      name,
      mobile,
      email,
      registrationNumber: registrationNumber ?? '',
    })
  } catch (error) {
    console.error('Failed to check for duplicate clients:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to check for duplicates')
  }
}

/**
 * Finds other clients sharing an identical identification document
 * (Civil ID, Passport, Trade Licence...) with the given client -- the
 * strongest duplicate signal available. Used to offer a Merge action on
 * the client workspace, distinct from the advisory-only name/mobile/
 * email checks the onboarding wizard runs.
 */
async function findIdentificationDuplicates(clientId: string): Promise<ClientDuplicateMatch[]> {
  try {
    return await apiClient.get<ClientDuplicateMatch[]>(`/api/clients/${clientId}/duplicate-identifications`)
  } catch (error) {
    console.error(`Failed to check for identification duplicates for client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to check for duplicates')
  }
}

/**
 * Merges sourceClientId into targetClientId: moves child records and
 * projects, preserves the source's own contact identity, then soft-
 * deletes the source. Returns the updated target client.
 */
async function mergeClients(targetClientId: string, sourceClientId: string): Promise<Client> {
  try {
    return await apiClient.post<Client>(`/api/clients/${targetClientId}/merge`, { sourceClientId })
  } catch (error) {
    console.error(`Failed to merge client ${sourceClientId} into ${targetClientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to merge clients')
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

export interface ClientFullCreatePayload {
  client: Partial<Client>
  contacts: ClientContactInput[]
  address?: ClientAddressInput
  identification?: ClientIdentificationInput
}

/**
 * The New Client wizard's submit action -- creates the client and
 * every sub-record (contacts, address, identification, identification
 * document) immediately, in one call, with no staging or confirmation
 * step. Sends the identification file as multipart/form-data alongside
 * a single JSON-stringified `payload` field (it nests a variable-length
 * contacts list, so it can't be flattened into individual Form fields).
 */
async function createClientFull(
  payload: ClientFullCreatePayload,
  identificationFile: File | null,
  documentCategory?: string,
  documentTitle?: string,
): Promise<Client> {
  try {
    const formData = new FormData()
    formData.append('payload', JSON.stringify(payload))
    if (documentCategory) formData.append('documentCategory', documentCategory)
    if (documentTitle) formData.append('documentTitle', documentTitle)
    if (identificationFile) formData.append('identificationFile', identificationFile)
    return await apiClient.postForm<Client>('/api/clients/full', formData)
  } catch (error) {
    console.error('Failed to create client:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to create client')
  }
}

/**
 * Toggle a client's Active/Inactive status via backend API.
 */
async function setStatus(clientId: string, status: Client['status']): Promise<Client> {
  try {
    return await apiClient.patch<Client>(`/api/clients/${clientId}/status`, { status })
  } catch (error) {
    console.error(`Failed to update status for client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update client status')
  }
}

export type ClientUpdateInput = {
  companyName?: string
  contactPerson?: string
  mobile?: string
  email?: string
  city?: string
  communicationPreference?: ClientCommunicationPreference
  individualProfile?: ClientIndividualProfile
  organisationProfile?: ClientOrganisationProfile
  /** "" unassigns; omit to leave untouched. */
  accountManagerId?: string
  /** "" clears; omit to leave untouched. */
  notes?: string
}

/**
 * Update an existing client's profile via backend API. Deliberately typed
 * to only the fields the backend's ClientUpdate schema actually accepts --
 * status changes go through their own dedicated endpoint (setStatus above)
 * rather than this general-purpose one.
 */
async function updateClient(clientId: string, clientData: ClientUpdateInput): Promise<Client> {
  try {
    return await apiClient.patch<Client>(`/api/clients/${clientId}`, clientData)
  } catch (error) {
    console.error(`Failed to update client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update client')
  }
}

/**
 * Delete (soft-delete) a client via backend API -- recoverable via
 * restoreClient below.
 */
async function deleteClient(clientId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/clients/${clientId}`)
  } catch (error) {
    console.error(`Failed to delete client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to delete client')
  }
}

/**
 * Restore a soft-deleted client via backend API -- undoes deleteClient.
 */
async function restoreClient(clientId: string): Promise<Client> {
  try {
    return await apiClient.post<Client>(`/api/clients/${clientId}/restore`, {})
  } catch (error) {
    console.error(`Failed to restore client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to restore client')
  }
}

export const clientService = {
  getClients,
  getClientsPage,
  getClientById,
  getContactsForClient,
  createContact,
  updateContact,
  deleteContact,
  getAddressesForClient,
  createAddress,
  updateAddress,
  deleteAddress,
  getIdentificationsForClient,
  createIdentification,
  updateIdentification,
  deleteIdentification,
  getDocumentsForClient,
  downloadDocument,
  findPossibleDuplicates,
  findIdentificationDuplicates,
  mergeClients,
  createClient,
  createClientFull,
  updateClient,
  setStatus,
  deleteClient,
  restoreClient,
}
