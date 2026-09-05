import type { Locale } from '@/types/Locale'

export const LOCALE_STORAGE_KEY = 'serviceos-locale'

export const DEFAULT_LOCALE: Locale = 'en'

export const RTL_LOCALES: Locale[] = ['ar-KW']

export const SUPPORTED_LOCALES: { value: Locale; label: string; nativeLabel: string }[] = [
  { value: 'en', label: 'English', nativeLabel: 'English' },
  { value: 'ar-KW', label: 'Arabic (Kuwait)', nativeLabel: 'العربية' },
]
