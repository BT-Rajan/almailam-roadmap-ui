import { defineStore } from 'pinia'

import { serverTimeService } from '@/services/serverTimeService'

interface ServerTimeState {
  // ISO date (YYYY-MM-DD), Kuwait local -- null until loadServerTime()
  // resolves at least once.
  todayIso: string | null
  isLoading: boolean
}

/**
 * The one place in the app allowed to know what day "today" is for a
 * business decision (payment obligation overdue status, contract
 * expiry, "days until due") -- everything else reads todayTimestamp
 * from here instead of calling `new Date()` itself.
 *
 * Why this exists: a visiting browser can be set to any timezone, and
 * this app's business rules are Kuwait-local (UTC+3) by policy (see
 * backend/app/core/kuwait_time.py) -- a browser even a few hours off
 * from Kuwait could show an obligation as "Scheduled" when the server
 * already considers it "Overdue", or vice versa. Fetched once per app
 * session (router.beforeEach, right after auth resolves) rather than
 * polled continuously -- these are day-granularity decisions, so a
 * date fetched once when the app loads stays correct for the entire
 * session in all but the rarest case (a tab left open and actively
 * used exactly across a Kuwait midnight boundary), which a page
 * refresh corrects.
 */
export const useServerTimeStore = defineStore('serverTime', {
  state: (): ServerTimeState => ({
    todayIso: null,
    isLoading: false,
  }),

  getters: {
    isLoaded: (state): boolean => state.todayIso !== null,

    // Local midnight of the server's Kuwait-local date, as a
    // timestamp -- the same shape paymentHelpers.ts's todayTimestamp()
    // previously built from `new Date()`. Null until loaded; callers
    // fall back to the browser's own clock only for that narrow
    // bootstrap window (see paymentHelpers.ts), never as an ongoing
    // substitute for the real value once it's arrived.
    todayTimestamp(state): number | null {
      if (state.todayIso === null) return null
      const [year, month, day] = state.todayIso.split('-').map(Number)
      return new Date(year, month - 1, day).getTime()
    },
  },

  actions: {
    async loadServerTime(): Promise<void> {
      if (this.isLoaded || this.isLoading) return
      this.isLoading = true
      try {
        const result = await serverTimeService.getServerTime()
        this.todayIso = result.date
      } catch {
        // Left null -- every consumer already has a documented,
        // clearly-flagged browser-date fallback for exactly this case
        // (server unreachable), rather than this store throwing and
        // blocking navigation entirely over a non-critical fetch.
      } finally {
        this.isLoading = false
      }
    },
  },
})
