import { watch } from 'vue'
import { useRouter } from 'vue-router'

import { ROUTE_NAMES } from '@/constants/routeNames'
import { useAuthStore } from '@/stores/authStore'

// 30 minutes of no mouse/keyboard/touch/scroll activity signs the user out,
// even though the access token itself would otherwise keep silently
// renewing via the refresh cookie for as long as the tab stays open.
const IDLE_TIMEOUT_MS = 30 * 60 * 1000

// Listening on window in the capture phase catches activity anywhere in the
// document, including inside iframes/portals that don't bubble normally.
const ACTIVITY_EVENTS = ['mousemove', 'mousedown', 'keydown', 'wheel', 'touchstart', 'scroll'] as const

/**
 * Wires up a single app-wide idle timer (call once, from App.vue). Resets
 * on any activity event while a session is active; on timeout, logs out
 * and bounces to the right login screen for whichever portal the person
 * was using, with a message explaining why they landed there.
 *
 * Deliberately keyed off authStore.isAuthenticated -- covers the staff
 * app and the Site Engineer Portal, which both authenticate through
 * authStore. The Customer Portal manages its own separate (pre-existing,
 * not-yet-unified) session and isn't covered by this timer.
 */
export function useIdleLogout(): void {
  const authStore = useAuthStore()
  const router = useRouter()

  let timeoutId: ReturnType<typeof setTimeout> | undefined

  function clear(): void {
    if (timeoutId !== undefined) {
      clearTimeout(timeoutId)
      timeoutId = undefined
    }
  }

  async function handleIdleTimeout(): Promise<void> {
    clear()
    stopListening()
    if (!authStore.isAuthenticated) return

    const currentRoute = router.currentRoute.value
    const loginRoute =
      currentRoute.meta.layout === 'site-portal' ? ROUTE_NAMES.SITE_PORTAL_LOGIN : ROUTE_NAMES.LOGIN

    await authStore.logout()
    await router.push({ name: loginRoute, query: { reason: 'You were signed out after 30 minutes of inactivity.' } })
  }

  function reset(): void {
    clear()
    timeoutId = setTimeout(handleIdleTimeout, IDLE_TIMEOUT_MS)
  }

  function startListening(): void {
    for (const eventName of ACTIVITY_EVENTS) {
      window.addEventListener(eventName, reset, { passive: true })
    }
    reset()
  }

  function stopListening(): void {
    for (const eventName of ACTIVITY_EVENTS) {
      window.removeEventListener(eventName, reset)
    }
    clear()
  }

  // Only listen (and hold a live timer) while actually authenticated --
  // otherwise this would fire logout() on an already-signed-out session
  // every time someone sits on the login page for half an hour.
  watch(
    () => authStore.isAuthenticated,
    (isAuthenticated) => {
      if (isAuthenticated) {
        startListening()
      } else {
        stopListening()
      }
    },
    { immediate: true },
  )
}
