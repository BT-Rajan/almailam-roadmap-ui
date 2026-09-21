import { createI18n } from 'vue-i18n'

import { DEFAULT_LOCALE } from '@/constants/locale'
import type { Locale } from '@/types/Locale'

import { loadNamespaces } from './namespaces'
import type { GlobModules, LocaleMessages } from './namespaces'

// English is bundled with the app: it is the fallback for every other locale,
// so it must always be present. Other locales are loaded on demand (see
// ensureLocaleMessages) -- their messages are a large share of the entry
// bundle that every visitor would otherwise download even if they never use
// that language.
const enModules = import.meta.glob('./locales/en/*.ts', { eager: true }) as GlobModules

const messages: Record<Locale, LocaleMessages> = {
  en: loadNamespaces(enModules),
  'ar-KW': {},
}

export const i18n = createI18n<[LocaleMessages], Locale, false>({
  legacy: false,
  locale: DEFAULT_LOCALE,
  fallbackLocale: 'en',
  messages,
})

const LAZY_LOCALE_LOADERS: Partial<Record<Locale, () => Promise<LocaleMessages>>> = {
  'ar-KW': () => import('./arKwMessages').then((module) => module.default),
}

const pendingLoads = new Map<Locale, Promise<void>>()

/**
 * Makes sure a locale's messages are registered, downloading them first if it
 * is one that loads on demand. Resolves immediately for English (always
 * bundled) and for a locale that has already been loaded; concurrent callers
 * share one download. A failed download is not remembered, so the next call
 * retries.
 *
 * Callers must await this BEFORE switching `i18n.global.locale` to that
 * locale -- switching first would show English (the fallback) until the
 * messages arrived.
 */
export function ensureLocaleMessages(locale: Locale): Promise<void> {
  const load = LAZY_LOCALE_LOADERS[locale]
  if (!load) return Promise.resolve()

  let pending = pendingLoads.get(locale)
  if (!pending) {
    pending = load()
      .then((localeMessages) => {
        i18n.global.setLocaleMessage(locale, localeMessages)
      })
      .catch((error) => {
        pendingLoads.delete(locale)
        throw error
      })
    pendingLoads.set(locale, pending)
  }
  return pending
}
