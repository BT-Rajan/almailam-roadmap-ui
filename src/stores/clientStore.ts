import { defineStore } from 'pinia'

import { clientService } from '@/services/clientService'
import type {
  ClientAddressInput,
  ClientAddressUpdateInput,
  ClientConsentInput,
  ClientContactInput,
  ClientContactUpdateInput,
  ClientDocumentInput,
  ClientDocumentUpdateInput,
  ClientIdentificationInput,
  ClientIdentificationUpdateInput,
  ClientUpdateInput,
  ClientVerificationInput,
} from '@/services/clientService'
import type {
  Client,
  ClientAddress,
  ClientAuditEvent,
  ClientConsent,
  ClientContact,
  ClientDocument,
  ClientIdentification,
  ClientOnboardingState,
  ClientStatus,
  ClientType,
  ClientVerification,
  ClientViewMode,
} from '@/types/Client'

interface ClientPaginationState {
  page: number
  pageSize: number
  total: number
  totalPages: number
}

interface ClientStoreState {
  clients: Client[]
  isLoading: boolean
  error: string | undefined
  searchTerm: string
  typeFilter: ClientType | 'All'
  statusFilter: ClientStatus | 'All'
  onboardingFilter: ClientOnboardingState | 'All'
  viewMode: ClientViewMode
  contacts: ClientContact[]
  addresses: ClientAddress[]
  identifications: ClientIdentification[]
  documents: ClientDocument[]
  verifications: ClientVerification[]
  consents: ClientConsent[]
  auditEvents: ClientAuditEvent[]
  isDetailLoading: boolean
  detailError: string | undefined
  // Server-paginated browse state for ClientsPage -- separate from
  // `clients` above, which stays a full, unpaginated cache because other
  // pages (e.g. the client workspace) look a client up locally by id
  // rather than fetching it individually.
  pageItems: Client[]
  pagination: ClientPaginationState
  isPageLoading: boolean
}

