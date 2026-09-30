<script setup lang="ts">
import { LogOut } from '@lucide/vue'
import { useI18n } from 'vue-i18n'

import { useLogoutCountdownStore } from '@/stores/logoutCountdownStore'

// Full-screen notice shown by useIdleLogout right after an inactivity
// logout, counting down from 10 to 1 before the person actually lands on
// the login screen -- otherwise the redirect happens instantly and it
// looks like the app just kicked them out with no explanation. The
// countdown itself is driven by the composable (see runLogoutCountdown in
// useIdleLogout.ts); this component only ever reflects that store's state.
const { t } = useI18n()
const store = useLogoutCountdownStore()
</script>

<template>
  <div
    v-if="store.isVisible"
    class="logout-countdown-overlay"
    role="alert"
    aria-live="assertive"
  >
    <div class="logout-countdown-overlay__card">
      <div class="logout-countdown-overlay__icon">
        <LogOut :size="28" />
      </div>
      <h1 class="logout-countdown-overlay__title">{{ t('auth.logoutCountdown.title') }}</h1>
      <p class="logout-countdown-overlay__description">{{ t('auth.logoutCountdown.description') }}</p>
      <p class="logout-countdown-overlay__count">{{ store.secondsRemaining }}</p>
    </div>
  </div>
</template>

<style scoped>
.logout-countdown-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--color-bg-page, #f2f2f4);
}

.logout-countdown-overlay__card {
  display: flex;
  max-width: 360px;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  border-radius: 1rem;
  border: 1px solid var(--color-border-light);
  background: var(--color-bg-card);
  padding: 32px 24px;
  text-align: center;
  box-shadow: var(--shadow-elevated);
}

.logout-countdown-overlay__icon {
  display: flex;
  height: 56px;
  width: 56px;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  background: rgb(var(--color-accent-500) / 0.12);
  color: rgb(var(--color-accent-600));
}

.logout-countdown-overlay__title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.logout-countdown-overlay__description {
  font-size: 0.875rem;
  line-height: 1.5;
  color: var(--color-text-secondary);
}

.logout-countdown-overlay__count {
  font-size: 2.5rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: rgb(var(--color-accent-600));
}
</style>
