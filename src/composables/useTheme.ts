import { storeToRefs } from 'pinia'

import { useThemeStore } from '@/stores/themeStore'

export function useTheme() {
  const themeStore = useThemeStore()
  const { mode, isDark } = storeToRefs(themeStore)

  return {
    mode,
    isDark,
    setMode: themeStore.setMode,
    toggleMode: themeStore.toggleMode,
  }
}
