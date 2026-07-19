import { defineStore } from 'pinia'

import { clientService } from '@/services/clientService'
import { messageService } from '@/services/messageService'
import { projectService } from '@/services/projectService'
import type { Client } from '@/types/Client'
import type { MessageChannel, MessageLogEntry, MessageTemplate, SendMessagePayload } from '@/types/Message'
import type { Project } from '@/types/Project'

interface MessageCentreStoreState {
  clients: Client[]
  projects: Project[]
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
    clients: [],
    projects: [],
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
    filteredClients(state): Client[] {
      const term = state.searchTerm.trim().toLowerCase()
      if (term.length === 0) return state.clients

      return state.clients.filter(
        (client) =>
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

    getClientById(state) {
      return (clientId: string): Client | undefined => state.clients.find((client) => client.id === clientId)
    },

    getProjectById(state) {
      return (projectId: string): Project | undefined => state.projects.find((project) => project.id === projectId)
    },

    getProjectsForClient(state) {
      return (clientId: string): Project[] => state.projects.filter((project) => project.clientId === clientId)
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
        const [clients, projects, templates, log] = await Promise.all([
          clientService.getClients(),
          projectService.getProjects(),
          messageService.getTemplates(),
          messageService.getMessageLog(),
        ])
        this.clients = clients
        this.projects = projects
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
