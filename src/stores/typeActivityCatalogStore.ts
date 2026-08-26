import { defineStore } from 'pinia'

import { typeActivityCatalogService } from '@/services/typeActivityCatalogService'
import type { TypeActivityCategory } from '@/types/TypeActivityCatalog'

interface TypeActivityCatalogStoreState {
  categories: TypeActivityCategory[]
  selectedCategoryId: string | undefined
  isLoading: boolean
  error: string | undefined
  isMutating: boolean
  mutationError: string | undefined
}

export const useTypeActivityCatalogStore = defineStore('typeActivityCatalog', {
  state: (): TypeActivityCatalogStoreState => ({
    categories: [],
    selectedCategoryId: undefined,
    isLoading: false,
    error: undefined,
    isMutating: false,
    mutationError: undefined,
  }),

  getters: {
    selectedCategory(state): TypeActivityCategory | undefined {
      return state.categories.find((category) => category.id === state.selectedCategoryId)
    },
  },

  actions: {
    async loadCategories() {
      this.isLoading = true
      this.error = undefined
      try {
        this.categories = await typeActivityCatalogService.getCategories()
        if (!this.selectedCategoryId && this.categories.length > 0) {
          this.selectedCategoryId = this.categories[0]!.id
        }
      } catch {
        this.error = 'Unable to load the type activity catalog. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    selectCategory(categoryId: string) {
      this.selectedCategoryId = categoryId
    },

    // Duplicate names are rejected by the backend (case-insensitive, see
    // service_catalog_service._assert_name_available) -- the store just
    // surfaces whatever message comes back rather than re-checking
    // client-side, so there's exactly one source of truth for what
    // counts as a duplicate.
    async addCategory(name: string) {
      this.isMutating = true
      this.mutationError = undefined
      try {
        const category = await typeActivityCatalogService.createCategory(name)
        this.categories = [...this.categories, category].sort((a, b) => a.name.localeCompare(b.name))
        this.selectedCategoryId = category.id
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to add the category. Please try again.'
      } finally {
        this.isMutating = false
      }
    },

    async renameCategory(categoryId: string, name: string) {
      this.isMutating = true
      this.mutationError = undefined
      try {
        const updated = await typeActivityCatalogService.renameCategory(categoryId, name)
        this.categories = this.categories
          .map((category) => (category.id === categoryId ? updated : category))
          .sort((a, b) => a.name.localeCompare(b.name))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to rename the category. Please try again.'
      } finally {
        this.isMutating = false
      }
    },

    async removeCategory(categoryId: string) {
      this.isMutating = true
      this.mutationError = undefined
      try {
        await typeActivityCatalogService.removeCategory(categoryId)
        this.categories = this.categories.filter((category) => category.id !== categoryId)
        if (this.selectedCategoryId === categoryId) {
          this.selectedCategoryId = this.categories[0]?.id
        }
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to remove the category. Please try again.'
      } finally {
        this.isMutating = false
      }
    },

    async addActivity(name: string, cost: number) {
      const category = this.selectedCategory
      if (!category) return
      this.isMutating = true
      this.mutationError = undefined
      try {
        const activity = await typeActivityCatalogService.addActivity(category.id, name, cost)
        category.activities = [...category.activities, activity]
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to add the activity. Please try again.'
      } finally {
        this.isMutating = false
      }
    },

    async updateActivity(activityId: string, fields: { name?: string; cost?: number }) {
      const category = this.selectedCategory
      if (!category) return
      this.isMutating = true
      this.mutationError = undefined
      try {
        const updated = await typeActivityCatalogService.updateActivity(activityId, fields)
        category.activities = category.activities.map((activity) => (activity.id === activityId ? updated : activity))
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to update the activity. Please try again.'
      } finally {
        this.isMutating = false
      }
    },

    async removeActivity(activityId: string) {
      const category = this.selectedCategory
      if (!category) return
      this.isMutating = true
      this.mutationError = undefined
      try {
        await typeActivityCatalogService.removeActivity(activityId)
        category.activities = category.activities.filter((activity) => activity.id !== activityId)
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to remove the activity. Please try again.'
      } finally {
        this.isMutating = false
      }
    },
  },
})
