import { defineStore } from 'pinia'

import { companyService } from '@/services/companyService'
import { applyBrandColor } from '@/utils/colorScale'
import type { CompanyBranding, CompanySettings } from '@/types/CompanySettings'

interface CompanyStoreState {
  settings: CompanySettings | undefined
  branding: CompanyBranding | undefined
  isLoading: boolean
  isSaving: boolean
  error: string | undefined
}

export const useCompanyStore = defineStore('company', {
  state: (): CompanyStoreState => ({
    settings: undefined,
    branding: undefined,
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
      // Live preview -- an admin editing the color picker sees the whole
      // app's accent shift immediately, not only after Save.
      if (field === 'brandColor') applyBrandColor(value as string)
    },

    async saveSettings(): Promise<boolean> {
      if (!this.settings) return false
      this.isSaving = true
      try {
        this.settings = await companyService.saveCompanySettings(this.settings)
        this.branding = { companyName: this.settings.companyName, brandColor: this.settings.brandColor, hasLogo: this.settings.hasLogo }
        applyBrandColor(this.settings.brandColor)
        return true
      } catch {
        this.error = 'Unable to save company settings. Please try again.'
        return false
      } finally {
        this.isSaving = false
      }
    },

    /**
     * Loads just the branding subset (no Administration:view needed --
     * see companyService.getBranding) and applies it app-wide. Called
     * once on app boot for every authenticated role; harmless to call
     * again (e.g. after re-login) since it's idempotent.
     */
    async loadBranding(): Promise<void> {
      try {
        this.branding = await companyService.getBranding()
        applyBrandColor(this.branding.brandColor)
      } catch {
        // Keep whatever's already applied (the #3995be CSS default, or a
        // previously-loaded branding) -- a failed fetch here shouldn't
        // block the rest of the app from working.
      }
    },

    async uploadLogo(file: File): Promise<void> {
      this.settings = await companyService.uploadLogo(file)
    },

    async deleteLogo(): Promise<void> {
      this.settings = await companyService.deleteLogo()
    },
  },
})
