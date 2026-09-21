import { defineStore } from 'pinia'

import { DEFAULT_LOCALE, LOCALE_STORAGE_KEY, RTL_LOCALES } from '@/constants/locale'
import { ensureLocaleMessages, i18n } from '@/i18n'
import type { Locale } from '@/types/Locale'

function readStoredLocale(): Locale {
  const stored = localStorage.getItem(LOCALE_STORAGE_KEY)
  return stored === 'en' || stored === 'ar-KW' ? stored : DEFAULT_LOCALE
}

function applyLocaleToDocument(locale: Locale): void {
  document.documentElement.lang = locale
  document.documentElement.dir = RTL_LOCALES.includes(locale) ? 'rtl' : 'ltr'
}

function applyLocaleToI18n(locale: Locale): void {
  i18n.global.locale.value = locale
}

export const useLocaleStore = defineStore('locale', {
  state: () => ({
    locale: readStoredLocale() as Locale,
  }),

  getters: {
    isRtl: (state) => RTL_LOCALES.includes(state.locale),
  },

  actions: {
    // Loads the locale's messages (Arabic downloads on demand) BEFORE
    // switching, so the UI never flashes English while they arrive. If the
    // download fails the current locale stays in place, nothing is saved, and
    // the user can simply try again.
    async setLocale(locale: Locale) {
      try {
        await ensureLocaleMessages(locale)
      } catch (error) {
        console.error(`Failed to load ${locale} messages:`, error)
        return
      }
      this.locale = locale
      localStorage.setItem(LOCALE_STORAGE_KEY, locale)
      applyLocaleToDocument(locale)
      applyLocaleToI18n(locale)
    },

    async toggleLocale() {
      await this.setLocale(this.locale === 'en' ? 'ar-KW' : 'en')
    },

    // Runs once at startup and must finish before the app mounts (see
    // main.ts), or a returning Arabic user would see English first. If their
    // saved language can't be loaded the app starts in English instead of not
    // starting; the saved preference is left alone so the next visit retries.
    async initializeLocale() {
      try {
        await ensureLocaleMessages(this.locale)
      } catch (error) {
        console.error(`Failed to load ${this.locale} messages, starting in ${DEFAULT_LOCALE}:`, error)
        this.locale = DEFAULT_LOCALE
      }
      applyLocaleToDocument(this.locale)
      applyLocaleToI18n(this.locale)
    },
  },
})
