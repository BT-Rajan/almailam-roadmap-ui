import { defineStore } from 'pinia'

import { permitCatalogService } from '@/services/permitCatalogService'
import type { PermitCatalogItem } from '@/types/PermitCatalog'

interface PermitCatalogStoreState {
  permits: PermitCatalogItem[]
  isLoading: boolean
  error: string | undefined
  isMutating: boolean
  mutationError: string | undefined
}

export const usePermitCatalogStore = defineStore('permitCatalog', {
  state: (): PermitCatalogStoreState => ({
    permits: [],
    isLoading: false,
    error: undefined,
    isMutating: false,
    mutationError: undefined,
  }),

  actions: {
    async loadPermits() {
      this.isLoading = true
      this.error = undefined
      try {
        this.permits = await permitCatalogService.getPermits()
      } catch {
        this.error = 'Unable to load the permit catalog. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    async addPermit(name: string) {
      this.isMutating = true
      this.mutationError = undefined
      try {
        const permit = await permitCatalogService.createPermit(name)
        this.permits = [...this.permits, permit].sort((a, b) => a.name.localeCompare(b.name))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to add the permit. Please try again.'
      } finally {
        this.isMutating = false
      }
    },

    async renamePermit(permitId: string, name: string) {
      this.isMutating = true
      this.mutationError = undefined
      try {
        const updated = await permitCatalogService.renamePermit(permitId, name)
        this.permits = this.permits
          .map((permit) => (permit.id === permitId ? updated : permit))
          .sort((a, b) => a.name.localeCompare(b.name))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to rename the permit. Please try again.'
      } finally {
        this.isMutating = false
      }
    },

    async removePermit(permitId: string) {
      this.isMutating = true
      this.mutationError = undefined
      try {
        await permitCatalogService.removePermit(permitId)
        this.permits = this.permits.filter((permit) => permit.id !== permitId)
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to remove the permit. Please try again.'
      } finally {
        this.isMutating = false
      }
    },
  },
})
