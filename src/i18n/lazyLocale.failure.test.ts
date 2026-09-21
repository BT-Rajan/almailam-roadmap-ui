import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { LOCALE_STORAGE_KEY } from '@/constants/locale'
import { ensureLocaleMessages, i18n } from '@/i18n'
import { useLocaleStore } from '@/stores/localeStore'

// Simulates the Arabic chunk failing to download (offline, deploy in
// progress, etc.).
vi.mock('@/i18n/arKwMessages', () => ({
  get default(): never {
    throw new Error('chunk failed to load')
  },
}))

describe('when the Arabic messages fail to download', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  it('ensureLocaleMessages rejects, and does not cache the failure', async () => {
    await expect(ensureLocaleMessages('ar-KW')).rejects.toThrow('chunk failed')
    await expect(ensureLocaleMessages('ar-KW')).rejects.toThrow('chunk failed')
  })

  it('a failed switch leaves the current language and saved preference untouched', async () => {
    const store = useLocaleStore()
    await store.setLocale('ar-KW')

    expect(store.locale).toBe('en')
    expect(i18n.global.locale.value).toBe('en')
    expect(localStorage.getItem(LOCALE_STORAGE_KEY)).toBeNull()
    expect(i18n.global.t('common.save')).toBe('Save')
  })

  it('the app still starts, in English, and keeps the saved preference for next time', async () => {
    localStorage.setItem(LOCALE_STORAGE_KEY, 'ar-KW')
    setActivePinia(createPinia())
    const store = useLocaleStore()

    await expect(store.initializeLocale()).resolves.toBeUndefined()

    expect(i18n.global.locale.value).toBe('en')
    expect(document.documentElement.lang).toBe('en')
    expect(localStorage.getItem(LOCALE_STORAGE_KEY)).toBe('ar-KW')
  })
})
