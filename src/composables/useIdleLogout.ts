import { onScopeDispose, watch } from 'vue'
import { useRouter } from 'vue-router'

import { ROUTE_NAMES } from '@/constants/routeNames'
import { useAuthStore } from '@/stores/authStore'
import { lastSharedActivity, onRemoteLogout, recordActivity } from '@/utils/sessionSync'

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
 * Deliberately keyed off authStore.isAuthenticated -- covers both
 * frontends (staff app, Site Engineer Portal), since both now
 * authenticate through authStore.
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
    if (!authStore.isAuthenticated) {
      stopListening()
      return
    }

    // The person may be working in another tab of the same session. Logging
    // out here would revoke the refresh cookie that tab depends on, so only
    // give up once every tab has been idle for the full timeout.
    const idleFor = Date.now() - lastSharedActivity()
    if (idleFor < IDLE_TIMEOUT_MS) {
      timeoutId = setTimeout(handleIdleTimeout, IDLE_TIMEOUT_MS - idleFor)
      return
    }

    stopListening()
    await authStore.logout()
    // Carried via authStore.logoutReason (in-memory), not a ?reason=
    // query param -- see that field's own doc comment for why: a query
    // string surviving into a reopened/reloaded tab at this exact URL
    // was landing some users on a login page that silently refused to
    // submit until they manually stripped it. The login route now
    // always stays the bare path.
    authStore.logoutReason = 'You were signed out after 30 minutes of inactivity.'
    await goToLogin()
  }

  function goToLogin(): Promise<unknown> {
    const currentRoute = router.currentRoute.value
    const loginRoute = currentRoute.meta.layout === 'site-portal' ? ROUTE_NAMES.SITE_PORTAL_LOGIN : ROUTE_NAMES.LOGIN
    return router.push({ name: loginRoute })
  }

  // Another tab logged out (by hand, idle timeout or password change). The
  // refresh cookie is already gone, so without this the tab would carry on
  // looking signed in and fail at some random later request instead.
  const stopRemoteLogout = onRemoteLogout(() => {
    if (!authStore.isAuthenticated) return
    authStore.endSessionFromOtherTab()
    authStore.logoutReason = 'You were signed out in another tab.'
    void goToLogin()
  })
  onScopeDispose(stopRemoteLogout)

  function reset(): void {
    recordActivity()
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
