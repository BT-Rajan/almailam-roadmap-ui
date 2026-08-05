import { computed } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import type { CurrentUser } from '@/services/authService'

/**
 * Composable for accessing authentication state and actions
 * 
 * Usage:
 * ```typescript
 * const { isAuthenticated, user, login, logout } = useAuth()
 * 
 * async function handleLogin(username: string, password: string) {
 *   try {
 *     await login(username, password)
 *     // User is now logged in
 *   } catch (error) {
 *     console.error('Login failed:', error)
 *   }
 * }
 * ```
 */
export function useAuth() {
  const authStore = useAuthStore()

  return {
    // Computed state
    isAuthenticated: computed(() => authStore.isAuthenticated),
    user: computed(() => authStore.user),
    accessToken: computed(() => authStore.accessToken),
    refreshToken: computed(() => authStore.refreshToken),

    // Computed user info
    username: computed(() => authStore.user?.name),
    userRole: computed(() => authStore.user?.role),
    isAdmin: computed(() => authStore.user?.role === 'Administrator'),

    // Actions
    login: (username: string, password: string) => authStore.login(username, password),
    logout: () => authStore.logout(),
    tryRefresh: () => authStore.tryRefresh(),
    hydrate: () => authStore.hydrate(),
  }
}
