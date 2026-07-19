import { defineStore } from 'pinia'

import { companyService } from '@/services/companyService'
import type { CompanySettings } from '@/types/CompanySettings'

interface CompanyStoreState {
  settings: CompanySettings | undefined
  isLoading: boolean
  isSaving: boolean
  error: string | undefined
}

export const useCompanyStore = defineStore('company', {
  state: (): CompanyStoreState => ({
    settings: undefined,
    isLoading: false,
    isSaving: false,
    error: undefined,
  }),

  actions: {
    async loadSettings() {
      this.isLoading = true
      this.error = undefined
      try {
        this.settings = await companyService.getCompanySettings()
      } catch {
        this.error = 'Unable to load company settings. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    updateField<K extends keyof CompanySettings>(field: K, value: CompanySettings[K]) {
      if (!this.settings) return
      this.settings = { ...this.settings, [field]: value }
    },

    async saveSettings(): Promise<boolean> {
      if (!this.settings) return false
      this.isSaving = true
      try {
        this.settings = await companyService.saveCompanySettings(this.settings)
        return true
      } catch {
        this.error = 'Unable to save company settings. Please try again.'
        return false
      } finally {
        this.isSaving = false
      }
    },
  },
})
