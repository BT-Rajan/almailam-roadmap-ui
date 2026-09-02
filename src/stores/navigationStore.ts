import { defineStore } from 'pinia'

const SIDEBAR_COLLAPSED_STORAGE_KEY = 'serviceos-sidebar-collapsed'

function getInitialCollapsedState(): boolean {
  const stored = localStorage.getItem(SIDEBAR_COLLAPSED_STORAGE_KEY)
  if (stored !== null) return stored === 'true'

  // No saved preference yet: default to collapsed everywhere, desktop
  // included, to leave more room for content until the user opts to
  // expand it themselves (see toggleSidebarCollapsed, which persists
  // that choice from then on).
  return true
}

export const useNavigationStore = defineStore('navigation', {
  state: () => ({
    isSidebarCollapsed: getInitialCollapsedState(),
    isMobileSidebarOpen: false,
  }),

  actions: {
    toggleSidebarCollapsed() {
      this.isSidebarCollapsed = !this.isSidebarCollapsed
      localStorage.setItem(SIDEBAR_COLLAPSED_STORAGE_KEY, String(this.isSidebarCollapsed))
    },

    openMobileSidebar() {
      this.isMobileSidebarOpen = true
    },

    closeMobileSidebar() {
      this.isMobileSidebarOpen = false
    },
  },
})
