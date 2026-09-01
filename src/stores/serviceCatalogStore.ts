import { defineStore } from 'pinia'

import { serviceCatalogService } from '@/services/serviceCatalogService'
import type { ServiceCatalogBranch, ServiceCatalogItem } from '@/types/ServiceCatalog'

interface ServiceCatalogStoreState {
  services: ServiceCatalogItem[]
  selectedServiceId: string | undefined
  isLoading: boolean
  error: string | undefined
  isMutating: boolean
  mutationError: string | undefined
}

export const useServiceCatalogStore = defineStore('serviceCatalog', {
  state: (): ServiceCatalogStoreState => ({
    services: [],
    selectedServiceId: undefined,
    isLoading: false,
    error: undefined,
    isMutating: false,
    mutationError: undefined,
  }),

  getters: {
    selectedService(state): ServiceCatalogItem | undefined {
      return state.services.find((service) => service.id === state.selectedServiceId)
    },
  },

  actions: {
    async loadServices() {
      this.isLoading = true
      this.error = undefined
      try {
        this.services = await serviceCatalogService.getServices()
        if (!this.selectedServiceId && this.services.length > 0) {
          this.selectedServiceId = this.services[0]!.id
        }
      } catch {
        this.error = 'Unable to load the service catalog. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    selectService(serviceId: string) {
      this.selectedServiceId = serviceId
    },

    // Duplicate names are rejected by the backend (case-insensitive, see
    // service_catalog_service._assert_name_available) -- the store just
    // surfaces whatever message comes back rather than re-checking
    // client-side, so there's exactly one source of truth for what
    // counts as a duplicate.
    async addService(name: string, branch: ServiceCatalogBranch) {
      this.isMutating = true
      this.mutationError = undefined
      try {
        const service = await serviceCatalogService.createService(name, branch)
        this.services = [...this.services, service].sort((a, b) => a.name.localeCompare(b.name))
        this.selectedServiceId = service.id
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to add the service. Please try again.'
      } finally {
        this.isMutating = false
      }
    },

    async renameService(serviceId: string, name: string) {
      this.isMutating = true
      this.mutationError = undefined
      try {
        const updated = await serviceCatalogService.renameService(serviceId, name)
        this.services = this.services
          .map((service) => (service.id === serviceId ? updated : service))
          .sort((a, b) => a.name.localeCompare(b.name))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to rename the service. Please try again.'
      } finally {
        this.isMutating = false
      }
    },

    async removeService(serviceId: string) {
      this.isMutating = true
      this.mutationError = undefined
      try {
        await serviceCatalogService.removeService(serviceId)
        this.services = this.services.filter((service) => service.id !== serviceId)
        if (this.selectedServiceId === serviceId) {
          this.selectedServiceId = this.services[0]?.id
        }
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to remove the service. Please try again.'
      } finally {
        this.isMutating = false
      }
    },

    async addActivity(name: string, fixedCost: number) {
      const service = this.selectedService
      if (!service) return
      this.isMutating = true
      this.mutationError = undefined
      try {
        const activity = await serviceCatalogService.addActivity(service.id, name, fixedCost)
        service.activities = [...service.activities, activity]
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to add the activity. Please try again.'
      } finally {
        this.isMutating = false
      }
    },

    async updateActivity(activityId: string, fields: { name?: string; fixedCost?: number }) {
      const service = this.selectedService
      if (!service) return
      this.isMutating = true
      this.mutationError = undefined
      try {
        const updated = await serviceCatalogService.updateActivity(activityId, fields)
        service.activities = service.activities.map((activity) => (activity.id === activityId ? updated : activity))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to update the activity. Please try again.'
      } finally {
        this.isMutating = false
      }
    },

    async removeActivity(activityId: string) {
      const service = this.selectedService
      if (!service) return
      this.isMutating = true
      this.mutationError = undefined
      try {
        await serviceCatalogService.removeActivity(activityId)
        service.activities = service.activities.filter((activity) => activity.id !== activityId)
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to remove the activity. Please try again.'
      } finally {
        this.isMutating = false
      }
    },
  },
})
