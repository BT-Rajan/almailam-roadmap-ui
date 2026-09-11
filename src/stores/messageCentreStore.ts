import { defineStore } from 'pinia'

import { messageService } from '@/services/messageService'
import { useClientStore } from '@/stores/clientStore'
import { useProjectStore } from '@/stores/projectStore'
import type { Client } from '@/types/Client'
import type { MessageChannel, MessageLogEntry, MessageTemplate, SendMessagePayload } from '@/types/Message'
import type { Project } from '@/types/Project'

interface MessageCentreStoreState {
  templates: MessageTemplate[]
  log: MessageLogEntry[]
  isLoading: boolean
  isSending: boolean
  error: string | undefined
  searchTerm: string
  selectedClientId: string | undefined
  isComposeOpen: boolean
}

export const useMessageCentreStore = defineStore('messageCentre', {
  state: (): MessageCentreStoreState => ({
    templates: [],
    log: [],
    isLoading: false,
    isSending: false,
    error: undefined,
    searchTerm: '',
    selectedClientId: undefined,
    isComposeOpen: false,
  }),

  getters: {
    // clientStore/projectStore are the single, canonical places these
    // full lists live -- this store used to keep two more independently-
    // fetched copies of the exact same data (loadAll below). Client
    // needs its full contact fields here (composing a message needs
    // mobile/email), which clientStore's list already carries -- this
    // isn't a slimmed-down lookup, just no longer a duplicate fetch of
    // the same full records.
    clients(): Client[] {
      return useClientStore().clients
    },

    projects(): Project[] {
      return useProjectStore().projects
    },

    filteredClients(): Client[] {
      const term = this.searchTerm.trim().toLowerCase()
      if (term.length === 0) return this.clients

      return this.clients.filter(
        (client: Client) =>
          client.companyName.toLowerCase().includes(term) ||
          client.contactPerson.toLowerCase().includes(term) ||
          client.mobile.toLowerCase().includes(term) ||
          client.email.toLowerCase().includes(term) ||
          client.city.toLowerCase().includes(term),
      )
    },

    hasActiveFilters(state): boolean {
      return state.searchTerm.trim().length > 0
    },

    getClientById(): (clientId: string) => Client | undefined {
      return (clientId: string) => useClientStore().getClientById(clientId)
    },

    getProjectById(): (projectId: string) => Project | undefined {
      return (projectId: string) => useProjectStore().getProjectById(projectId)
    },

    getProjectsForClient(): (clientId: string) => Project[] {
      return (clientId: string) => this.projects.filter((project: Project) => project.clientId === clientId)
    },

    selectedClient(): Client | undefined {
      if (!this.selectedClientId) return undefined
      return this.getClientById(this.selectedClientId)
    },

    templatesForChannel(state) {
      return (channel: MessageChannel): MessageTemplate[] => state.templates.filter((template) => template.channel === channel)
    },

    recentLog(state): MessageLogEntry[] {
      return state.log
    },
  },

  actions: {
    async loadAll() {
      this.isLoading = true
      this.error = undefined
      try {
        const clientStore = useClientStore()
        const projectStore = useProjectStore()
        const [templates, log] = await Promise.all([
          messageService.getTemplates(),
          messageService.getMessageLog(),
          clientStore.clients.length === 0 ? clientStore.loadClients() : Promise.resolve(),
          projectStore.projects.length === 0 ? projectStore.loadProjects() : Promise.resolve(),
        ])
        this.templates = templates
        this.log = log
      } catch {
        this.error = 'Unable to load the Message Centre. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    setSearchTerm(value: string) {
      this.searchTerm = value
    },

    clearFilters() {
      this.searchTerm = ''
    },

    openCompose(clientId: string) {
      this.selectedClientId = clientId
      this.isComposeOpen = true
    },

    closeCompose() {
      this.isComposeOpen = false
    },

    async sendMessage(payload: SendMessagePayload): Promise<MessageLogEntry> {
      this.isSending = true
      try {
        const entry = await messageService.sendMessage(payload)
        this.log = [entry, ...this.log]
        return entry
      } finally {
        this.isSending = false
      }
    },
  },
})
