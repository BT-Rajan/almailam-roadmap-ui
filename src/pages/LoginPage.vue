<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'

import StaffLoginForm from '@/components/auth/StaffLoginForm.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useAuthStore } from '@/stores/authStore'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

async function handleSuccess(): Promise<void> {
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : undefined
  await router.push(redirect ?? { name: ROUTE_NAMES.DASHBOARD })
}
</script>

<template>
  <div>
    <h1 class="text-xl font-semibold text-[var(--color-text-primary)]">Sign in</h1>
    <p class="mt-1 text-sm text-[var(--color-text-secondary)]">
      Access the ServiceOS engineering consultancy workspace.
    </p>

    <div class="mt-6">
      <StaffLoginForm
        id-label="User ID"
        id-placeholder="Enter your user ID"
        :login-fn="authStore.login"
        show-remember-me
        show-forgot-password
        show-clear
        @success="handleSuccess"
      />
    </div>
  </div>
</template>
