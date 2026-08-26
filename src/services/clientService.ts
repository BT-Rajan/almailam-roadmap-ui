import { apiClient } from '@/services/httpClient'
import { useAuthStore } from '@/stores/authStore'
import type {
  Client,
  ClientAddress,
  ClientAuditEvent,
  ClientCommunicationPreference,
  ClientContact,
  ClientDocument,
  ClientDocumentVersion,
  ClientDuplicateMatch,
  ClientIdentification,
  ClientIndividualProfile,
  ClientOnboardingState,
  ClientOrganisationProfile,
  ClientVerification,
  ClientVerificationResult,
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
  params: PageParams & { clientType?: string; status?: string; onboardingState?: string; accountManagerId?: string } = {},
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

export type ClientDocumentInput = {
  category: ClientDocument['category']
  title: string
  issueDate?: string
  expiryDate?: string
  issuingAuthority?: string
  file: File
}

/**
 * Upload a new client document via backend API. Sends the actual file as
 * multipart/form-data -- apiClient always JSON-encodes its body, so this
 * bypasses it and does a raw fetch instead, same pattern as
 * documentService.ts's uploadDocument() for project documents (including
 * the 401 -> refresh -> retry-once flow, since apiClient's helper only
 * covers JSON requests).
 */
async function createDocument(clientId: string, input: ClientDocumentInput): Promise<ClientDocument> {
  const authStore = useAuthStore()
  const formData = new FormData()
  formData.append('category', input.category)
  formData.append('title', input.title)
  if (input.issueDate) formData.append('issueDate', input.issueDate)
  if (input.expiryDate) formData.append('expiryDate', input.expiryDate)
  if (input.issuingAuthority) formData.append('issuingAuthority', input.issuingAuthority)
  formData.append('file', input.file)

  const doRequest = () =>
    fetch(`/api/clients/${clientId}/documents`, {
      method: 'POST',
      headers: authStore.accessToken ? { Authorization: `Bearer ${authStore.accessToken}` } : undefined,
      credentials: 'include',
      body: formData,
    })

  try {
    let response = await doRequest()

    if (response.status === 401) {
      const refreshed = await authStore.tryRefresh()
      if (refreshed) {
        response = await doRequest()
      }
    }

    if (!response.ok) {
      const data = await response.json().catch(() => undefined)
      throw new Error(data?.error ?? data?.detail ?? data?.message ?? `Upload failed with status ${response.status}`)
    }

    return (await response.json()) as ClientDocument
  } catch (error) {
    console.error(`Failed to record document for client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to record document')
  }
}

export interface IdentificationVerificationResult {
  checked: boolean
  matches?: boolean
  reasoning?: string
}

/**
 * Vision-based plausibility check for the New Client wizard's
 * identification upload -- not tied to a client id, since this is
 * called before any client record exists yet. `checked: false` means
 * the AI couldn't evaluate the file (disabled, unconfigured, provider
 * error, or a PDF, which this check doesn't attempt) -- the wizard
 * treats that as "accept with a manual verification caveat," not as a
 * rejection. A non-2xx response here means the file itself was
 * rejected outright (wrong type, over the 5 MB limit, content doesn't
 * match its extension) -- callers should surface that as a hard error.
 */
async function verifyIdentificationDocument(file: File, documentType: string): Promise<IdentificationVerificationResult> {
  const authStore = useAuthStore()
  const formData = new FormData()
  formData.append('file', file)
  formData.append('documentType', documentType)

  const doRequest = () =>
    fetch('/api/clients/verify-identification-document', {
      method: 'POST',
      headers: authStore.accessToken ? { Authorization: `Bearer ${authStore.accessToken}` } : undefined,
      credentials: 'include',
      body: formData,
    })

  let response = await doRequest()
  if (response.status === 401) {
    const refreshed = await authStore.tryRefresh()
    if (refreshed) response = await doRequest()
  }

  if (!response.ok) {
    const data = await response.json().catch(() => undefined)
    throw new Error(data?.error ?? data?.detail ?? data?.message ?? `Verification failed with status ${response.status}`)
  }

  return (await response.json()) as IdentificationVerificationResult
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

export type ClientDocumentUpdateInput = {
  category?: ClientDocument['category']
  title?: string
  issueDate?: string
  expiryDate?: string
  issuingAuthority?: string
}

/**
 * Update a client document's metadata (title, category, dates, issuing
 * authority) via backend API. Does not replace the stored file -- use
 * replaceDocumentFile() below for that.
 */
async function updateDocument(clientId: string, documentId: string, input: ClientDocumentUpdateInput): Promise<ClientDocument> {
  try {
    return await apiClient.patch<ClientDocument>(`/api/clients/${clientId}/documents/${documentId}`, input)
  } catch (error) {
    console.error(`Failed to update document ${documentId} for client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update document')
  }
}

/**
 * Replace a client document's stored file with a new one, bumping its
 * version. The replaced file's own version is preserved and remains
 * downloadable -- see getDocumentVersions()/downloadDocumentVersion()
 * below -- rather than being silently discarded.
 */
async function replaceDocumentFile(clientId: string, documentId: string, file: File, notes?: string): Promise<ClientDocument> {
  const authStore = useAuthStore()
  const formData = new FormData()
  formData.append('file', file)
  if (notes) formData.append('notes', notes)

  const doRequest = () =>
    fetch(`/api/clients/${clientId}/documents/${documentId}/replace-file`, {
      method: 'POST',
      headers: authStore.accessToken ? { Authorization: `Bearer ${authStore.accessToken}` } : undefined,
      credentials: 'include',
      body: formData,
    })

  try {
    let response = await doRequest()
    if (response.status === 401) {
      const refreshed = await authStore.tryRefresh()
      if (refreshed) response = await doRequest()
    }
    if (!response.ok) {
      const data = await response.json().catch(() => undefined)
      throw new Error(data?.error ?? data?.detail ?? data?.message ?? `Upload failed with status ${response.status}`)
    }
    return (await response.json()) as ClientDocument
  } catch (error) {
    console.error(`Failed to replace file for document ${documentId} on client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to replace document file')
  }
}

/**
 * Fetch the full version history for a client document -- every past
 * file, not just the current one, each genuinely downloadable via
 * downloadDocumentVersion() below.
 */
async function getDocumentVersions(clientId: string, documentId: string): Promise<ClientDocumentVersion[]> {
  try {
    return await apiClient.get<ClientDocumentVersion[]>(`/api/clients/${clientId}/documents/${documentId}/versions`)
  } catch (error) {
    console.error(`Failed to fetch versions for document ${documentId} on client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch document versions')
  }
}

/**
 * Download one specific past version's file (not necessarily the
 * current one) -- this is what actually makes version history useful
 * for recovering a prior revision, not just a read-only log.
 */
async function downloadDocumentVersion(clientId: string, documentId: string, versionId: string): Promise<Blob> {
  const authStore = useAuthStore()
  try {
    const response = await fetch(`/api/clients/${clientId}/documents/${documentId}/versions/${versionId}/download`, {
      method: 'GET',
      headers: authStore.accessToken ? { Authorization: `Bearer ${authStore.accessToken}` } : undefined,
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error(`Download failed with status ${response.status}`)
    }

    return await response.blob()
  } catch (error) {
    console.error(`Failed to download version ${versionId} of document ${documentId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to download document version')
  }
}

/**
 * Remove a client document via backend API (soft delete -- the stored
 * file is retained on disk, same as the main project Documents module).
 */
async function deleteDocument(clientId: string, documentId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/clients/${clientId}/documents/${documentId}`)
  } catch (error) {
    console.error(`Failed to delete document ${documentId} for client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to delete document')
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

export type ClientOnboardingStateInput = {
  onboardingState: ClientOnboardingState
  reason?: string
}

/**
 * Advance or change a client's onboarding state via backend API. The
 * backend re-validates the transition against its own state machine
 * (app/core/status_transitions.py) and requires a reason for certain
 * target states -- this call can be rejected even if the UI offered it.
 */
async function updateOnboardingState(clientId: string, input: ClientOnboardingStateInput): Promise<Client> {
  try {
    return await apiClient.patch<Client>(`/api/clients/${clientId}/onboarding-state`, input)
  } catch (error) {
    console.error(`Failed to update onboarding state for client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update onboarding state')
  }
}

/**
 * Walks a client forward through every onboarding transition that has
 * exactly one legal next state, in a single call -- replaces what used
 * to be several separate "Change Status" round trips for the common
 * case where each step has nothing to actually decide. Stops on its
 * own at the first genuine decision point or reason-requiring state;
 * see client_service.auto_advance_onboarding on the backend.
 */
async function autoAdvanceOnboarding(clientId: string): Promise<Client> {
  try {
    return await apiClient.post<Client>(`/api/clients/${clientId}/onboarding-state/auto-advance`, {})
  } catch (error) {
    console.error(`Failed to auto-advance onboarding for client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to advance onboarding')
  }
}

export type ClientVerificationInput = {
  item: string
  result: ClientVerificationResult
  notes?: string
  documentId?: string
}

/**
 * Record a new client verification via backend API. When documentId is
 * given, the backend also updates that document's own verificationStatus
 * to match -- see createVerification() below in the store for the local
 * cache update that keeps the document list in sync without a re-fetch.
 */
async function createVerification(clientId: string, input: ClientVerificationInput): Promise<ClientVerification> {
  try {
    return await apiClient.post<ClientVerification>(`/api/clients/${clientId}/verifications`, input)
  } catch (error) {
    console.error(`Failed to record verification for client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to record verification')
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
 * status and onboardingState changes go through their own dedicated,
 * reason-validated endpoints (setStatus / updateOnboardingState above)
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
  createDocument,
  verifyIdentificationDocument,
  updateDocument,
  replaceDocumentFile,
  getDocumentVersions,
  downloadDocumentVersion,
  deleteDocument,
  downloadDocument,
  getVerificationsForClient,
  createVerification,
  updateOnboardingState,
  autoAdvanceOnboarding,
  getAuditEventsForClient,
  findPossibleDuplicates,
  findIdentificationDuplicates,
  mergeClients,
  createClient,
  updateClient,
  setStatus,
  deleteClient,
}