export const useClientStore = defineStore('client', {
  state: (): ClientStoreState => ({
    clients: [],
    isLoading: false,
    error: undefined,
    searchTerm: '',
    typeFilter: 'All',
    statusFilter: 'All',
    onboardingFilter: 'All',
    viewMode: 'grid',
    contacts: [],
    addresses: [],
    identifications: [],
    documents: [],
    verifications: [],
    consents: [],
    auditEvents: [],
    isDetailLoading: false,
    detailError: undefined,
    pageItems: [],
    pagination: { page: 1, pageSize: 9, total: 0, totalPages: 1 },
    isPageLoading: false,
  }),

  getters: {
    hasActiveFilters(state): boolean {
      return (
        state.searchTerm.trim().length > 0 ||
        state.typeFilter !== 'All' ||
        state.statusFilter !== 'All' ||
        state.onboardingFilter !== 'All'
      )
    },

    getClientById(state) {
      return (clientId: string): Client | undefined => state.clients.find((client) => client.id === clientId)
    },
  },

  actions: {
    async loadClients() {
      this.isLoading = true
      this.error = undefined
      try {
        this.clients = await clientService.getClients()
      } catch {
        this.error = 'Unable to load clients. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    // Fetches just the current page/filter/sort combination from the
    // server for the Clients browse table -- the actual pagination fix,
    // as opposed to loadClients() above which still loads everything
    // (safely, in bounded pages) for cross-reference lookups.
    async loadClientsPage() {
      this.isPageLoading = true
      this.error = undefined
      try {
        const result = await clientService.getClientsPage({
          page: this.pagination.page,
          pageSize: this.pagination.pageSize,
          search: this.searchTerm.trim() || undefined,
          clientType: this.typeFilter !== 'All' ? this.typeFilter : undefined,
          status: this.statusFilter !== 'All' ? this.statusFilter : undefined,
          onboardingState: this.onboardingFilter !== 'All' ? this.onboardingFilter : undefined,
        })
        this.pageItems = result.items
        this.pagination = {
          page: result.page,
          pageSize: result.pageSize,
          total: result.total,
          totalPages: result.totalPages,
        }
      } catch {
        this.error = 'Unable to load clients. Please try again.'
      } finally {
        this.isPageLoading = false
      }
    },

    setPage(page: number) {
      this.pagination.page = page
      void this.loadClientsPage()
    },

    setPageSize(size: number) {
      this.pagination.pageSize = size
      this.pagination.page = 1
      void this.loadClientsPage()
    },

    async loadClientDetail(clientId: string) {
      this.isDetailLoading = true
      this.detailError = undefined
      try {
        const [contacts, addresses, identifications, documents, verifications, consents, auditEvents] = await Promise.all([
          clientService.getContactsForClient(clientId),
          clientService.getAddressesForClient(clientId),
          clientService.getIdentificationsForClient(clientId),
          clientService.getDocumentsForClient(clientId),
          clientService.getVerificationsForClient(clientId),
          clientService.getConsentsForClient(clientId),
          clientService.getAuditEventsForClient(clientId),
        ])
        this.contacts = contacts
        this.addresses = addresses
        this.identifications = identifications
        this.documents = documents
        this.verifications = verifications
        this.consents = consents
        this.auditEvents = auditEvents
      } catch {
        this.detailError = 'Unable to load the client profile. Please try again.'
      } finally {
        this.isDetailLoading = false
      }
    },

    setSearchTerm(term: string) {
      this.searchTerm = term
    },

    // Called from the search box's debounced @search event, once the
    // person has paused typing, so we're not firing a request per keystroke.
    applySearch(term: string) {
      this.searchTerm = term
      this.pagination.page = 1
      void this.loadClientsPage()
    },

    setTypeFilter(type: ClientType | 'All') {
      this.typeFilter = type
      this.pagination.page = 1
      void this.loadClientsPage()
    },

    setStatusFilter(status: ClientStatus | 'All') {
      this.statusFilter = status
      this.pagination.page = 1
      void this.loadClientsPage()
    },

    setOnboardingFilter(state: ClientOnboardingState | 'All') {
      this.onboardingFilter = state
      this.pagination.page = 1
      void this.loadClientsPage()
    },

    setViewMode(mode: ClientViewMode) {
      this.viewMode = mode
    },

    addClient(client: Client) {
      this.clients = [client, ...this.clients]
    },

    // Persists a new client via the backend API. Prefer this over
    // addClient() above, which only mutates local state -- this was the
    // cause of a serious bug: the New Client Wizard appeared to onboard a
    // client successfully, but nothing was ever actually saved, so it
    // vanished on refresh.
    async createClient(clientData: Partial<Client>) {
      const client = await clientService.createClient(clientData)
      this.clients = [client, ...this.clients]
      return client
    },

    // Persists an edit to an existing client's profile via the backend
    // API and updates the cached copy in both `clients` (workspace page)
    // and `pageItems` (browse table) so the change shows up immediately.
    async updateClient(clientId: string, input: ClientUpdateInput) {
      const updated = await clientService.updateClient(clientId, input)
      this.clients = this.clients.map((c) => (c.id === clientId ? updated : c))
      this.pageItems = this.pageItems.map((c) => (c.id === clientId ? updated : c))
      return updated
    },

    // Toggles Active/Inactive. Kept separate from updateClient() since it
    // maps to its own dedicated, simpler backend endpoint rather than the
    // general-purpose profile PATCH.
    async setClientStatus(clientId: string, status: Client['status']) {
      const updated = await clientService.setStatus(clientId, status)
      this.clients = this.clients.map((c) => (c.id === clientId ? updated : c))
      this.pageItems = this.pageItems.map((c) => (c.id === clientId ? updated : c))
      return updated
    },

    // Deletes (soft) a client via the backend API and removes it from
    // both local caches. The backend itself blocks this if the client
    // still has active projects on file.
    async deleteClient(clientId: string) {
      await clientService.deleteClient(clientId)
      this.clients = this.clients.filter((c) => c.id !== clientId)
      this.pageItems = this.pageItems.filter((c) => c.id !== clientId)
    },

    addContact(contact: ClientContact) {
      this.contacts = [...this.contacts, contact]
    },

    // Persists a client contact via the backend API. Prefer this over
    // addContact() above, which only mutates local state.
    async createContact(clientId: string, input: ClientContactInput) {
      const contact = await clientService.createContact(clientId, input)
      this.contacts = [...this.contacts, contact]
      return contact
    },

    async updateContact(clientId: string, contactId: string, input: ClientContactUpdateInput) {
      const updated = await clientService.updateContact(clientId, contactId, input)
      this.contacts = this.contacts.map((c) => (c.id === contactId ? updated : c))
      return updated
    },

    async deleteContact(clientId: string, contactId: string) {
      await clientService.deleteContact(clientId, contactId)
      this.contacts = this.contacts.filter((c) => c.id !== contactId)
    },

    addAddress(address: ClientAddress) {
      this.addresses = [...this.addresses, address]
    },

    // Persists a client address via the backend API. Prefer this over
    // addAddress() above, which only mutates local state -- see
    // createDocument() below for why that matters.
    async createAddress(clientId: string, input: ClientAddressInput) {
      const address = await clientService.createAddress(clientId, input)
      this.addresses = [...this.addresses, address]
      return address
    },

    async updateAddress(clientId: string, addressId: string, input: ClientAddressUpdateInput) {
      const updated = await clientService.updateAddress(clientId, addressId, input)
      this.addresses = this.addresses.map((a) => (a.id === addressId ? updated : a))
      return updated
    },

    async deleteAddress(clientId: string, addressId: string) {
      await clientService.deleteAddress(clientId, addressId)
      this.addresses = this.addresses.filter((a) => a.id !== addressId)
    },

    addIdentification(identification: ClientIdentification) {
      this.identifications = [...this.identifications, identification]
    },

    // Persists a client identification document via the backend API.
    // Prefer this over addIdentification() above, which only mutates
    // local state.
    async createIdentification(clientId: string, input: ClientIdentificationInput) {
      const identification = await clientService.createIdentification(clientId, input)
      this.identifications = [...this.identifications, identification]
      return identification
    },

    async updateIdentification(clientId: string, identificationId: string, input: ClientIdentificationUpdateInput) {
      const updated = await clientService.updateIdentification(clientId, identificationId, input)
      this.identifications = this.identifications.map((i) => (i.id === identificationId ? updated : i))
      return updated
    },

    async deleteIdentification(clientId: string, identificationId: string) {
      await clientService.deleteIdentification(clientId, identificationId)
      this.identifications = this.identifications.filter((i) => i.id !== identificationId)
    },

    addDocument(document: ClientDocument) {
      this.documents = [document, ...this.documents]
    },

    // Persists a client document via the backend API. Prefer this over
    // addDocument() above, which only mutates local state and was the
    // cause of a real bug: documents "uploaded" during client onboarding
    // and from the client workspace were never actually saved anywhere.
    async createDocument(clientId: string, input: ClientDocumentInput) {
      const document = await clientService.createDocument(clientId, input)
      this.documents = [document, ...this.documents]
      return document
    },

    async updateDocument(clientId: string, documentId: string, input: ClientDocumentUpdateInput) {
      const updated = await clientService.updateDocument(clientId, documentId, input)
      this.documents = this.documents.map((d) => (d.id === documentId ? updated : d))
      return updated
    },

    async replaceDocumentFile(clientId: string, documentId: string, file: File) {
      const updated = await clientService.replaceDocumentFile(clientId, documentId, file)
      this.documents = this.documents.map((d) => (d.id === documentId ? updated : d))
      return updated
    },

    async deleteDocument(clientId: string, documentId: string) {
      await clientService.deleteDocument(clientId, documentId)
      this.documents = this.documents.filter((d) => d.id !== documentId)
    },

    async downloadDocument(clientId: string, documentId: string, filename: string) {
      const blob = await clientService.downloadDocument(clientId, documentId)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      link.click()
      URL.revokeObjectURL(url)
    },

    // Advances/changes a client's onboarding state via the backend's
    // transition engine and updates the cached copy in both `clients`
    // (used by the workspace page) and `pageItems` (used by the browse
    // table) so the new state shows up immediately without a full reload.
    async setOnboardingState(clientId: string, onboardingState: ClientOnboardingState, reason?: string) {
      const updated = await clientService.updateOnboardingState(clientId, { onboardingState, reason })
      this.clients = this.clients.map((c) => (c.id === clientId ? updated : c))
      this.pageItems = this.pageItems.map((c) => (c.id === clientId ? updated : c))
      return updated
    },

    // Records a verification check via the backend API. When it's tied to
    // a specific document, the backend also updates that document's own
    // verificationStatus in the same transaction -- mirrored here on the
    // cached copy so the Documents tab reflects it immediately.
    async createVerification(clientId: string, input: ClientVerificationInput) {
      const verification = await clientService.createVerification(clientId, input)
      this.verifications = [verification, ...this.verifications]
      if (verification.documentId) {
        this.documents = this.documents.map((d) =>
          d.id === verification.documentId ? { ...d, verificationStatus: verification.result } : d,
        )
      }
      return verification
    },

    recordConsent(consent: ClientConsent) {
      this.consents = [consent, ...this.consents]
    },

    // Persists a client consent via the backend API. Prefer this over
    // recordConsent() above, which only mutates local state.
    async createConsent(clientId: string, input: ClientConsentInput) {
      const consent = await clientService.createConsent(clientId, input)
      this.consents = [consent, ...this.consents]
      return consent
    },

    clearFilters() {
      this.searchTerm = ''
      this.typeFilter = 'All'
      this.statusFilter = 'All'
      this.onboardingFilter = 'All'
      this.pagination.page = 1
      void this.loadClientsPage()
    },

    async findDuplicates(name: string, mobile: string, email: string, registrationNumber?: string) {
      return clientService.findPossibleDuplicates(name, mobile, email, registrationNumber)
    },
  },
})
