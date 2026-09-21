import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { LOCALE_STORAGE_KEY } from '@/constants/locale'
import { ensureLocaleMessages, i18n } from '@/i18n'
import { useLocaleStore } from '@/stores/localeStore'

const arabicMessagesLoaded = () => Object.keys(i18n.global.getLocaleMessage('ar-KW')).length > 0

// The Arabic table is filled once per test file (the module registry caches
// it), so these run as one ordered story rather than each starting clean.
describe('lazy Arabic messages', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('does not bundle Arabic up front: only English is registered at startup', () => {
    expect(arabicMessagesLoaded()).toBe(false)
    expect(i18n.global.t('common.save')).toBe('Save')
  })

  it('English never triggers a download', async () => {
    await ensureLocaleMessages('en')
    expect(arabicMessagesLoaded()).toBe(false)
  })

  it('switching to Arabic loads the messages BEFORE the locale changes', async () => {
    const store = useLocaleStore()
    const switching = store.setLocale('ar-KW')

    // Still English while the download is in flight -- no flash of fallback text.
    expect(i18n.global.locale.value).toBe('en')
    expect(store.locale).toBe('en')

    await switching
    expect(arabicMessagesLoaded()).toBe(true)
    expect(i18n.global.locale.value).toBe('ar-KW')
    expect(i18n.global.t('common.save')).toBe('حفظ')
    expect(store.locale).toBe('ar-KW')
    expect(store.isRtl).toBe(true)
    expect(document.documentElement.dir).toBe('rtl')
    expect(localStorage.getItem(LOCALE_STORAGE_KEY)).toBe('ar-KW')
  })

  it('switching back to English restores English text', async () => {
    const store = useLocaleStore()
    await store.setLocale('en')
    expect(i18n.global.t('common.save')).toBe('Save')
    expect(document.documentElement.dir).toBe('ltr')
  })

  it('loading again is instant and does not re-register anything', async () => {
    const spy = vi.spyOn(i18n.global, 'setLocaleMessage')
    await ensureLocaleMessages('ar-KW')
    await ensureLocaleMessages('ar-KW')
    expect(spy).not.toHaveBeenCalled()
    spy.mockRestore()
  })

  it('initializeLocale applies a saved Arabic preference once its messages are ready', async () => {
    localStorage.setItem(LOCALE_STORAGE_KEY, 'ar-KW')
    setActivePinia(createPinia())
    const store = useLocaleStore()
    await store.initializeLocale()
    expect(i18n.global.locale.value).toBe('ar-KW')
    expect(document.documentElement.lang).toBe('ar-KW')
  })

  it('toggleLocale flips between the two languages', async () => {
    const store = useLocaleStore()
    await store.setLocale('en')
    await store.toggleLocale()
    expect(store.locale).toBe('ar-KW')
    await store.toggleLocale()
    expect(store.locale).toBe('en')
  })
})
