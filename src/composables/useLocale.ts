import { storeToRefs } from 'pinia'

import { useLocaleStore } from '@/stores/localeStore'

export function useLocale() {
  const localeStore = useLocaleStore()
  const { locale, isRtl } = storeToRefs(localeStore)

  return {
    locale,
    isRtl,
    setLocale: localeStore.setLocale,
    toggleLocale: localeStore.toggleLocale,
  }
}
