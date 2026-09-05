import { createI18n } from 'vue-i18n'

import { DEFAULT_LOCALE } from '@/constants/locale'
import type { Locale } from '@/types/Locale'

type LocaleMessages = Record<string, unknown>
type GlobModules = Record<string, { default: LocaleMessages }>

// Each domain (common, navigation, dashboard, client, ...) lives in its own
// file under locales/<locale>/, named after its top-level message namespace
// (e.g. locales/en/client.ts -> messages.en.client). Loaded via import.meta.glob
// instead of a hand-maintained barrel file so adding a new domain file is
// enough on its own -- no index to keep in sync, and no merge conflicts
// between domains being translated at the same time.
function loadNamespaces(modules: GlobModules): LocaleMessages {
  const messages: LocaleMessages = {}
  for (const path in modules) {
    const namespace = path.split('/').pop()?.replace(/\.ts$/, '')
    if (!namespace) continue
    messages[namespace] = modules[path].default
  }
  return messages
}

const enModules = import.meta.glob('./locales/en/*.ts', { eager: true }) as GlobModules
const arKwModules = import.meta.glob('./locales/ar-KW/*.ts', { eager: true }) as GlobModules

const messages: Record<Locale, LocaleMessages> = {
  en: loadNamespaces(enModules),
  'ar-KW': loadNamespaces(arKwModules),
}

export const i18n = createI18n<[LocaleMessages], Locale, false>({
  legacy: false,
  locale: DEFAULT_LOCALE,
  fallbackLocale: 'en',
  messages,
})
