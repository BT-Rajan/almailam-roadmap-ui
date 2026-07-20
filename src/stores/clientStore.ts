import { defineStore } from 'pinia'

import { clientService } from '@/services/clientService'
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
  }),

  getters: {
    filteredClients(state): Client[] {
      const term = state.searchTerm.trim().toLowerCase()

      return state.clients.filter((client) => {
        const matchesSearch =
          term.length === 0 ||
          client.companyName.toLowerCase().includes(term) ||
          client.contactPerson.toLowerCase().includes(term) ||
          client.mobile.replace(/\D/g, '').includes(term.replace(/\D/g, '')) ||
          client.email.toLowerCase().includes(term)

        const matchesType = state.typeFilter === 'All' || client.clientType === state.typeFilter
        const matchesStatus = state.statusFilter === 'All' || client.status === state.statusFilter
        const matchesOnboarding = state.onboardingFilter === 'All' || client.onboardingState === state.onboardingFilter

        return matchesSearch && matchesType && matchesStatus && matchesOnboarding
      })
    },

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

    setTypeFilter(type: ClientType | 'All') {
      this.typeFilter = type
    },

    setStatusFilter(status: ClientStatus | 'All') {
      this.statusFilter = status
    },

    setOnboardingFilter(state: ClientOnboardingState | 'All') {
      this.onboardingFilter = state
    },

    setViewMode(mode: ClientViewMode) {
      this.viewMode = mode
    },

    addClient(client: Client) {
      this.clients = [client, ...this.clients]
    },

    addContact(contact: ClientContact) {
      this.contacts = [...this.contacts, contact]
    },

    addDocument(document: ClientDocument) {
      this.documents = [document, ...this.documents]
    },

    recordConsent(consent: ClientConsent) {
      this.consents = [consent, ...this.consents]
    },

    clearFilters() {
      this.searchTerm = ''
      this.typeFilter = 'All'
      this.statusFilter = 'All'
      this.onboardingFilter = 'All'
    },
  },
})
