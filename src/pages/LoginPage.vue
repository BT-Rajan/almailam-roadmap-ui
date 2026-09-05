<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import StaffLoginForm from '@/components/auth/StaffLoginForm.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useAuthStore } from '@/stores/authStore'

const { t } = useI18n()
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

// Set by useIdleLogout (30-minute inactivity auto-logout) when it bounces
// here -- without this, someone dropped back on the login screen mid-work
// has no idea why and it looks like the app just broke.
const initialMessage = typeof route.query.reason === 'string' ? route.query.reason : undefined

async function handleSuccess(): Promise<void> {
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : undefined
  await router.push(redirect ?? { name: ROUTE_NAMES.DASHBOARD })
}
</script>

<template>
  <div>
    <h1 class="text-xl font-semibold text-[var(--color-text-primary)]">{{ t('auth.loginPage.title') }}</h1>
    <p class="mt-1 text-sm text-[var(--color-text-secondary)]">
      {{ t('auth.loginPage.subtitle') }}
    </p>

    <div class="mt-6">
      <StaffLoginForm
        :id-label="t('auth.loginPage.idLabel')"
        :id-placeholder="t('auth.loginPage.idPlaceholder')"
        :login-fn="authStore.login"
        :initial-message="initialMessage"
        show-remember-me
        show-forgot-password
        show-clear
        @success="handleSuccess"
      />
    </div>
  </div>
</template>
