import { defineStore } from 'pinia'

export const useNavigationStore = defineStore('navigation', {
  state: () => ({
    isSidebarCollapsed: false,
    isMobileSidebarOpen: false,
  }),

  actions: {
    toggleSidebarCollapsed() {
      this.isSidebarCollapsed = !this.isSidebarCollapsed
    },

    openMobileSidebar() {
      this.isMobileSidebarOpen = true
    },

    closeMobileSidebar() {
      this.isMobileSidebarOpen = false
    },
  },
})
