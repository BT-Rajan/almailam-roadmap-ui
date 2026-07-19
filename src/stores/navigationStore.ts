import { defineStore } from 'pinia'

const SIDEBAR_COLLAPSED_STORAGE_KEY = 'serviceos-sidebar-collapsed'
const TABLET_MAX_WIDTH = 1024

function getInitialCollapsedState(): boolean {
  const stored = localStorage.getItem(SIDEBAR_COLLAPSED_STORAGE_KEY)
  if (stored !== null) return stored === 'true'

  // No saved preference yet: default to collapsed on tablet-sized viewports
  // to leave more room for content, matching the desktop default otherwise.
  if (typeof window !== 'undefined') {
    return window.innerWidth < TABLET_MAX_WIDTH
  }
  return false
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
