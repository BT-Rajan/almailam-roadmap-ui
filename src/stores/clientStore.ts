import { defineStore } from 'pinia'

import { clientService } from '@/services/clientService'
import type {
  ClientAddressInput,
  ClientAddressUpdateInput,
  ClientContactInput,
  ClientContactUpdateInput,
  ClientFullCreatePayload,
  ClientIdentificationInput,
  ClientIdentificationUpdateInput,
  ClientUpdateInput,
} from '@/services/clientService'
import { useAuthStore } from '@/stores/authStore'
import { triggerBlobDownload } from '@/utils/fileDownload'
import type {
  Client,
  ClientAddress,
  ClientContact,
  ClientDocument,
  ClientIdentification,
  ClientStatus,
  ClientType,
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
  typeFilter: ClientType | 'All'
  statusFilter: ClientStatus | 'All'
  myClientsOnly: boolean
  // Browses soft-deleted clients (see restoreClient) instead of active
  // ones -- an admin-only alternate view of the same paginated table,
  // not combined with the type/status filters above.
  showDeleted: boolean
  viewMode: ClientViewMode
  contacts: ClientContact[]
  addresses: ClientAddress[]
  identifications: ClientIdentification[]
  documents: ClientDocument[]
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
    typeFilter: 'All',
    statusFilter: 'All',
    myClientsOnly: false,
    showDeleted: false,
    viewMode: 'grid',
    contacts: [],
    addresses: [],
    identifications: [],
    documents: [],
    isDetailLoading: false,
    detailError: undefined,
    pageItems: [],
    pagination: { page: 1, pageSize: 9, total: 0, totalPages: 1 },
    isPageLoading: false,
  }),

  getters: {
    hasActiveFilters(state): boolean {
      return state.typeFilter !== 'All' || state.statusFilter !== 'All' || state.myClientsOnly
    },

    // Indexed once per change to `clients` (Pinia getters are cached the
    // same way a Vue computed is) rather than rebuilt on every lookup --
    // getClientById below is called once per row for every list in the
    // app that shows a client name (Tasks, Documents, Payments,
    // Government Submissions, Message Centre, ...), so an O(n) `.find()`
    // there turns rendering an N-row list into O(n*m) work against the
    // client table instead of O(n).
    clientById(state): Map<string, Client> {
      return new Map(state.clients.map((client) => [client.id, client]))
    },

    getClientById(): (clientId: string) => Client | undefined {
      return (clientId: string) => this.clientById.get(clientId)
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
        const authStore = useAuthStore()
        const result = await clientService.getClientsPage({
          page: this.pagination.page,
          pageSize: this.pagination.pageSize,
          clientType: this.typeFilter !== 'All' ? this.typeFilter : undefined,
          status: this.statusFilter !== 'All' ? this.statusFilter : undefined,
          accountManagerId: this.myClientsOnly ? authStore.user?.id : undefined,
          deleted: this.showDeleted,
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
        const [contacts, addresses, identifications, documents] = await Promise.all([
          clientService.getContactsForClient(clientId),
          clientService.getAddressesForClient(clientId),
          clientService.getIdentificationsForClient(clientId),
          clientService.getDocumentsForClient(clientId),
        ])
        this.contacts = contacts
        this.addresses = addresses
        this.identifications = identifications
        this.documents = documents
      } catch {
        this.detailError = 'Unable to load the client profile. Please try again.'
      } finally {
        this.isDetailLoading = false
      }
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

    // Toggles between browsing active clients and browsing soft-deleted
    // ones (the Deleted Clients view, paired with restoreClient below).
    setShowDeleted(value: boolean) {
      this.showDeleted = value
      this.pagination.page = 1
      void this.loadClientsPage()
    },

    setMyClientsOnly(value: boolean) {
      this.myClientsOnly = value
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

    // The New Client wizard's submit action -- creates the client and
    // every sub-record (contacts, address, identification document)
    // immediately, in one call, with no staging/confirmation step.
    async createClientFull(
      payload: ClientFullCreatePayload,
      identificationFile: File | null,
      documentCategory?: string,
      documentTitle?: string,
    ) {
      const client = await clientService.createClientFull(payload, identificationFile, documentCategory, documentTitle)
      this.clients = [client, ...this.clients]
      return client
    },

    // Shared by updateClient/setClientStatus below -- both patch the same
    // client into both caches after a mutating call succeeds.
    patchClientInCache(clientId: string, updated: Client) {
      this.clients = this.clients.map((c) => (c.id === clientId ? updated : c))
      this.pageItems = this.pageItems.map((c) => (c.id === clientId ? updated : c))
    },

    // Persists an edit to an existing client's profile via the backend
    // API and updates the cached copy in both `clients` (workspace page)
    // and `pageItems` (browse table) so the change shows up immediately.
    async updateClient(clientId: string, input: ClientUpdateInput) {
      const updated = await clientService.updateClient(clientId, input)
      this.patchClientInCache(clientId, updated)
      return updated
    },

    // Toggles Active/Inactive. Kept separate from updateClient() since it
    // maps to its own dedicated, simpler backend endpoint rather than the
    // general-purpose profile PATCH.
    async setClientStatus(clientId: string, status: Client['status']) {
      const updated = await clientService.setStatus(clientId, status)
      this.patchClientInCache(clientId, updated)
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

    // Undoes deleteClient -- restores a soft-deleted client and removes
    // it from the Deleted Clients view's page cache (it belongs back
    // among active clients now, not this list).
    async restoreClient(clientId: string) {
      const restored = await clientService.restoreClient(clientId)
      this.pageItems = this.pageItems.filter((c) => c.id !== clientId)
      return restored
    },

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

    async downloadDocument(clientId: string, documentId: string, filename: string) {
      const blob = await clientService.downloadDocument(clientId, documentId)
      triggerBlobDownload(blob, filename)
    },

    // Opens the document in a new tab instead of saving it -- used by the
    // "View" action (e.g. the Customer ID Documents section of a
    // project's Documents tab), separate from the "Download" action
    // above which triggers a Save As.
    async viewDocument(clientId: string, documentId: string) {
      const blob = await clientService.downloadDocument(clientId, documentId)
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank', 'noopener,noreferrer')
    },

    clearFilters() {
      this.typeFilter = 'All'
      this.statusFilter = 'All'
      this.myClientsOnly = false
      this.pagination.page = 1
      void this.loadClientsPage()
    },

    async findDuplicates(name: string, mobile: string, email: string, registrationNumber?: string) {
      return clientService.findPossibleDuplicates(name, mobile, email, registrationNumber)
    },

    async findIdentificationDuplicates(clientId: string) {
      return clientService.findIdentificationDuplicates(clientId)
    },

    // Merges sourceClientId into this store's currently-loaded target
    // client, then refreshes the target's own detail data in place
    // (its own record may have gained a preserved contact, an inherited
    // account manager, or appended notes from the merge).
    async mergeClients(targetClientId: string, sourceClientId: string) {
      const updated = await clientService.mergeClients(targetClientId, sourceClientId)
      this.clients = this.clients.map((c) => (c.id === targetClientId ? updated : c))
      this.pageItems = this.pageItems.filter((c) => c.id !== sourceClientId).map((c) => (c.id === targetClientId ? updated : c))
      await this.loadClientDetail(targetClientId)
      return updated
    },
  },
})
