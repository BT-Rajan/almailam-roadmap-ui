import { defineStore } from 'pinia'

import { permitCatalogService } from '@/services/permitCatalogService'
import type { PermitApplicationSetupInput, PermitCatalogItem } from '@/types/PermitCatalog'
import { describeStoreError } from '@/utils/storeError'

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
      } catch (error) {
        this.error = describeStoreError('Unable to load the permit catalog. Please try again.', error)
      } finally {
        this.isLoading = false
      }
    },

    async addPermit(name: string, fixedCost: number) {
      this.isMutating = true
      this.mutationError = undefined
      try {
        const permit = await permitCatalogService.createPermit(name, fixedCost)
        this.permits = [...this.permits, permit].sort((a, b) => a.name.localeCompare(b.name))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to add the permit. Please try again.'
      } finally {
        this.isMutating = false
      }
    },

    async renamePermit(permitId: string, name: string, fixedCost: number) {
      this.isMutating = true
      this.mutationError = undefined
      try {
        const updated = await permitCatalogService.renamePermit(permitId, name, fixedCost)
        this.permits = this.permits
          .map((permit) => (permit.id === permitId ? updated : permit))
          .sort((a, b) => a.name.localeCompare(b.name))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to rename the permit. Please try again.'
      } finally {
        this.isMutating = false
      }
    },

    async setApplicationSetup(permitId: string, setup: PermitApplicationSetupInput) {
      this.isMutating = true
      this.mutationError = undefined
      try {
        const updated = await permitCatalogService.setApplicationSetup(permitId, setup)
        this.permits = this.permits.map((permit) => (permit.id === permitId ? updated : permit))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to save the application setup. Please try again.'
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
