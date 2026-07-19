import { defineStore } from 'pinia'

import { DEFAULT_THEME_MODE, THEME_STORAGE_KEY } from '@/constants/theme'
import type { ThemeMode } from '@/types/Theme'

function readStoredMode(): ThemeMode {
  const stored = localStorage.getItem(THEME_STORAGE_KEY)
  return stored === 'dark' || stored === 'light' ? stored : DEFAULT_THEME_MODE
}

function applyModeToDocument(mode: ThemeMode): void {
  document.documentElement.classList.toggle('dark', mode === 'dark')
}

export const useThemeStore = defineStore('theme', {
  state: () => ({
    mode: readStoredMode() as ThemeMode,
  }),

  getters: {
    isDark: (state) => state.mode === 'dark',
  },

  actions: {
    setMode(mode: ThemeMode) {
      this.mode = mode
      localStorage.setItem(THEME_STORAGE_KEY, mode)
      applyModeToDocument(mode)
    },

    toggleMode() {
      this.setMode(this.mode === 'dark' ? 'light' : 'dark')
    },

    initializeTheme() {
      applyModeToDocument(this.mode)
    },
  },
})
