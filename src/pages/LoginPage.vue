<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'

import StaffLoginForm from '@/components/auth/StaffLoginForm.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useAuthStore } from '@/stores/authStore'

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
    <!-- font-display (Playfair Display), not the plain sans heading this
         used to be -- on screens below the split-panel breakpoint the
         brand panel's own serif headline is hidden entirely, so this is
         the ONLY place the premium typographic identity shows up at all;
         leaving it plain sans undid the richness everywhere else. -->
    <h1 class="font-display text-2xl text-[var(--color-text-primary)]">Sign in</h1>
    <p class="mt-1 text-sm text-[var(--color-text-secondary)]">
      Access the ServiceOS engineering consultancy workspace.
    </p>

    <div class="mt-6">
      <StaffLoginForm
        id-label="User ID"
        id-placeholder="Enter your user ID"
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
