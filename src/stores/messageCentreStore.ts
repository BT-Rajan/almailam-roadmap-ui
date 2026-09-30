import { defineStore } from 'pinia'

import { messageService } from '@/services/messageService'
import { useClientStore } from '@/stores/clientStore'
import { useProjectStore } from '@/stores/projectStore'
import type { Client } from '@/types/Client'
import type { MessageChannel, MessageLogEntry, MessageTemplate, SendEmailPayload, SendMessagePayload } from '@/types/Message'
import type { PagedResponse } from '@/types/Pagination'
import type { Project } from '@/types/Project'
import { triggerBlobDownload } from '@/utils/fileDownload'
import { describeStoreError } from '@/utils/storeError'

interface MessageCentreStoreState {
  templates: MessageTemplate[]
  log: MessageLogEntry[]
  logPagination: { page: number; pageSize: number; total: number; totalPages: number }
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
    logPagination: { page: 1, pageSize: 25, total: 0, totalPages: 0 },
    isLoading: false,
    isSending: false,
    error: undefined,
    searchTerm: '',
    selectedClientId: undefined,
    isComposeOpen: false,
  }),

  getters: {
    // clientStore/projectStore are the single, canonical places these
    // full lists live. Client needs its full contact fields here
    // (composing a message needs mobile/email), which clientStore's
    // list already carries.
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
        // The client directory is this page's purpose, so it loads every
        // client. Projects are NOT all downloaded: the log carries its
        // project names, and a client's projects are fetched when a message
        // to that client is composed (loadProjectsForClient below).
        const clientStore = useClientStore()
        const [templates, log] = await Promise.all([
          messageService.getTemplates(),
          messageService.getMessageLog(1, this.logPagination.pageSize),
          !clientStore.isFullyLoaded ? clientStore.loadClients() : Promise.resolve(),
        ])
        this.templates = templates
        this.applyLogPage(log)
      } catch (error) {
        this.error = describeStoreError('Unable to load the Message Centre. Please try again.', error)
      } finally {
        this.isLoading = false
      }
    },

    applyLogPage(result: PagedResponse<MessageLogEntry>) {
      this.log = result.items
      this.logPagination = { page: result.page, pageSize: result.pageSize, total: result.total, totalPages: result.totalPages }
    },

    // The log is paged on the server: it only grows, so it is never
    // downloaded whole.
    async loadLogPage(page: number, pageSize?: number) {
      try {
        this.applyLogPage(await messageService.getMessageLog(page, pageSize ?? this.logPagination.pageSize))
      } catch (error) {
        this.error = describeStoreError('Unable to load the message log. Please try again.', error)
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

    // Just the selected client's projects, for the compose form's
    // "related project" picker.
    async loadProjectsForClient(clientId: string) {
      await useProjectStore().loadProjectsForClient(clientId)
    },

    closeCompose() {
      this.isComposeOpen = false
    },

    async sendMessage(payload: SendMessagePayload): Promise<MessageLogEntry> {
      this.isSending = true
      try {
        const entry = await messageService.sendMessage(payload)
        void this.loadLogPage(1)
        return entry
      } finally {
        this.isSending = false
      }
    },

    // Real send (SMTP, optional attachments) -- see messageService.sendEmail.
    // A delivery failure is still recorded as a 'Failed' MessageLogEntry
    // on the backend (see message_service.send_email), but the backend
    // also raises alongside logging it, so this call rejects too -- the
    // compose dialog's own catch block surfaces the error toast, and the
    // failed entry shows up in this.log on the next page load rather than
    // being spliced in here.
    async sendEmail(payload: SendEmailPayload): Promise<MessageLogEntry> {
      this.isSending = true
      try {
        const entry = await messageService.sendEmail(payload)
        void this.loadLogPage(1)
        return entry
      } finally {
        this.isSending = false
      }
    },

    async downloadAttachment(messageId: string, attachmentId: string, filename: string) {
      const blob = await messageService.downloadAttachment(messageId, attachmentId)
      triggerBlobDownload(blob, filename)
    },
  },
})
