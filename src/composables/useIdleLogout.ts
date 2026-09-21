import { watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { ROUTE_NAMES } from '@/constants/routeNames'
import { useAuthStore } from '@/stores/authStore'
import { useLogoutCountdownStore } from '@/stores/logoutCountdownStore'

// 5 minutes of no mouse/keyboard/touch/scroll activity signs the user out,
// even though the access token itself would otherwise keep silently
// renewing via the refresh cookie for as long as the tab stays open.
const IDLE_TIMEOUT_MS = 5 * 60 * 1000

// How long the full-screen "you were signed out" countdown stays up before
// the redirect to the login screen actually happens -- counts down from
// this value to 1, one tick per second (see runLogoutCountdown below).
const LOGOUT_COUNTDOWN_START_SECONDS = 10

// Listening on window in the capture phase catches activity anywhere in the
// document, including inside iframes/portals that don't bubble normally.
const ACTIVITY_EVENTS = ['mousemove', 'mousedown', 'keydown', 'wheel', 'touchstart', 'scroll'] as const

/**
 * Wires up a single app-wide idle timer (call once, from App.vue). Resets
 * on any activity event while a session is active; on timeout, logs out,
 * shows a full-screen countdown (see logoutCountdownStore /
 * LogoutCountdownOverlay.vue) so the person actually notices they were
 * signed out instead of just finding themselves back on the login screen
 * with no explanation, then bounces to the right login screen for
 * whichever portal they were using.
 *
 * Deliberately keyed off authStore.isAuthenticated -- covers both
 * frontends (staff app, Site Engineer Portal), since both now
 * authenticate through authStore.
 */
export function useIdleLogout(): void {
  const authStore = useAuthStore()
  const countdownStore = useLogoutCountdownStore()
  const router = useRouter()
  const { t } = useI18n()

  let timeoutId: ReturnType<typeof setTimeout> | undefined

  function clear(): void {
    if (timeoutId !== undefined) {
      clearTimeout(timeoutId)
      timeoutId = undefined
    }
  }

  // Ticks countdownStore.secondsRemaining down from
  // LOGOUT_COUNTDOWN_START_SECONDS to 1, one step per second, then hides
  // the overlay. Resolves once the last second has elapsed, so the caller
  // can await it before navigating away.
  function runLogoutCountdown(): Promise<void> {
    return new Promise((resolve) => {
      countdownStore.show(LOGOUT_COUNTDOWN_START_SECONDS)
      const intervalId = setInterval(() => {
        const next = countdownStore.secondsRemaining - 1
        if (next < 1) {
          clearInterval(intervalId)
          countdownStore.hide()
          resolve()
          return
        }
        countdownStore.tick(next)
      }, 1000)
    })
  }

  async function handleIdleTimeout(): Promise<void> {
    clear()
    stopListening()
    if (!authStore.isAuthenticated) return

    const currentRoute = router.currentRoute.value
    const loginRoute = currentRoute.meta.layout === 'site-portal' ? ROUTE_NAMES.SITE_PORTAL_LOGIN : ROUTE_NAMES.LOGIN

    // authStore.logout() already never throws -- it clears local session
    // state (and logs any server-side revoke failure) regardless of
    // whether the network call itself succeeds -- see its own doc
    // comment. Awaited here so the session is actually dead *before* the
    // countdown/redirect run, not just visually.
    await authStore.logout()
    // Carried via authStore.logoutReason (in-memory), not a ?reason=
    // query param -- see that field's own doc comment for why: a query
    // string surviving into a reopened/reloaded tab at this exact URL
    // was landing some users on a login page that silently refused to
    // submit until they manually stripped it. The login route now
    // always stays the bare path.
    authStore.logoutReason = t('auth.idleLogoutReason')
    await runLogoutCountdown()
    await router.push({ name: loginRoute })
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
