import { watch } from 'vue'

import { useAuthStore } from '@/stores/authStore'
import { useCompanyStore } from '@/stores/companyStore'
import { useKnowledgeStore } from '@/stores/knowledgeStore'
import { useServerTimeStore } from '@/stores/serverTimeStore'

/**
 * Hands what the server sends with every new token (Kuwait date,
 * branding, knowledgebase switch -- authStore.session) to the stores that
 * own them, so starting the app is one request, not four. Lives here
 * rather than in authStore because those stores' services import
 * httpClient, which imports authStore.
 *
 * Synchronous, so it's applied before the router guard that awaited
 * sign-in moves on (and would otherwise ask for the server date itself).
 */
export function installSessionBootstrap(): void {
  const authStore = useAuthStore()
  watch(
    () => authStore.session,
    (session) => {
      if (!session) return
      useServerTimeStore().setToday(session.serverTime.date)
      useCompanyStore().applyBranding(session.branding)
      useKnowledgeStore().setEnabledLocally(session.knowledgeEnabled)
    },
    { flush: 'sync', immediate: true },
  )
}
