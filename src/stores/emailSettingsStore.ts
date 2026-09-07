import { defineStore } from 'pinia'

import { emailSettingsService } from '@/services/emailSettingsService'
import type { EmailProviderId, EmailProviderPreset, EmailSettings, EmailSettingsTestResult } from '@/types/EmailSettings'

interface EmailSettingsStoreState {
  settings: EmailSettings | undefined
  presets: Record<EmailProviderId, EmailProviderPreset> | undefined
  isLoading: boolean
  isSaving: boolean
  isTesting: boolean
  error: string | undefined
  testResult: EmailSettingsTestResult | undefined
}

export const useEmailSettingsStore = defineStore('emailSettings', {
  state: (): EmailSettingsStoreState => ({
    settings: undefined,
    presets: undefined,
    isLoading: false,
    isSaving: false,
    isTesting: false,
    error: undefined,
    testResult: undefined,
  }),

  actions: {
    async loadSettings() {
      this.isLoading = true
      this.error = undefined
      try {
        const [settings, presets] = await Promise.all([
          emailSettingsService.getSettings(),
          this.presets ? Promise.resolve(this.presets) : emailSettingsService.getProviderPresets(),
        ])
        this.settings = settings
        this.presets = presets
      } catch (error) {
        // Surfaces the real backend message (permission error, a genuine
        // server fault, etc.) instead of a fixed generic string that
        // gave no way to tell what actually went wrong.
        this.error = error instanceof Error && error.message ? error.message : 'Unable to load email settings. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    updateField<K extends keyof EmailSettings>(field: K, value: EmailSettings[K]) {
      if (!this.settings) return
      this.settings = { ...this.settings, [field]: value }
    },

    // Applies a provider's preset host/port/TLS values to the form --
    // does not touch anything else (username, from address, password).
    applyProviderPreset(providerId: EmailProviderId) {
      if (!this.settings || !this.presets) return
      const preset = this.presets[providerId]
      if (!preset) return
      this.settings = {
        ...this.settings,
        provider: providerId,
        smtpHost: preset.smtpHost,
        smtpPort: preset.smtpPort,
        smtpUseTls: preset.smtpUseTls,
      }
    },

    // Stages a raw password locally (see EmailSettings.password) -- it
    // isn't sent to the server, and hasPassword isn't touched, until
    // Save Changes actually persists it (see saveSettings below).
    updatePassword(rawPassword: string) {
      if (!this.settings) return
      this.settings = { ...this.settings, password: rawPassword }
    },

    async saveSettings(): Promise<boolean> {
      if (!this.settings) return false
      this.isSaving = true
      try {
        this.settings = await emailSettingsService.saveSettings(this.settings)
        this.testResult = undefined
        return true
      } catch (error) {
        this.error = error instanceof Error && error.message ? error.message : 'Unable to save email settings. Please try again.'
        return false
      } finally {
        this.isSaving = false
      }
    },

    async testConnection(): Promise<EmailSettingsTestResult> {
      this.isTesting = true
      try {
        const result = await emailSettingsService.testConnection()
        this.testResult = result
        // The backend records the outcome against the saved row --
        // refresh so lastTestedAt/lastTestOk reflect it without a
        // second round trip's worth of manual field-syncing here.
        this.settings = await emailSettingsService.getSettings()
        return result
      } finally {
        this.isTesting = false
      }
    },
  },
})
