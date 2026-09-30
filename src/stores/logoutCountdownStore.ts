import { defineStore } from 'pinia'

// Backs LogoutCountdownOverlay.vue: a full-screen "you were signed out,
// returning you to sign in in N..." notice shown by useIdleLogout after an
// inactivity logout, so the countdown itself (start/tick/hide) has one
// owner -- the composable driving the timer -- while the component stays
// purely presentational.
export const useLogoutCountdownStore = defineStore('logoutCountdown', {
  state: () => ({
    isVisible: false,
    secondsRemaining: 0,
  }),

  actions: {
    show(startSeconds: number) {
      this.secondsRemaining = startSeconds
      this.isVisible = true
    },

    tick(secondsRemaining: number) {
      this.secondsRemaining = secondsRemaining
    },

    hide() {
      this.isVisible = false
    },
  },
})
