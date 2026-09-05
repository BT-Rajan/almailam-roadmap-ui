import { defineStore } from 'pinia'

import { DEFAULT_LOCALE, LOCALE_STORAGE_KEY, RTL_LOCALES } from '@/constants/locale'
import { i18n } from '@/i18n'
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
    setLocale(locale: Locale) {
      this.locale = locale
      localStorage.setItem(LOCALE_STORAGE_KEY, locale)
      applyLocaleToDocument(locale)
      applyLocaleToI18n(locale)
    },

    toggleLocale() {
      this.setLocale(this.locale === 'en' ? 'ar-KW' : 'en')
    },

    initializeLocale() {
      applyLocaleToDocument(this.locale)
      applyLocaleToI18n(this.locale)
    },
  },
})
