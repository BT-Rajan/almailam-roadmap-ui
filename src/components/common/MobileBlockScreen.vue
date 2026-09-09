<script setup lang="ts">
import { MonitorSmartphone } from '@lucide/vue'
import { useI18n } from 'vue-i18n'

// Full-screen gate rendered by App.vue in place of the normal layout
// whenever useViewport().isBelowTablet is true. ServiceOS's workspaces
// (multi-column forms, Smart Tables, side-by-side document review) assume
// at least a tablet-sized canvas -- there is no cut-down phone layout to
// fall back to, so rather than let every page break in its own way below
// 768px, the whole shell is replaced with this single, calm explanation.
// Purely reactive to viewport width (see useViewport.ts), so rotating a
// tablet or resizing a window past the breakpoint removes this screen
// immediately, without a reload.
const { t } = useI18n()
</script>

<template>
  <div class="mobile-block-screen">
    <div class="mobile-block-screen__card">
      <div class="mobile-block-screen__icon">
        <MonitorSmartphone :size="28" />
      </div>
      <h1 class="mobile-block-screen__title">{{ t('common.mobileBlockScreen.title') }}</h1>
      <p class="mobile-block-screen__description">{{ t('common.mobileBlockScreen.description') }}</p>
      <p class="mobile-block-screen__recommendation">{{ t('common.mobileBlockScreen.recommendation') }}</p>
    </div>
  </div>
</template>

<style scoped>
.mobile-block-screen {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--color-bg-page, #f2f2f4);
}

.mobile-block-screen__card {
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

.mobile-block-screen__icon {
  display: flex;
  height: 56px;
  width: 56px;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  background: rgb(var(--color-accent-500) / 0.12);
  color: rgb(var(--color-accent-600));
}

.mobile-block-screen__title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.mobile-block-screen__description {
  font-size: 0.875rem;
  line-height: 1.5;
  color: var(--color-text-secondary);
}

.mobile-block-screen__recommendation {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-primary);
}
</style>
